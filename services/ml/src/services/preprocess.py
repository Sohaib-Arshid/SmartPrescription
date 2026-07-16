import cv2
import numpy as np
import os


def preprocess_image(
    image_path: str,
    target_dpi_scale: float = 2.0,
    save_dir: str | None = None,
) -> str:
    """
    Advanced preprocessing pipeline for OCR.
    Steps: validate -> resize -> grayscale -> denoise -> deskew ->
           contrast enhance (CLAHE) -> adaptive threshold -> morphology cleanup
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    h, w = image.shape[:2]
    if max(h, w) < 1500:
        image = cv2.resize(
            image, None, fx=target_dpi_scale, fy=target_dpi_scale,
            interpolation=cv2.INTER_CUBIC
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(denoised)

    deskewed = _deskew(contrast_enhanced)

    binary = cv2.adaptiveThreshold(
        deskewed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )

    
    kernel_open = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open, iterations=1)

    kernel_close = np.ones((2, 2), np.uint8)
    final = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close, iterations=1)

    out_dir = save_dir or os.path.dirname(image_path)
    os.makedirs(out_dir, exist_ok=True)
    processed_filename = f"processed_{os.path.basename(image_path)}"
    processed_path = os.path.join(out_dir, processed_filename)

    if not cv2.imwrite(processed_path, final):
        raise IOError(f"Failed to save processed image: {processed_path}")

    return processed_path


def _deskew(gray_image: np.ndarray) -> np.ndarray:
    """Detects skew angle via text contours and rotates image to correct it."""
    
    inverted = cv2.bitwise_not(gray_image)
    thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] == 0:
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
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        gray_image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated