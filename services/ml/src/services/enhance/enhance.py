import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_JPEG_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 95]
_TOP_N = 6


def _clahe(gray: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)


def _bilateral_clahe(gray: np.ndarray) -> np.ndarray:
    smooth = cv2.bilateralFilter(gray, 9, 75, 75)
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(smooth)


def _unsharp(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    return cv2.addWeighted(gray, 2.5, blurred, -1.5, 0)


def _gamma(gray: np.ndarray, value: float = 1.4) -> np.ndarray:
    table = (np.arange(256) / 255.0) ** (1.0 / value) * 255
    return cv2.LUT(gray, table.astype(np.uint8))


def _otsu(gray: np.ndarray) -> np.ndarray:
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img


def _local_adaptive(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10,
    )


def _tophat_enhanced(gray: np.ndarray) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    enhanced = cv2.add(gray, tophat)
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(enhanced)


def _denoised_adaptive(gray: np.ndarray) -> np.ndarray:
    denoised = cv2.fastNlMeansDenoising(gray, h=10,
                                        templateWindowSize=7,
                                        searchWindowSize=21)
    return cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25, 8,
    )


def _ocr_readability_score(gray: np.ndarray) -> float:
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_val = float(np.mean(gray))
    contrast = float(np.std(gray))
    brightness_penalty = abs(mean_val - 180) / 180.0
    return sharpness * (1.0 + contrast / 128.0) * (1.0 - 0.4 * brightness_penalty)


def _save(save_dir: str, name: str, image: np.ndarray) -> str:
    path = os.path.join(save_dir, name)
    if not cv2.imwrite(path, image, _JPEG_PARAMS):
        raise IOError(f"Unable to save image: {path}")
    return path.replace("\\", "/")


def generate_enhanced_images(image_path: str, save_dir: str) -> dict[str, str]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to load image.")

    os.makedirs(save_dir, exist_ok=True)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    # Score every variant in memory before touching disk.
    # Only the top-N are written, avoiding unnecessary I/O.
    candidates: list[tuple[str, np.ndarray, float]] = [
        ("clahe",            _clahe(gray),            0.0),
        ("bilateral_clahe",  _bilateral_clahe(gray),  0.0),
        ("unsharp",          _unsharp(gray),          0.0),
        ("gamma",            _gamma(gray),            0.0),
        ("otsu",             _otsu(gray),             0.0),
        ("local_adaptive",   _local_adaptive(gray),   0.0),
        ("tophat",           _tophat_enhanced(gray),  0.0),
        ("denoised_adaptive",_denoised_adaptive(gray),0.0),
    ]

    scored: list[tuple[str, np.ndarray, float]] = [
        (name, arr, _ocr_readability_score(arr))
        for name, arr, _ in candidates
    ]

    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[:_TOP_N - 1]  # -1 to leave a slot for "original"

    result: dict[str, str] = {"original": image_path}

    for name, arr, score in top:
        path = _save(save_dir, f"v_{name}.jpg", arr)
        result[name] = path

    logger.info(
        "Variants: %d candidates scored, %d selected (top readability)",
        len(scored), len(result),
    )
    return result
