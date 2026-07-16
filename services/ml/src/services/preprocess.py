from utils.image import download_image

@router.post("/process")
def process(request: ProcessRequest):

    image_path = download_image(request.imageUrl)

    print(image_path)

    return {
        "path": image_path
    }