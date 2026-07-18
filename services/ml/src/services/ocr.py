import os
import gc
import traceback

from paddleocr import PaddleOCR

ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)


def _normalize_path(path: str) -> str:
    # PaddleOCR's C++ inference engine on Windows raises RuntimeError: Unknown
    # exception when the path contains backslashes or mixed separators
    # (e.g. 'd:/temp\\processed.jpg' produced by os.path.join).
    return path.replace("\\", "/")


def _validate_image(image_path: str) -> None:
    import cv2

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if os.path.getsize(image_path) == 0:
        raise ValueError(f"Image file is empty: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot decode image (corrupt or unsupported format): {image_path}")

    h, w = img.shape[:2]
    if h < 10 or w < 10:
        raise ValueError(f"Image is too small for OCR ({w}x{h}px): {image_path}")


def extract_text(image_path: str) -> str:
    image_path = _normalize_path(image_path)
    _validate_image(image_path)

    last_exc = None
    for attempt in range(1, 3):
        try:
            result = ocr.predict(image_path)

            texts = []
            for page in result:
                for text in page.get("rec_texts", []):
                    text = text.strip()
                    if text:
                        texts.append(text)

            gc.collect()
            return " ".join(texts).strip()

        except Exception as exc:
            last_exc = exc
            traceback.print_exc()
            gc.collect()

    raise RuntimeError(
        f"PaddleOCR inference failed after 2 attempts. "
        f"Last error: {type(last_exc).__name__}: {last_exc}"
    ) from last_exc
