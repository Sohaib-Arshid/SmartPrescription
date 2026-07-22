import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_JPEG_PARAMS = [cv2.IMWRITE_JPEG_QUALITY, 95]


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


def _laplacian_var(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _ocr_readability_score(gray: np.ndarray) -> float:
    sharpness = _laplacian_var(gray)
    mean_val = float(np.mean(gray))
    contrast = float(np.std(gray))
    brightness_penalty = abs(mean_val - 180) / 180.0
    score = sharpness * (1.0 + contrast / 128.0) * (1.0 - 0.4 * brightness_penalty)
    return score


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

    candidates = {
        "original":        (image_path, None),
        "clahe":           (_save(save_dir, "v_clahe.jpg",           _clahe(gray)),           None),
        "bilateral_clahe": (_save(save_dir, "v_bilateral_clahe.jpg", _bilateral_clahe(gray)), None),
        "unsharp":         (_save(save_dir, "v_unsharp.jpg",         _unsharp(gray)),         None),
        "gamma":           (_save(save_dir, "v_gamma.jpg",           _gamma(gray)),           None),
        "otsu":            (_save(save_dir, "v_otsu.jpg",            _otsu(gray)),            None),
        "local_adaptive":  (_save(save_dir, "v_local_adaptive.jpg",  _local_adaptive(gray)),  None),
        "tophat":          (_save(save_dir, "v_tophat.jpg",          _tophat_enhanced(gray)), None),
        "denoised_adaptive":(_save(save_dir, "v_denoised_adaptive.jpg", _denoised_adaptive(gray)), None),
    }

    scored = {}
    for name, (path, _) in candidates.items():
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            scored[name] = (path, _ocr_readability_score(img))

    ranked = sorted(scored.items(), key=lambda x: x[1][1], reverse=True)
    top_names = {name for name, _ in ranked[:6]}

    result: dict[str, str] = {}
    for name, (path, score) in scored.items():
        if name in top_names:
            result[name] = path

    if "original" not in result:
        result["original"] = image_path

    logger.info(
        "Variants generated: %d total, %d selected by readability score",
        len(scored), len(result),
    )
    return result
