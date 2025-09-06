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

© 2025 PixelForge — Mach Square Games  
Developed by **Sarfraz Saghir Ahmad**
