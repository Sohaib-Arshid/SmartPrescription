import os
import traceback

from paddleocr import PaddleOCR

# ---------------------------------------------------------------------------
# Singleton PaddleOCR instance.
#
# WHY A SINGLETON:
# PaddleOCR wraps a PaddlePaddle C++ inference predictor. Constructing and
# destroying it per-request causes two problems:
#
#   1. MEMORY CORRUPTION / RuntimeError: Unknown exception
#      Calling `del ocr` drops the Python reference but the underlying C++
#      predictor (thread pools, memory arenas, operator registry) does NOT
#      fully release. Each cycle leaves residual C++ heap state. After enough
#      requests the process either OOMs or the inference engine is left in a
#      corrupt state, producing RuntimeError or OpenCV OutOfMemoryError.
#
#   2. ECONNRESET FROM NODE
#      Constructing PaddleOCR takes 2–6 s per request (model loading + C++
#      predictor init). That overhead pushes response time high enough that
#      Node's HTTP timeout fires and drops the connection mid-request.
#
# The singleton is created once at startup (loaded with the FastAPI app) and
# reused for every request. `ocr.predict()` is safe to call repeatedly on
# the same instance — the C++ predictor holds no mutable state between calls.
# ---------------------------------------------------------------------------
_ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)


def _normalize_path(path: str) -> str:
    # PaddleOCR's C++ engine on Windows raises RuntimeError: Unknown exception
    # when the path contains backslashes or mixed separators produced by
    # os.path.join (e.g. 'd:/temp\\processed.jpg').
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

    try:
        result = _ocr.predict(image_path)

        texts = []
        for page in result:
            for text in page.get("rec_texts", []):
                text = text.strip()
                if text:
                    texts.append(text)

        return " ".join(texts).strip()

    except Exception as exc:
        traceback.print_exc()
        raise RuntimeError(f"PaddleOCR inference failed: {type(exc).__name__}: {exc}") from exc
