import cv2
import numpy as np

from config import SVG_WIDTH, SVG_HEIGHT


def resize_to_target(image: np.ndarray) -> np.ndarray:
    """
    Redimensionne l'image à la taille cible définie dans config.py
    en conservant les proportions (letterbox).

    Les bandes ajoutées pour compléter l'espace sont noires.

    Paramètres
    ----------
    image : np.ndarray
        Image binaire (H, W), dtype uint8

    Retourne
    --------
    np.ndarray
        Image redimensionnée (SVG_HEIGHT, SVG_WIDTH), dtype uint8
    """

    h, w = image.shape[:2]

    ratio = min(SVG_WIDTH / w, SVG_HEIGHT / h)

    new_w = int(w * ratio)
    new_h = int(h * ratio)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

    canvas = np.zeros((SVG_HEIGHT, SVG_WIDTH), dtype=np.uint8)

    x_offset = (SVG_WIDTH - new_w) // 2
    y_offset = (SVG_HEIGHT - new_h) // 2

    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

    return canvas