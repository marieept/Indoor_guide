
import numpy as np
from pathlib import Path
from PIL import Image
from wand.image import Image as WandImage


def load_svg(file_path: Path):
    """
    Convert SVG file to a numpy array RGB by ImageMagick (wand)
    """

    with WandImage(filename=str(file_path), resolution=72) as wand_img:
        wand_img.format = "png"
        png_bytes = wand_img.make_blob() # put the image in bytes

    image = Image.open(__import__("io").BytesIO(png_bytes)).convert("RGB") #bytes -> PIL can read

    return np.array(image)

