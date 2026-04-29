

from pathlib import Path
import cv2 as cv
import numpy as np
from pdf2image import convert_from_path

from config import POPPLER_PATH
from formats.svg_loader import load_svg

def load_plan(file_path):
    """
    this function will treat the file format of PNG, JPEG, PDF, SVG
    if not error
    :param file_path:
    :return:
    """
    path = Path(file_path)  # update a character to a path

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    extension = path.suffix #return the file format

    if extension in (".png", ".jpg", ".jpeg"):
        return load_raster(path)

    elif extension==".pdf":
        return load_pdf(path)

    elif extension== ".svg":
        return load_svg(path)

    else:
        raise ValueError(f"Format non supporté : {extension}")


def load_raster(path):
    """
    read image with openCV
    :return: an array numpy RGB by conversion BGR
    """
    image =cv.imread(str(path))

    if image is None:
        raise ValueError(f"OpenCV n'a pas pu lire le fichier : {path}")
    return cv.cvtColor(image, cv.COLOR_BGR2RGB)


def load_pdf(path):
    pages = convert_from_path(str(path), poppler_path=POPPLER_PATH) # return list image
    return np.array(pages[0])   #we take only the first page



