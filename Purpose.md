# 🛠️ Problems PixelForge Resolves

### 1. **Unity Texture Compression Errors (ETC/ETC2)**
When building games in **Unity** (and other engines), textures used with **ETC/ETC2 compression** must have dimensions that are **multiples of 4**.  
- Example: an image sized **511×512** or **1025×1025** will **throw errors** or fail to compress.  
- Manually fixing these dimensions for dozens or hundreds of textures wastes valuable time.  

✅ **PixelForge automatically resizes or pads images to valid 4×4 dimensions**, preventing build errors and keeping your workflow smooth.

---

### 2. **Google Play Asset Rejections**
Publishing apps to the **Google Play Store** requires strict image sizes:  
- **App Icon** must be **512×512**  
- **Screenshots** must be **1920×1080 (landscape)** or **1080×1920 (portrait)**  

Designers often hand over files that are just slightly off, like **511×512** or **1920×1081**. Google Play **rejects these files**, forcing last-minute fixes.  

✅ **PixelForge instantly corrects off-by-1 or mismatched dimensions**, ensuring your assets pass Play Console checks without hassle.

---

### 3. **Time-Consuming Manual Fixes**
When dealing with:  
- Large texture libraries for **games**  
- Multiple **screenshots and icons** for mobile apps  
- Mixed asset folders with many file types  

…it’s tedious to open each image in Photoshop or GIMP just to resize, crop, or align.  

✅ **PixelForge processes entire folders (and subfolders) in one click**, applying consistent fixes to all supported formats.

---

### 4. **Preserving Quality and Compatibility**
Resizing and fixing images often risks losing sharpness or breaking transparency. PixelForge avoids this by:  
- Using **Lanczos resampling** for high-quality scaling  
- Preserving **EXIF orientation** so photos don’t appear rotated  
- Supporting many formats (**PNG, JPG, WEBP, TGA, BMP, TIFF, PSD**)  
- Optional **.bak backups** for safety  

---

👉 **In short**:  
PixelForge eliminates the most common **Unity build errors** and **Google Play submission issues**, while saving you hours of repetitive resizing work.  
