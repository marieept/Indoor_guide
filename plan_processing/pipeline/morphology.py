"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------

Opérations morphologique pour consolider les murs et/ou supprimer le bruit residuel

Le closing (dilatation puis erosion) : ferme des petits trou ou gap dans les murs
L'opening (erosion puis dilatation) : supprime les petits ilots de bruit.
"""

import cv2 as cv
import numpy as np

from config import MORPH_KERNEL_SIZE, MORPH_ITERATIONS


def clean(image: np.ndarray):
    """
    prend un image binaire et la nettoie
    etape : - opening
            - closing

    :param image: image binaire avec des valeurs 0 ou 255
    :return: image binaire nettoyée
    """
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE))

    opened = cv.morphologyEx(image, cv.MORPH_OPEN, kernel, iterations=MORPH_ITERATIONS)
    closed = cv.morphologyEx(opened, cv.MORPH_CLOSE, kernel, iterations=MORPH_ITERATIONS)

    return closed

