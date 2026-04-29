"""
morphologic operations to consolidate walls and/or cancel residual noise

Closing (expansion followed by erosion): closes small holes or gaps in the walls.
Opening (erosion followed by expansion): eliminates small groups of noise.
"""

import cv2 as cv
import numpy as np

from config import MORPH_KERNEL_SIZE, MORPH_ITERATIONS


def clean(image: np.ndarray):
    """
    take binary image and clean it
    step : - opening
            - closing

    :param image: binary image with values= 0 or 255
    :return: binary image cleaned
    """
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE))

    opened = cv.morphologyEx(image, cv.MORPH_OPEN, kernel, iterations=MORPH_ITERATIONS)
    closed = cv.morphologyEx(opened, cv.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)

    return closed

