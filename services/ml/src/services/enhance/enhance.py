import cv2
import os


def generate_variants(image_path: str):
    image = cv2.imread(image_path)

    folder = os.path.dirname(image_path)

    variants = []

    # original
    variants.append(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ---------------------------------
    # CLAHE
    # ---------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=3,
        tileGridSize=(8,8)
    )

    clahe_img = clahe.apply(gray)

    p1 = os.path.join(folder,"variant_clahe.jpg")

    cv2.imwrite(p1,clahe_img)

    variants.append(p1)

    # ---------------------------------
    # Adaptive Threshold
    # ---------------------------------

    th = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    p2=os.path.join(folder,"variant_thresh.jpg")

    cv2.imwrite(p2,th)

    variants.append(p2)

    # ---------------------------------
    # Denoise
    # ---------------------------------

    denoise=cv2.fastNlMeansDenoising(gray,None,15)

    p3=os.path.join(folder,"variant_denoise.jpg")

    cv2.imwrite(p3,denoise)

    variants.append(p3)

    # ---------------------------------
    # Sharpen
    # ---------------------------------

    kernel = [
        [0,-1,0],
        [-1,5,-1],
        [0,-1,0]
    ]

    import numpy as np

    kernel=np.array(kernel)

    sharp=cv2.filter2D(gray,-1,kernel)

    p4=os.path.join(folder,"variant_sharp.jpg")

    cv2.imwrite(p4,sharp)

    variants.append(p4)

    return variants