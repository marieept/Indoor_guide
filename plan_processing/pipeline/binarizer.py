"""
we want convert grayscale image in a binary mask, that's to say walls are white (255) and the background is black(0)
why :because it's a convention in image processing
"""

import cv2 as cv
import numpy as np

def binarize(image: np.ndarray, method: str ="otsu"):
    """
    :param image:returned by preprocess.py
    :param method: we have the choice between otsu(quick et automatic threshold ) ou adaptive (Local thresholding, good for uneven lighting
    :return: binary image with value = 0 ou 255
    """

    if method == "otsu":
        #threshold return 2 variables, but are not interest by first one
        _, binary = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    elif method =="adaptive":
        binary = cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, blockSize=15, C=10)

    else:
        raise ValueError(f"Méthode inconnue : {method}. Utiliez 'otsu' ou 'adaptive'.")

    return binary

