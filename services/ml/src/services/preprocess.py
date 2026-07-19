import logging
import os
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreprocessConfig:
    max_dim: int = 1800
    min_dim: int = 1000
    upscale_factor: float = 2.0

    denoise_strength: int = 10

    clahe_clip_limit: float = 2.5
    clahe_tile_grid: tuple[int, int] = (8, 8)

    adaptive_block_size: int = 31
    adaptive_c: int = 12

    morph_kernel_size: tuple[int, int] = (2, 2)

    sharpen: bool = True


DEFAULT_CONFIG = PreprocessConfig()


def preprocess_image(
    image_path: str,
    save_dir: str | None = None,
    config: PreprocessConfig = DEFAULT_CONFIG,
) -> str:

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    image = _resize(image, config)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.fastNlMeansDenoising(
        gray,
        h=config.denoise_strength,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    gray = cv2.bilateralFilter(gray, 7, 50, 50)

    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=config.clahe_tile_grid,
    )

    gray = clahe.apply(gray)

    gray = _deskew(gray)

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_block_size,
        config.adaptive_c,
    )

    kernel = np.ones(config.morph_kernel_size, np.uint8)

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1,
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=1,
    )

    if config.sharpen:

        kernel = np.array(
            [
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0],
            ],
            dtype=np.float32,
        )

        binary = cv2.filter2D(binary, -1, kernel)

    processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    processed_path = _build_output_path(image_path, save_dir)

    if not cv2.imwrite(processed_path, processed):
        raise IOError(f"Unable to save processed image to: {processed_path}")

    logger.info("Processed image saved: %s", processed_path)

    return processed_path


def _resize(image: np.ndarray, config: PreprocessConfig):

    h, w = image.shape[:2]

    largest = max(h, w)

    if largest > config.max_dim:

        scale = config.max_dim / largest

        image = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )

    elif largest < config.min_dim:

        image = cv2.resize(
            image,
            None,
            fx=config.upscale_factor,
            fy=config.upscale_factor,
            interpolation=cv2.INTER_CUBIC,
        )

    return image


def _deskew(gray_image: np.ndarray):

    inverted = cv2.bitwise_not(gray_image)

    thresh = cv2.threshold(
        inverted,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

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

    return cv2.warpAffine(
        gray_image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _build_output_path(image_path: str, save_dir: str | None):

    out_dir = save_dir or os.path.dirname(os.path.abspath(image_path))

    os.makedirs(out_dir, exist_ok=True)

    filename = "processed_" + os.path.basename(image_path)

    return out_dir.replace("\\", "/").rstrip("/") + "/" + filename