#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Resizer GUI v3
Modes:
  1) 4x4-only: Make dimensions multiples of 4
  2) Resize: Resize to target width (optionally enforce multiples of 4)
  3) Google Play assets: Force exact canvas sizes (e.g., 512x512 or 1920x1080) using Pad/Crop/Stretch

Features:
- Choose a folder
- Optional: recurse into subfolders
- Optional: .bak backups
- Progress bar + log
- Supported: PNG, JPG, JPEG, TGA, PSD*, TIF/TIFF, BMP, WEBP
  (* PSD requires 'psd-tools')

Install:
  pip install pillow
Optional for PSD:
  pip install psd-tools
"""
import os
import sys
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps
except Exception as e:
    raise SystemExit("Pillow is required. Please run: pip install pillow") from e

_HAS_PSD_TOOLS = False
try:
    import psd_tools  # noqa: F401
    _HAS_PSD_TOOLS = True
except Exception:
    _HAS_PSD_TOOLS = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".psd", ".tif", ".tiff", ".bmp", ".webp"}

def next_multiple_of_4(n: int) -> int:
    r = n % 4
    return n if r == 0 else (n + (4 - r))

def compute_new_size_resize_mode(width: int, height: int, target_w: Optional[int], enforce_mult4: bool, allow_upscale: bool) -> Tuple[int, int]:
    new_w, new_h = width, height
    if target_w is not None and target_w > 0:
        if width > target_w or (allow_upscale and width < target_w):
            ratio = width / float(target_w)
            new_w = target_w
            new_h = max(1, int(round(height / ratio)))
    if enforce_mult4:
        new_w = next_multiple_of_4(new_w)
        new_h = next_multiple_of_4(new_h)
    return new_w, new_h

def compute_new_size_mult4_only(width: int, height: int) -> Tuple[int, int]:
    return next_multiple_of_4(width), next_multiple_of_4(height)

def iter_files(folder: str, recursive: bool):
    if recursive:
        for root, _, files in os.walk(folder):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in SUPPORTED_EXTS:
                    yield os.path.join(root, f)
    else:
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
                if ext in SUPPORTED_EXTS:
                    yield p

@dataclass
class JobConfig:
    folder: str
    recursive: bool
    mode: str  # "mult4", "resize", "gp"
    # Resize mode
    target_width: Optional[int]
    enforce_mult4: bool
    allow_upscale: bool
    # Google Play mode
    gp_w: Optional[int]
    gp_h: Optional[int]
    gp_method: str  # "pad", "crop", "stretch"
    gp_force_png: bool
    gp_bg_color: Optional[Tuple[int,int,int,int]]  # RGBA
    # Common
    backup: bool

class ResizerWorker(threading.Thread):
    def __init__(self, cfg: JobConfig, log_fn, progress_fn, done_fn):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.log = log_fn
        self.progress = progress_fn
        self.done = done_fn

    def run(self):
        files = list(iter_files(self.cfg.folder, self.cfg.recursive))
        total = len(files)
        processed = changed = skipped = errors = 0

        if total == 0:
            self.log("No supported images found.")
            self.done(0, 0, 0, 0)
            return

        self.log(f"Found {total} image(s). Starting...")

        for idx, path in enumerate(files, 1):
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".psd" and not _HAS_PSD_TOOLS:
                    self.log(f"Skipping PSD (psd-tools not installed): {path}")
                    skipped += 1
                    processed += 1
                    self.progress(idx, total)
                    continue

                with Image.open(path) as im:
                    try:
                        im = ImageOps.exif_transpose(im)
                    except Exception:
                        pass

                    src_w, src_h = im.size

                    if self.cfg.mode == "mult4":
                        new_w, new_h = compute_new_size_mult4_only(src_w, src_h)
                        if (new_w, new_h) == (src_w, src_h):
                            skipped += 1
                            self.log(f"Skip (already 4x4): {os.path.basename(path)} [{src_w}x{src_h}]")
                        else:
                            im = im.resize((new_w, new_h), Image.LANCZOS)
                            self._save_image(im, path, keep_format=True)
                            changed += 1
                            self.log(f"4x4 align: {os.path.basename(path)} [{src_w}x{src_h}] -> [{new_w}x{new_h}]")

                    elif self.cfg.mode == "resize":
                        new_w, new_h = compute_new_size_resize_mode(
                            src_w, src_h,
                            self.cfg.target_width,
                            self.cfg.enforce_mult4,
                            self.cfg.allow_upscale,
                        )
                        if (new_w, new_h) == (src_w, src_h):
                            skipped += 1
                            self.log(f"Skip (no change): {os.path.basename(path)} [{src_w}x{src_h}]")
                        else:
                            im = im.resize((new_w, new_h), Image.LANCZOS)
                            self._save_image(im, path, keep_format=True)
                            changed += 1
                            self.log(f"resize: {os.path.basename(path)} [{src_w}x{src_h}] -> [{new_w}x{new_h}]")

                    else:  # "gp" Google Play assets
                        target_w = int(self.cfg.gp_w or 0)
                        target_h = int(self.cfg.gp_h or 0)
                        if target_w <= 0 or target_h <= 0:
                            raise ValueError("Invalid Google Play target size.")

                        # Off-by-1 quick fix: if within 1px in each dimension, pad/crop minimally without scaling
                        dw = target_w - src_w
                        dh = target_h - src_h
                        within_one = abs(dw) <= 1 and abs(dh) <= 1

                        if self.cfg.gp_method == "stretch":
                            out = im.resize((target_w, target_h), Image.LANCZOS)
                        elif self.cfg.gp_method == "crop":
                            # scale to cover, then center-crop
                            scale = max(target_w / src_w, target_h / src_h)
                            if scale != 1.0 and not within_one:
                                new_w = max(1, int(round(src_w * scale)))
                                new_h = max(1, int(round(src_h * scale)))
                                im = im.resize((new_w, new_h), Image.LANCZOS)
                            # center crop to exact
                            left = max(0, (im.width - target_w) // 2)
                            top = max(0, (im.height - target_h) // 2)
                            out = im.crop((left, top, left + target_w, top + target_h))
                        else:  # "pad"
                            # scale to fit, then pad canvas
                            scale = min(target_w / src_w, target_h / src_h)
                            if scale != 1.0 and not within_one:
                                new_w = max(1, int(round(src_w * scale)))
                                new_h = max(1, int(round(src_h * scale)))
                                im = im.resize((new_w, new_h), Image.LANCZOS)
                            out = self._pad_to_canvas(im, target_w, target_h, self.cfg.gp_bg_color)

                        if out.size == (src_w, src_h):
                            skipped += 1
                            self.log(f"Skip (already exact): {os.path.basename(path)} [{src_w}x{src_h}]")
                        else:
                            self._save_image(out, path, keep_format=not self.cfg.gp_force_png, force_png=self.cfg.gp_force_png)
                            changed += 1
                            self.log(f"google-play: {os.path.basename(path)} [{src_w}x{src_h}] -> [{target_w}x{target_h}] ({self.cfg.gp_method})")

                processed += 1

            except Exception as e:
                errors += 1
                self.log(f"ERROR on {path}: {e!r}")

            self.progress(idx, total)

        self.log("Done.")
        self.done(processed, changed, skipped, errors)

    def _pad_to_canvas(self, im: Image.Image, tw: int, th: int, bg_rgba: Optional[Tuple[int,int,int,int]]):
        # Choose background
        if bg_rgba is None:
            # default transparent for images with alpha, else white
            bg_rgba = (255, 255, 255, 0 if ("A" in im.getbands()) else 255)
        canvas = Image.new("RGBA", (tw, th), bg_rgba)
        # Convert im to RGBA for proper alpha pasting when needed
        if im.mode != "RGBA" and bg_rgba[3] < 255:
            im = im.convert("RGBA")
        x = (tw - im.width) // 2
        y = (th - im.height) // 2
        canvas.paste(im, (x, y), im if im.mode == "RGBA" else None)
        return canvas

    def _save_image(self, im: Image.Image, path: str, keep_format: bool, force_png: bool=False):
        # Optional backup
        if self.cfg.backup:
            bak = path + ".bak"
            if not os.path.exists(bak):
                try:
                    with open(path, "rb") as rf, open(bak, "wb") as wf:
                        wf.write(rf.read())
                except Exception as e:
                    self.log(f"Backup failed, proceeding anyway: {e}")

        params = {}
        if force_png:
            # Save as PNG next to original (overwrite same path extension changed to .png)
            base, _ = os.path.splitext(path)
            out_path = base + ".png"
            im.save(out_path, **params)
            return

        fmt = None
        try:
            fmt = (Image.open(path).format or "").upper()
        except Exception:
            pass

        if fmt in {"JPG", "JPEG"}:
            params["quality"] = 92
            params["optimize"] = True
            params["subsampling"] = "keep"
        try:
            im.save(path, **params)
        except Exception:
            im.save(path)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PixelForge")

        # Fix: Set window/taskbar icon
        if hasattr(sys, "_MEIPASS"):  # running from PyInstaller bundle
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
        else:
            icon_path = "app_icon.ico"

        try:
            self.iconbitmap(icon_path)  # sets taskbar and window icon
        except Exception as e:
            print("Icon load failed:", e)


        # self.title("Image Resizer (GUI) — v3")
        self.geometry("880x740")
        self.minsize(840, 700)

        # Vars
        self.folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.backup_var = tk.BooleanVar(value=False)

        # Mode
        self.mode_var = tk.StringVar(value="gp")  # default to GP since requested

        # Resize options
        self.enforce4_var = tk.BooleanVar(value=True)
        self.upscale_var = tk.BooleanVar(value=False)
        self.width_choice_var = tk.StringVar(value="1024")
        self.custom_width_var = tk.StringVar(value="")

        # Google Play options
        self.gp_preset_var = tk.StringVar(value="Icon 512x512")
        self.gp_custom_w_var = tk.StringVar(value="")
        self.gp_custom_h_var = tk.StringVar(value="")
        self.gp_method_var = tk.StringVar(value="pad")
        self.gp_force_png_var = tk.BooleanVar(value=True)
        self.gp_bg_rgba = (255, 255, 255, 0)  # default transparent

        self._build_ui()
        self._update_mode_state()

        self.worker: Optional[ResizerWorker] = None

    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        # Folder picker
        fr_folder = ttk.LabelFrame(self, text="1) Choose folder")
        fr_folder.pack(fill="x", **pad)
        ttk.Entry(fr_folder, textvariable=self.folder_var).pack(side="left", fill="x", expand=True, padx=(12,6), pady=10)
        ttk.Button(fr_folder, text="Browse…", command=self._pick_folder).pack(side="left", padx=6, pady=10)

        # Mode
        fr_mode = ttk.LabelFrame(self, text="2) Processing mode")
        fr_mode.pack(fill="x", **pad)
        ttk.Radiobutton(fr_mode, text="Make dimensions multiples of 4 (4x4 only)", value="mult4",
                        variable=self.mode_var, command=self._update_mode_state).pack(anchor="w", padx=12)
        ttk.Radiobutton(fr_mode, text="Resize to target width", value="resize",
                        variable=self.mode_var, command=self._update_mode_state).pack(anchor="w", padx=12)
        ttk.Radiobutton(fr_mode, text="Google Play assets (exact sizes like 512×512, 1920×1080)", value="gp",
                        variable=self.mode_var, command=self._update_mode_state).pack(anchor="w", padx=12)

        # Resize options
        self.fr_opts_resize = ttk.LabelFrame(self, text="3) Options — Resize mode")
        self.fr_opts_resize.pack(fill="x", **pad)
        sub = ttk.Frame(self.fr_opts_resize); sub.pack(fill="x", padx=8, pady=8)
        ttk.Label(sub, text="Target width:").grid(row=0, column=0, sticky="w")
        choices = ["256", "512", "1024", "2048", "Custom…"]
        self.cb_width = ttk.Combobox(sub, values=choices, textvariable=self.width_choice_var, state="readonly", width=10)
        self.cb_width.grid(row=0, column=1, sticky="w", padx=(8, 16))
        ttk.Label(sub, text="Custom width:").grid(row=0, column=2, sticky="w")
        self.ent_cw = ttk.Entry(sub, textvariable=self.custom_width_var, width=10)
        self.ent_cw.grid(row=0, column=3, sticky="w", padx=(8, 16))
        self.chk_enf = ttk.Checkbutton(self.fr_opts_resize, text="Enforce multiples of 4 (width & height)", variable=self.enforce4_var)
        self.chk_enf.pack(anchor="w", padx=12)
        self.chk_up = ttk.Checkbutton(self.fr_opts_resize, text="Allow upscaling (if image smaller than target)", variable=self.upscale_var)
        self.chk_up.pack(anchor="w", padx=12)

        # Google Play options
        self.fr_opts_gp = ttk.LabelFrame(self, text="3) Options — Google Play assets")
        self.fr_opts_gp.pack(fill="x", **pad)

        row = 0
        ttk.Label(self.fr_opts_gp, text="Preset:").grid(row=row, column=0, sticky="w", padx=12, pady=6)
        self.cb_preset = ttk.Combobox(self.fr_opts_gp,
                                      values=["Icon 512x512", "Screenshot 1920x1080 (landscape)", "Screenshot 1080x1920 (portrait)", "Custom…"],
                                      textvariable=self.gp_preset_var, state="readonly", width=28)
        self.cb_preset.grid(row=row, column=1, sticky="w", padx=8)
        self.cb_preset.bind("<<ComboboxSelected>>", lambda e: self._update_gp_custom_state())

        row += 1
        ttk.Label(self.fr_opts_gp, text="Custom WxH:").grid(row=row, column=0, sticky="w", padx=12, pady=6)
        self.ent_gpw = ttk.Entry(self.fr_opts_gp, textvariable=self.gp_custom_w_var, width=8)
        self.ent_gpw.grid(row=row, column=1, sticky="w", padx=(8, 4))
        ttk.Label(self.fr_opts_gp, text="×").grid(row=row, column=1, sticky="w", padx=(70,0))
        self.ent_gph = ttk.Entry(self.fr_opts_gp, textvariable=self.gp_custom_h_var, width=8)
        self.ent_gph.grid(row=row, column=1, sticky="w", padx=(88, 0))

        row += 1
        ttk.Label(self.fr_opts_gp, text="Method:").grid(row=row, column=0, sticky="w", padx=12, pady=6)
        self.cb_method = ttk.Combobox(self.fr_opts_gp, values=["pad", "crop", "stretch"], textvariable=self.gp_method_var, state="readonly", width=12)
        self.cb_method.grid(row=row, column=1, sticky="w", padx=8)

        row += 1
        self.chk_png = ttk.Checkbutton(self.fr_opts_gp, text="Force PNG output (recommended for icon)", variable=self.gp_force_png_var)
        self.chk_png.grid(row=row, column=1, sticky="w", padx=8, pady=6)

        row += 1
        ttk.Button(self.fr_opts_gp, text="Background color… (pad mode)", command=self._choose_bg).grid(row=row, column=1, sticky="w", padx=8, pady=6)

        # Common options
        fr_common = ttk.LabelFrame(self, text="4) Common options")
        fr_common.pack(fill="x", **pad)
        ttk.Checkbutton(fr_common, text="Recurse into subfolders", variable=self.recursive_var).pack(anchor="w", padx=12)
        ttk.Checkbutton(fr_common, text="Create .bak backups before overwriting", variable=self.backup_var).pack(anchor="w", padx=12)

        # Actions
        fr_actions = ttk.LabelFrame(self, text="5) Run")
        fr_actions.pack(fill="x", **pad)
        self.btn_start = ttk.Button(fr_actions, text="Start", command=self.on_start); self.btn_start.pack(side="left", padx=12, pady=10)
        self.btn_cancel = ttk.Button(fr_actions, text="Cancel", command=self.on_cancel, state="disabled"); self.btn_cancel.pack(side="left", padx=6, pady=10)

        # Progress
        fr_prog = ttk.Frame(fr_actions); fr_prog.pack(fill="x", expand=True, padx=12)
        self.prog = ttk.Progressbar(fr_prog, orient="horizontal", mode="determinate"); self.prog.pack(fill="x", expand=True)
        self.lbl_prog = ttk.Label(fr_actions, text="Idle"); self.lbl_prog.pack(side="right", padx=12)

        # Log
        fr_log = ttk.LabelFrame(self, text="Log"); fr_log.pack(fill="both", expand=True, **pad)
        self.txt = tk.Text(fr_log, height=12, wrap="word"); self.txt.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(self, text="Tip: Google Play mode makes assets exact size; choose Pad/Crop/Stretch to control behavior.").pack(anchor="w", padx=14, pady=(0, 10))

        self._update_gp_custom_state()

    def _update_mode_state(self):
        mode = self.mode_var.get()
        # Toggle groups
        for w in (self.fr_opts_resize,):
            w.pack_forget()
        for w in (self.fr_opts_gp,):
            w.pack_forget()

        if mode == "resize":
            self.fr_opts_resize.pack_configure(fill="x", padx=10, pady=8)
        elif mode == "gp":
            self.fr_opts_gp.pack_configure(fill="x", padx=10, pady=8)

    def _update_gp_custom_state(self):
        is_custom = (self.gp_preset_var.get() == "Custom…")
        state = "normal" if is_custom else "disabled"
        self.ent_gpw.configure(state=state)
        self.ent_gph.configure(state=state)

    def _choose_bg(self):
        # Returns tuple (rgb, hexstr); we convert to RGBA (opaque by default)
        rgb, hx = colorchooser.askcolor(title="Choose background color for pad mode")
        if rgb is None:
            return
        r, g, b = map(int, rgb)
        # If you want transparency, you can set alpha 0 manually below or add a slider later
        self.gp_bg_rgba = (r, g, b, 255)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="Select Parent Folder")
        if d:
            self.folder_var.set(d)

    def resolve_target_width(self) -> Optional[int]:
        choice = self.width_choice_var.get()
        if choice == "Custom…":
            cw = self.custom_width_var.get().strip()
            if not cw:
                return None
            return max(1, int(cw))
        else:
            return int(choice)

    def _gp_target_size(self) -> Tuple[int, int]:
        preset = self.gp_preset_var.get()
        if preset == "Icon 512x512":
            return 512, 512
        if preset == "Screenshot 1920x1080 (landscape)":
            return 1920, 1080
        if preset == "Screenshot 1080x1920 (portrait)":
            return 1080, 1920
        # Custom
        try:
            w = int(self.gp_custom_w_var.get().strip())
            h = int(self.gp_custom_h_var.get().strip())
            if w <= 0 or h <= 0:
                raise ValueError
            return w, h
        except Exception:
            raise ValueError("Enter valid custom width and height for Google Play mode.")

    def on_start(self):
        folder = self.folder_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Folder missing", "Please choose a valid folder.")
            return

        mode = self.mode_var.get()

        # Defaults
        target_w = None
        enforce4 = self.enforce4_var.get()
        allow_up = self.upscale_var.get()
        gp_w = gp_h = None

        if mode == "resize":
            try:
                target_w = self.resolve_target_width()
            except Exception as e:
                messagebox.showerror("Invalid width", str(e)); return
        elif mode == "mult4":
            enforce4 = True
            allow_up = False
        else:  # gp
            try:
                gp_w, gp_h = self._gp_target_size()
            except Exception as e:
                messagebox.showerror("Invalid Google Play size", str(e)); return

        cfg = JobConfig(
            folder=folder,
            recursive=self.recursive_var.get(),
            mode=mode,
            target_width=target_w,
            enforce_mult4=enforce4,
            allow_upscale=allow_up,
            gp_w=gp_w,
            gp_h=gp_h,
            gp_method=self.gp_method_var.get(),
            gp_force_png=self.gp_force_png_var.get(),
            gp_bg_color=self.gp_bg_rgba,
            backup=self.backup_var.get(),
        )

        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.txt.delete("1.0", "end")

        if mode == "mult4":
            self.log(f"Starting 4x4-only alignment on: {folder}")
        elif mode == "resize":
            self.log(f"Starting resize on: {folder} | target_width={target_w}; 4x4={cfg.enforce_mult4}; upscale={cfg.allow_upscale}")
        else:
            self.log(f"Starting Google Play assets on: {folder} | target={gp_w}x{gp_h}; method={cfg.gp_method}; force_png={cfg.gp_force_png}")

        self.log(f"recurse={cfg.recursive}; backup={cfg.backup}")
        self.prog.configure(value=0, maximum=1)
        self.lbl_prog.configure(text="Preparing…")

        def progress_fn(done: int, total: int):
            self.after(0, lambda: self._update_progress(done, total))

        def done_fn(processed: int, changed: int, skipped: int, errors: int):
            def _finish():
                self.btn_start.configure(state="normal")
                self.btn_cancel.configure(state="disabled")
                self.lbl_prog.configure(text=f"Processed: {processed} | Changed: {changed} | Skipped: {skipped} | Errors: {errors}")
            self.after(0, _finish)

        self.worker = ResizerWorker(cfg, self.log, progress_fn, done_fn)
        self.worker.start()

    def on_cancel(self):
        messagebox.showinfo("Cancel", "Cancel requested. Please wait for the current file to finish. You can close the window to stop.")
        self.btn_cancel.configure(state="disabled")

    def _update_progress(self, done: int, total: int):
        self.prog.configure(maximum=total, value=done)
        self.lbl_prog.configure(text=f"{done} / {total}")

    def log(self, msg: str):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
