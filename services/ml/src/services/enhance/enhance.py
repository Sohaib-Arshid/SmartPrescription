import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _clahe(gray: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)


def _bilateral(gray: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(gray, 7, 50, 50)


def _sharpen(gray: np.ndarray) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(gray, -1, kernel)


def _gamma(gray: np.ndarray, value: float = 1.4) -> np.ndarray:
    table = (np.arange(256) / 255.0) ** (1.0 / value) * 255
    return cv2.LUT(gray, table.astype(np.uint8))


def _otsu(gray: np.ndarray) -> np.ndarray:
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img


def _save(save_dir: str, name: str, image: np.ndarray) -> str:
    path = os.path.join(save_dir, name)
    if not cv2.imwrite(path, image):
        raise IOError(f"Unable to save image: {path}")
    return path.replace("\\", "/")


def generate_enhanced_images(image_path: str, save_dir: str) -> dict[str, str]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to load image.")

    os.makedirs(save_dir, exist_ok=True)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    variants: dict[str, str] = {
        "original": image_path,
        "clahe":    _save(save_dir, "v_clahe.jpg",    _clahe(gray)),
        "bilateral":_save(save_dir, "v_bilateral.jpg",_bilateral(gray)),
        "sharpen":  _save(save_dir, "v_sharpen.jpg",  _sharpen(gray)),
        "gamma":    _save(save_dir, "v_gamma.jpg",    _gamma(gray)),
        "otsu":     _save(save_dir, "v_otsu.jpg",     _otsu(gray)),
    }

    logger.info("Generated %d enhanced variants", len(variants))
    return variants
