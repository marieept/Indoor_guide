"""
The first step of the process
"""


import cv2 as cv
import numpy as np


def preprocess(image: np.ndarray):
    """
    Pre-preparing the image for binarization, which follows immediately.
    First, we'll perform a grayscale conversion.
    Then, noise reduction with a Gaussian filter, which isn't very useful because, generally,
    the actual images are clean, but if you have a format other than SVG, it can be helpful.

    :param image: RGB, return by loader.py
    :return: grayscale image denoised
    """

    gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)    #conversion image RGB to gray

    # gaussian filter do the mean of pixel arround
    denoised = cv.GaussianBlur(gray, ksize=(3,3), sigmaX=0) # ksize =pixel zone arround one pixel (odd)
                                                            # sigmax = intensity smoothing, pixels far away are more heavy
    return denoised

