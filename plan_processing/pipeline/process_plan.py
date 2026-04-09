"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------
Processus de chaque etape pour le pipeline complet
ordre :
    - chargement
    - binarisation
    - debruitage
    - nettoyage morphologique
    - Calibration
    - Masque batiment
    - fermeture des portes
"""

from pathlib import Path

import numpy as np

from pipeline.loader     import load_plan
from pipeline.preprocess   import preprocess
from pipeline.binarizer  import binarize
from boundary.contour    import apply_boundary
from doors.door_closer   import close_doors
from calibration.scale   import resize_to_target
from output.svg_exporter import export


def process(file_path: str) -> tuple[Path, Path]:
    """
    Exécute le pipeline complet de traitement d'un plan architectural.

    Étapes :
        1. Chargement
        2. Prétraitement (niveaux de gris + débruitage)
        3. Binarisation
        4. Nettoyage morphologique
        5. Boundary (masque extérieur)
        6. Fermeture des portes
        7. Redimensionnement à la taille cible
        8. Export SVG

    Paramètres
    ----------
    file_path : str | Path
        Chemin vers le plan à traiter

    Retourne
    --------
    tuple[Path, Path]
        (chemin SVG traité, chemin SVG affichage)
    """

    file_path = Path(file_path)
    plan_name = file_path.stem

    print(f"Chargement de {file_path.name}...")
    image = load_plan(file_path)

    print("Prétraitement...")
    gray = preprocess(image)

    print("Binarisation...")
    binary = binarize(gray)

    print("Boundary...")
    bounded = apply_boundary(binary)

    print("Fermeture des portes...")
    closed = close_doors(bounded)

    path_processed, path_display = export(closed, file_path, plan_name)

    print(f"SVG traité   : {path_processed}")
    print(f"SVG affichage : {path_display}")

    return path_processed, path_display