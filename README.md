# MangaScale - AI Manga Image Upscaler

Upscale manga and anime images to **4K resolution** using the **RealESRGAN_x4plus_anime_6B** AI model.

## Features

- **4K Upscaling** — Every image is upscaled 4x and fit to 4K UHD (3840 px longest edge)
- **ZIP Support** — Upload `.zip` archives containing multiple manga pages for batch processing
- **Individual Images** — Upload PNG, JPG, WEBP, BMP, TIFF files directly
- **Custom Output Folder** — Specify any folder path to save your upscaled images
- **Real-time Progress** — Live progress bar with per-file status updates
- **Download Results** — Download all processed images as a single ZIP archive
- **Preview Grid** — View upscaled images directly in the browser
- **Drag & Drop** — Intuitive drag-and-drop upload interface

## Tech Stack

| Layer    | Technology                           |
|----------|--------------------------------------|
| Frontend | HTML / CSS / JavaScript (Vanilla)    |
| Backend  | Python 3 + Flask                     |
| AI Model | realesrgan-ncnn-vulkan (Vulkan GPU)  |
| Model    | RealESRGAN_x4plus_anime_6B           |

## Quick Start

```bash
# 1. Run setup (installs dependencies + downloads ESRGAN engine)
python setup.py

# 2. Start the server
python server.py

# 3. Open in browser
# http://localhost:5000
```

## Project Structure

```
Image Upscaler/
├── server.py                        # Flask backend
├── setup.py                         # One-click setup script
├── requirements.txt                 # Python dependencies
├── frontend/
│   ├── index.html                   # Main UI page
│   ├── style.css                    # Premium dark theme
│   └── app.js                       # Client-side logic
├── realesrgan-ncnn-vulkan/          # ESRGAN engine (auto-downloaded)
│   ├── realesrgan-ncnn-vulkan.exe
│   └── models/
├── uploads/                         # Temporary upload storage
├── output/                          # Default output directory
└── temp/                            # Temporary files
```

## How It Works

1. **Upload** — Drop images or a `.zip` file into the upload zone
2. **Configure** — Optionally set a custom output folder path
3. **Process** — The backend runs each image through `realesrgan-ncnn-vulkan.exe` with the anime-optimized model
4. **Post-Process** — Images are resized to fit within 4K (3840 px) bounds using Lanczos resampling
5. **Download** — Preview results in-browser or download as a ZIP

## Requirements

- **Python 3.8+**
- **Windows** (uses the ncnn-vulkan portable executable)
- **Vulkan-compatible GPU** (Intel, AMD, or Nvidia)
