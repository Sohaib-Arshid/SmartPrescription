import logging
import os
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreprocessConfig:
    max_dim: int = 2000
    min_dim: int = 1000
    upscale_factor: float = 2.0
    clahe_clip_limit: float = 3.0
    clahe_tile_grid: tuple[int, int] = (8, 8)
    adaptive_block_size: int = 25
    adaptive_c: int = 10
    morph_kernel_size: tuple[int, int] = (2, 2)


DEFAULT_CONFIG = PreprocessConfig()

# Hard cap applied before cv2.imread so we never attempt to decompress a
# 5100×6600 (96 MB) scan straight into RAM.  PIL.Image.thumbnail() uses
# a streaming JPEG decoder and only decompresses to the requested size,
# so RAM usage stays proportional to the *output* not the original.
_SAFE_READ_MAX_DIM = 1200


def _safe_imread(image_path: str) -> np.ndarray:
    """
    Load an image safely regardless of its original resolution.

    PIL reads JPEG headers, determines original size, and downscales
    during decode (JPEG DCT shortcuts).  Only then is the result
    converted to a numpy BGR array for cv2.  This avoids the
    cv2.imread() OOM crash on high-DPI scans (e.g. 5100×6600 @ 300 DPI).
    """
    with Image.open(image_path) as pil_img:
        w, h = pil_img.size
        if max(w, h) > _SAFE_READ_MAX_DIM:
            logger.info(
                "Large image detected (%dx%d). Downscaling to max_dim=%d before decode.",
                w, h, _SAFE_READ_MAX_DIM,
            )
            # thumbnail() modifies in-place and preserves aspect ratio
            pil_img.thumbnail((_SAFE_READ_MAX_DIM, _SAFE_READ_MAX_DIM), Image.LANCZOS)

        # Ensure BGR for cv2 compatibility
        pil_rgb = pil_img.convert("RGB")
        arr = np.array(pil_rgb, dtype=np.uint8)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def preprocess_image(
    image_path: str,
    save_dir: str | None = None,
    config: PreprocessConfig = DEFAULT_CONFIG,
) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = _safe_imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    image = _resize(image, config)
    image = _correct_perspective(image)
    image = _remove_shadow(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = _normalize_illumination(gray)
    gray = _denoise(gray)
    gray = _deskew(gray)

    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=config.clahe_tile_grid,
    )
    gray = clahe.apply(gray)
    gray = _unsharp_mask(gray)

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_block_size,
        config.adaptive_c,
    )

    kernel = np.ones(config.morph_kernel_size, np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    processed_path = _build_output_path(image_path, save_dir)

    if not cv2.imwrite(processed_path, processed):
        raise IOError(f"Unable to save processed image: {processed_path}")

    logger.info("Preprocessed: %s", processed_path)
    return processed_path


def _resize(image: np.ndarray, config: PreprocessConfig) -> np.ndarray:
    h, w = image.shape[:2]
    largest = max(h, w)
    if largest > config.max_dim:
        scale = config.max_dim / largest
        return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    if largest < config.min_dim:
        return cv2.resize(image, None, fx=config.upscale_factor, fy=config.upscale_factor,
                          interpolation=cv2.INTER_CUBIC)
    return image


def _correct_perspective(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image

    largest = max(contours, key=cv2.contourArea)
    h, w = image.shape[:2]

    if cv2.contourArea(largest) < 0.2 * h * w:
        return image

    rect = cv2.minAreaRect(largest)
    angle = rect[2]

    if abs(angle) < 1.0 or abs(angle - 90) < 1.0:
        return image

    if angle < -45:
        angle += 90

    if abs(angle) > 15:
        return image

    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def _remove_shadow(image: np.ndarray) -> np.ndarray:
    channels = cv2.split(image)
    result = []
    for ch in channels:
        dilated = cv2.dilate(ch, np.ones((7, 7), np.uint8))
        bg = cv2.medianBlur(dilated, 21)
        diff = 255 - cv2.absdiff(ch, bg)
        norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        result.append(norm)
    return cv2.merge(result)


def _normalize_illumination(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (51, 51), 0)
    denom = blurred.astype(np.float32) + 1.0
    norm = gray.astype(np.float32) / denom
    # Stretch to [0, 255] based on actual range so dark and bright images both work.
    lo, hi = norm.min(), norm.max()
    if hi - lo < 1e-6:
        return gray
    norm = (norm - lo) / (hi - lo) * 255.0
    return np.clip(norm, 0, 255).astype(np.uint8)


def _denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(gray, 9, 75, 75)


def _unsharp_mask(gray: np.ndarray, strength: float = 1.5) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    sharpened = cv2.addWeighted(gray, 1 + strength, blurred, -strength, 0)
    return sharpened


def _deskew(gray_image: np.ndarray) -> np.ndarray:
    inverted = cv2.bitwise_not(gray_image)
    thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))

    if len(coords) == 0:
        return gray_image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5:
        return gray_image

    h, w = gray_image.shape
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray_image, matrix, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def _build_output_path(image_path: str, save_dir: str | None) -> str:
    out_dir = save_dir or os.path.dirname(os.path.abspath(image_path))
    os.makedirs(out_dir, exist_ok=True)
    filename = "processed_" + os.path.basename(image_path)
    return out_dir.replace("\\", "/").rstrip("/") + "/" + filename
