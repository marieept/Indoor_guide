"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------

L'objectif est de charger un fichier dans les formats suivant:
    - Obligatoire : PNG, JPG, JPEG, PDF, SVG
    - Optionnel (à voir si j'ai le temps et si je trouve des fichiers OpenSource) : DWG, DXF
"""
from pathlib import Path
import cv2 as cv
import numpy as np
from pdf2image import convert_from_path

from config import POPPLER_PATH
from formats.svg_loader import load_svg

def load_plan(file_path):
    """
    En fonction du formats du fichier appelle un fonction qui va traiter le cas présent
    :param file_path:
    :return:
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    extension = path.suffix

    if extension in (".png", ".jpg", ".jpeg"):
        return load_raster(path)

    elif extension==".pdf":
        return load_pdf(path)

    elif extension== ".svg":
        return load_svg(path)

    else:
        raise ValueError(f"Format non supporté : {extension}")


def load_raster(path):
    image =cv.imread(str(path))

    if image is None:
        raise ValueError(f"OpenCV n'a pas pu lire le fichier : {path}")
    return cv.cvtColor(image, cv.COLOR_BGR2RGB)


def load_pdf(path):
    pages = convert_from_path(str(path), poppler_path=POPPLER_PATH)
    return np.array(pages[0])



