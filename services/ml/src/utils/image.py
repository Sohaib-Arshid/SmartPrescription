import os
import uuid
import requests

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)


def download_image(image_url: str) -> str:

    response = requests.get(image_url)

    if response.status_code != 200:
        raise Exception("Failed to download image")

    file_name = f"{uuid.uuid4()}.jpg"

    file_path = os.path.join(TEMP_DIR, file_name)

    with open(file_path, "wb") as file:
        file.write(response.content)

    return file_path


def cleanup_image(file_path: str):

    if os.path.exists(file_path):
        os.remove(file_path)