import os
import uuid
import requests

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)


def download_image(image_url: str) -> str:
    response = requests.get(image_url, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Failed to download image — HTTP {response.status_code}: {image_url}")

    ext = _ext_from_content_type(response.headers.get("Content-Type", ""))
    file_name = f"{uuid.uuid4()}{ext}"

    # Forward slashes — backslashes from os.path.join cause PaddleOCR's C++ engine
    # to raise RuntimeError: Unknown exception on Windows.
    abs_temp = os.path.abspath(TEMP_DIR).replace("\\", "/")
    file_path = f"{abs_temp}/{file_name}"

    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path


def cleanup_image(file_path: str) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: could not delete temp file {file_path}: {e}")


def _ext_from_content_type(content_type: str) -> str:
    ct = content_type.lower()
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "png" in ct:
        return ".png"
    if "bmp" in ct:
        return ".bmp"
    # webp and everything else saved as jpg — paddleocr doesn't support webp extension
    return ".jpg"
