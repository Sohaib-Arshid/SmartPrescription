import easyocr

reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def extract_text(image_path: str) -> str:
    result = reader.readtext(image_path)

    extracted_text = " ".join(
        text for _, text, _ in result
    )

    return extracted_text