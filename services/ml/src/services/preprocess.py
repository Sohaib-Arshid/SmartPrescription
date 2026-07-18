import cv2
import numpy as np
import os


def preprocess_image(
    image_path: str,
    target_dpi_scale: float = 2.0,
    save_dir: str | None = None,
) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    h, w = image.shape[:2]

    # Resize
    if max(h, w) > 1800:
        scale = 1800 / max(h, w)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    elif max(h, w) < 1000:
        image = cv2.resize(image, None, fx=target_dpi_scale, fy=target_dpi_scale, interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # Deskew
    deskewed = _deskew(contrast)

    # Adaptive threshold
    binary = cv2.adaptiveThreshold(
        deskewed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15,
    )

    # Morphology
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Convert to 3-channel BGR — PaddleOCR 3.2 / PaddleX requires a 3-channel image.
    processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    # Save — forward slashes only; backslashes from os.path.join cause
    # PaddleOCR's C++ engine to raise RuntimeError: Unknown exception on Windows.
    out_dir = save_dir or os.path.dirname(os.path.abspath(image_path))
    os.makedirs(out_dir, exist_ok=True)

    basename = f"processed_{os.path.basename(image_path)}"
    processed_path = out_dir.replace("\\", "/").rstrip("/") + "/" + basename

    if not cv2.imwrite(processed_path, processed):
        raise IOError(f"Unable to save processed image to: {processed_path}")

    return processed_path


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

    (h, w) = gray_image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    return cv2.warpAffine(
        gray_image, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
