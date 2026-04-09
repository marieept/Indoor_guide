"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------


"""

import numpy as np
from pathlib import Path
from PIL import Image
from wand.image import Image as WandImage


def load_svg(file_path: Path) -> np.ndarray:
    """
    Convertit un fichier SVG en numpy array RGB via ImageMagick (Wand).

    Paramètres
    ----------
    file_path : Path
        Chemin vers le fichier SVG

    Retourne
    --------
    np.ndarray
        Image RGB (H, W, 3), dtype uint8
    """

    with WandImage(filename=str(file_path), resolution=72) as wand_img:
        wand_img.format = "png"
        png_bytes = wand_img.make_blob()

    image = Image.open(__import__("io").BytesIO(png_bytes)).convert("RGB")

    return np.array(image)

