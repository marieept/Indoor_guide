"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------

L'objectif est de prétraiter l'image chargée
Voici la 1er étape du processus complet
"""

import cv2 as cv
import numpy as np


def preprocess(image: np.ndarray):
    """
    Pré prépare l'image pour la binarisation qui suit juste après
    Dans un premier temps on va avoir une conversion en niveaux de gris
    puis une réduction de bruit  avec un filtre gaussien pas tres utile car en général
    les vrais plans sont propre mais si on a un autre format que svg cela peut etre utile

    :param image: RGB, retourné par loader.py
    :return: image en niveau de gris débruitée
    """

    gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)

    # filtre gaussien fait la moyenne des pixel autour
    denoised = cv.GaussianBlur(gray, ksize=(3,3), sigmaX=0) # ksize = zone de pixel autour d'un pixel (impair)
                                                            # sigmax = intensité du lissage, cad les pixels loins ont plus de poids
    return denoised

