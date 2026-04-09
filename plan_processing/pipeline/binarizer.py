"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------

On veut convertir l'image en niveaux de gris en masque binaire, c'est-à-dire
les murs sont en blanc (255) et le fond en noir(0)
Pourquoi :car convention dans le monde du traitement d'image mais pas trouvé d'article parlant du pourquoi
"""

import cv2 as cv
import numpy as np

def binarize(image: np.ndarray, method: str ="otsu"):
    """

    :param image: elle retournée par preprocess.py
    :param method: on a le choix entre otsu(rapide et seuillage automatique) ou adaptive (seuillage local, bien pour inegalités d'éclairage
    :return: une image binaire avec des valeurs = 0 ou 255
    """

    if method == "otsu":
        #threshold renvoi 2 variable mais la premiere ne nous interresse pas donc _
        _, binary = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    elif method =="adaptive":
        binary = cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, blockSize=15, C=10)

    else:
        raise ValueError(f"Méthode inconnue : {method}. Utiliez 'otsu' ou 'adaptive'.")

    return binary

