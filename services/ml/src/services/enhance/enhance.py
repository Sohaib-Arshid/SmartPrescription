import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _clahe(gray: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)


def _bilateral(gray: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(gray, 9, 75, 75)


def _unsharp(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    return cv2.addWeighted(gray, 2.5, blurred, -1.5, 0)


def _gamma(gray: np.ndarray, value: float = 1.4) -> np.ndarray:
    table = (np.arange(256) / 255.0) ** (1.0 / value) * 255
    return cv2.LUT(gray, table.astype(np.uint8))


def _otsu(gray: np.ndarray) -> np.ndarray:
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img


def _denoised_clahe(gray: np.ndarray) -> np.ndarray:
    denoised = cv2.fastNlMeansDenoising(gray, h=12,
                                        templateWindowSize=7,
                                        searchWindowSize=21)
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(denoised)


def _sauvola_threshold(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
    diff = cv2.subtract(gray, blurred)
    norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    _, thresh = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


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

    # Read as grayscale if already grayscale (preprocessed output), else convert
    if image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    variants: dict[str, str] = {
        "original":      image_path,
        "clahe":         _save(save_dir, "v_clahe.jpg",         _clahe(gray)),
        "bilateral":     _save(save_dir, "v_bilateral.jpg",     _bilateral(gray)),
        "unsharp":       _save(save_dir, "v_unsharp.jpg",       _unsharp(gray)),
        "gamma":         _save(save_dir, "v_gamma.jpg",         _gamma(gray)),
        "otsu":          _save(save_dir, "v_otsu.jpg",          _otsu(gray)),
        "denoised_clahe":_save(save_dir, "v_denoised_clahe.jpg",_denoised_clahe(gray)),
        "sauvola":       _save(save_dir, "v_sauvola.jpg",       _sauvola_threshold(gray)),
    }

    logger.info("Generated %d enhanced variants", len(variants))
    return variants
