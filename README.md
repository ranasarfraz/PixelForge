# PixelForge

PixelForge is a user-friendly desktop tool to prepare images for app development, Google Play Store, and game assets.

## 🚀 Download
Download **PixelForge.exe** from **Windows Build** folder to run it in your Windows Computer

## ✨ Features
- **4x4 Alignment Mode**: Ensures images have width/height divisible by 4 (ETC2 compression friendly for Unity and other engines).
- **Resize Mode**: Resize images to target width (256, 512, 1024, 2048, or custom).
- **Google Play Assets Mode**:
  - Icon (512x512)
  - Screenshots (1920x1080, 1080x1920)
  - Custom sizes with Pad / Crop / Stretch options
  - Off-by-1 auto-fix for designer-provided images
- Supports **PNG, JPG, JPEG, TGA, PSD*, TIF/TIFF, BMP, WEBP** (*PSD requires `psd-tools`).
- Optional **recursive folder scanning** and **.bak backups**.

## 🛠️ Problems It Solves
1. **Unity ETC/ETC2 Compression Issues**  
   Unity requires textures to have dimensions multiple of 4. Non-compliant images (e.g., 511×512) break builds.  
   ✅ PixelForge automatically aligns textures to multiples of 4.

2. **Google Play Store Asset Rejections**  
   Google Play requires exact sizes: icons (512×512), screenshots (1920×1080 or 1080×1920).  
   Designer-provided assets often come as 511×512 or 1920×1081.  
   ✅ PixelForge fixes these off-by-1 errors instantly.

3. **Batch Processing**  
   Fix hundreds of images at once, saving hours of manual work.

4. **Quality Preservation**  
   Uses **Lanczos resampling**, keeps **EXIF orientation**, supports many formats.

## 🚀 Installation

### Requirements
- Python 3.8+
- Pillow
- (Optional) psd-tools for PSD support

Install dependencies:
```bash
pip install pillow psd-tools
```

### Run from Source
```bash
python image_resizer_gui_v3.py
```

### Build as EXE (Windows)
Use PyInstaller to package:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=app_icon.ico --add-data "app_icon.ico;." image_resizer_gui_v3.py
```

- `--icon=app_icon.ico` → sets the app’s EXE icon.  
- `--add-data "app_icon.ico;."` → bundles the icon for use at runtime.  

### Fixing Taskbar Icon in Tkinter
Tkinter apps often show the default **feather icon** in the taskbar.  
To fix this, add in your `App` class:
```python
import sys, os

if hasattr(sys, "_MEIPASS"):
    icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
else:
    icon_path = "app_icon.ico"

self.iconbitmap(icon_path)
```

This ensures your custom icon is used in both the **taskbar** and the **window title bar**.

## 🎨 Icon
The included `app_icon.ico` and `app_icon.png` can be used for branding.

## 📖 Usage
1. Launch the app.
2. Select a folder with images.
3. Choose processing mode:
   - **4x4 Alignment** → fix texture sizes.
   - **Resize** → resize to a target width.
   - **Google Play Assets** → prepare icons/screenshots with exact dimensions.
4. Click **Start** and monitor the progress log.

## 📦 Distribution
- Share the `.exe` in the `dist/` folder.
- Optionally create an installer using Inno Setup for Windows.

---

© 2025 PixelForge — Mach Square Games  
Developed by **Sarfraz Saghir Ahmad**
