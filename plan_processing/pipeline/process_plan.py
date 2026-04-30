"""
Process for each step in the complete pipeline
order:
    - loading
    - binarization
    - denoising
    - morphological cleaning
    - calibration
    - building masking
    - closing the gates
"""

from pathlib import Path
import cv2 as cv
import numpy as np

from pipeline.loader     import load_plan
from pipeline.preprocess   import preprocess
from pipeline.binarizer  import binarize
from boundary.contour    import apply_boundary
from doors.door_closer   import close_doors
from calibration.scale   import resize_to_target
from output.svg_exporter import export


def process(file_path: str):
    """
    Run the complete process
    """
    file_path = Path(file_path)
    plan_name = file_path.stem

    print(f"Chargement de {file_path.name}...")
    image = load_plan(file_path)

    print("Prétraitement...")
    gray = preprocess(image)

    print("Binarisation...")
    binary = binarize(gray)

    # Inversion: walls in black, floor in white (image processing convention)
    binary = cv.bitwise_not(binary)

    print("Boundary...")
    bounded = apply_boundary(binary)

    print("Fermeture des portes...")
    closed = close_doors(bounded)

    # inversion before export : walls in white, ground in black
    closed = cv.bitwise_not(closed)

    path_processed, path_display = export(closed, file_path, plan_name)

    print(f"SVG traité   : {path_processed}")
    print(f"SVG affichage : {path_display}")

    return path_processed, path_display