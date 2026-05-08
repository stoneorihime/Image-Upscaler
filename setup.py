# -*- coding: utf-8 -*-
"""
Setup script - Downloads realesrgan-ncnn-vulkan for Windows
and extracts it into the project directory.
"""

import io
import os
import sys
import zipfile
import urllib.request
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TARGET = BASE_DIR / "realesrgan-ncnn-vulkan"

RELEASE_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/"
    "v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
)


def download_and_extract():
    if (TARGET / "realesrgan-ncnn-vulkan.exe").exists():
        print("[OK] realesrgan-ncnn-vulkan.exe already exists -- skipping download.")
        return

    print("[*] Downloading from:")
    print("    %s" % RELEASE_URL)
    print("    This may take a minute...")

    req = urllib.request.Request(RELEASE_URL, headers={"User-Agent": "MangaScale/1.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    print("    Downloaded %.1f MB" % (len(data) / (1024*1024)))

    # Extract
    TARGET.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # The zip has a top-level directory; we want its contents directly
        top_dirs = {name.split("/")[0] for name in zf.namelist()}
        top_dir = top_dirs.pop() if len(top_dirs) == 1 else None

        for member in zf.infolist():
            if member.is_dir():
                continue
            # Strip the top-level directory from the path if it exists
            if top_dir and member.filename.startswith(top_dir + "/"):
                rel = member.filename[len(top_dir) + 1:]
            else:
                rel = member.filename

            if not rel:
                continue

            dest = TARGET / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)

    exe = TARGET / "realesrgan-ncnn-vulkan.exe"
    if exe.exists():
        print("[OK] Extracted successfully to: %s" % TARGET)
    else:
        print("[FAIL] Extraction completed but exe not found. Check %s" % TARGET)
        print("    You may need to download manually from:")
        print("    %s" % RELEASE_URL)


def install_requirements():
    print("")
    print("[*] Installing Python dependencies...")
    req_file = str(BASE_DIR / "requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=False)
    print("[OK] Dependencies installed.")


if __name__ == "__main__":
    print("=" * 55)
    print("  MangaScale -- Setup")
    print("=" * 55)
    install_requirements()
    print()
    download_and_extract()
    print()
    print("=" * 55)
    print("  Setup complete! Run the app with:")
    print("    python server.py")
    print("  Then open http://localhost:5000")
    print("=" * 55)
