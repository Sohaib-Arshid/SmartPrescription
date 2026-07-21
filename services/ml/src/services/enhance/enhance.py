import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def clahe(gray: np.ndarray) -> np.ndarray:
    clahe_filter = cv2.createCLAHE(
        clipLimit=2.5,
        tileGridSize=(8, 8),
    )
    return clahe_filter.apply(gray)


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        12,
    )


def otsu_threshold(gray: np.ndarray) -> np.ndarray:
    _, img = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    return img


def bilateral(gray: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(
        gray,
        7,
        50,
        50,
    )


def sharpen(gray: np.ndarray) -> np.ndarray:
    kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )
    return cv2.filter2D(gray, -1, kernel)


def gamma(gray: np.ndarray, gamma_value: float = 1.4) -> np.ndarray:
    inv = 1.0 / gamma_value
    table = np.array(
        [
            ((i / 255.0) ** inv) * 255
            for i in range(256)
        ]
    ).astype("uint8")
    return cv2.LUT(gray, table)


def morphology(gray: np.ndarray) -> np.ndarray:
    kernel = np.ones((2, 2), np.uint8)
    gray = cv2.morphologyEx(
        gray,
        cv2.MORPH_OPEN,
        kernel,
    )
    gray = cv2.morphologyEx(
        gray,
        cv2.MORPH_CLOSE,
        kernel,
    )
    return gray


def _save(save_dir: str, name: str, image: np.ndarray) -> str:
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, name)

    if not cv2.imwrite(path, image):
        raise IOError(f"Unable to save image to: {path}")

    return path.replace("\\", "/")


def generate_enhanced_images(image_path: str) -> dict[str, str]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to load image.")

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    save_dir = os.path.dirname(os.path.abspath(image_path))
    outputs: dict[str, str] = {}
    outputs["original"] = image_path

    clahe_img = clahe(gray)
    outputs["clahe"] = _save(
        save_dir,
        "clahe.jpg",
        clahe_img,
    )

    bilateral_img = bilateral(gray)
    outputs["bilateral"] = _save(
        save_dir,
        "bilateral.jpg",
        bilateral_img,
    )

    sharpen_img = sharpen(gray)
    outputs["sharpen"] = _save(
        save_dir,
        "sharpen.jpg",
        sharpen_img,
    )

    gamma_img = gamma(gray)
    outputs["gamma"] = _save(
        save_dir,
        "gamma.jpg",
        gamma_img,
    )

    adaptive_img = adaptive_threshold(gray)
    outputs["adaptive"] = _save(
        save_dir,
        "adaptive.jpg",
        adaptive_img,
    )

    otsu_img = otsu_threshold(gray)
    outputs["otsu"] = _save(
        save_dir,
        "otsu.jpg",
        otsu_img,
    )

    morph_img = morphology(adaptive_img)
    outputs["morphology"] = _save(
        save_dir,
        "morphology.jpg",
        morph_img,
    )

    logger.info("Generated %d enhanced variants for %s", len(outputs), image_path)

    return outputs