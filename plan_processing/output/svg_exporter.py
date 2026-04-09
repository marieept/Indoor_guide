"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------
Export du résultat du pipeline en deux fichiers SVG :
  - *_processed.svg  : SVG navigable (fond blanc/noir, pour graph.py)
  - *_display.svg    : SVG d'affichage (plan original superposé)

Les PNG sont embarqués en base64 directement dans le SVG.
Le SVG est ainsi totalement autonome (aucune dépendance fichier externe).
"""
import base64
import traceback
from pathlib import Path
import cv2
import numpy as np
from config import OUTPUT_DIR, SVG_WIDTH, SVG_HEIGHT


def _png_to_base64(image: np.ndarray) -> str:
    """Encode un numpy array en PNG base64 pour l'embarquer dans un SVG."""
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError("Impossible d'encoder l'image en PNG.")
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _write_svg(href: str, width: int, height: int, output_path: Path) -> None:
    """Écrit un fichier SVG avec l'image embarquée en base64."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{width}" height="{height}"\n'
        f'     viewBox="0 0 {width} {height}">\n'
        f'  <image href="{href}"\n'
        f'         x="0" y="0"\n'
        f'         width="{width}" height="{height}"/>\n'
        f'</svg>\n'
    )
    output_path.write_text(svg, encoding="utf-8")


def _load_display_image(original_path: Path, h: int, w: int) -> np.ndarray:
    """
    Charge l'image originale pour le SVG d'affichage.

    Stratégie par priorité :
      1. Lire le fichier source directement avec cv2 si c'est un raster (PNG/JPG)
      2. Passer par Wand si c'est un SVG (le fichier source, PAS un SVG wrapper)
      3. Lever une exception explicite — on ne tombe plus silencieusement
         sur le fallback processed_image sans le savoir.

    Le bug précédent : load_plan() était appelé sur original_path qui pouvait
    être un SVG "wrapper" (<image href="chemin absolu Windows">), Wand produisait
    un rectangle blanc, l'exception était avalée par le except, et le display SVG
    finissait avec l'image binaire processed à la place de l'original.
    """
    suffix = original_path.suffix.lower()

    if suffix in (".png", ".jpg", ".jpeg"):
        # Lecture directe, pas besoin de Wand
        img_bgr = cv2.imread(str(original_path), cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise FileNotFoundError(f"cv2 ne peut pas lire : {original_path}")

    elif suffix == ".svg":
        # On utilise Wand directement sur le SVG SOURCE (pas un wrapper).
        # Si ce SVG contient lui-même un <image href> avec un chemin cassé,
        # Wand retournera une image blanche → on le détecte et on plante proprement.
        from wand.image import Image as WandImage
        import io
        from PIL import Image as PILImage
        PILImage.MAX_IMAGE_PIXELS = None

        with WandImage(filename=str(original_path), resolution=150) as wimg:
            wimg.format = "png"
            png_bytes = wimg.make_blob()

        pil_img = PILImage.open(io.BytesIO(png_bytes)).convert("RGB")
        arr = np.array(pil_img)

        # Détection rectangle blanc : si >99% des pixels sont blancs, Wand a échoué
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        white_ratio = np.sum(gray > 250) / gray.size
        if white_ratio > 0.99:
            raise RuntimeError(
                f"Wand a produit une image quasi-entièrement blanche pour {original_path}.\n"
                "Vérifiez que ce SVG ne contient pas un <image href> avec un chemin cassé."
            )

        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    elif suffix == ".pdf":
        from pipeline.loader import load_plan
        arr = load_plan(original_path)           # retourne RGB
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    else:
        raise ValueError(f"Format non supporté pour le display : {suffix}")

    # Redimensionner à la taille de l'image processed si nécessaire
    if img_bgr.shape[:2] != (h, w):
        img_bgr = cv2.resize(img_bgr, (w, h), interpolation=cv2.INTER_AREA)

    return img_bgr


def export(
    processed_image: np.ndarray,
    original_path: Path,
    plan_name: str,
) -> tuple[Path, Path]:
    """
    Exporte deux SVG depuis l'image traitée.

    Paramètres
    ----------
    processed_image : np.ndarray
        Image binaire issue du pipeline (H, W), dtype uint8
    original_path : Path
        Chemin vers le fichier source ORIGINAL (PNG, JPG, SVG ou PDF).
        Doit pointer vers le fichier réel, pas un SVG wrapper.
    plan_name : str
        Nom de base pour les fichiers de sortie

    Retourne
    --------
    tuple[Path, Path]
        (path_processed_svg, path_display_svg)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    h, w = processed_image.shape[:2]

    # ── SVG traité (navigable) ────────────────────────────────────────────────
    href_processed = _png_to_base64(processed_image)
    path_processed = OUTPUT_DIR / f"{plan_name}_processed.svg"
    _write_svg(href_processed, w, h, path_processed)
    print(f"  → processed SVG : {path_processed}")

    # ── SVG affichage (plan original) ─────────────────────────────────────────
    try:
        display_bgr = _load_display_image(original_path, h, w)
    except Exception as e:
        # On affiche l'erreur CLAIREMENT au lieu de l'avaler silencieusement,
        # et on utilise processed en fallback en le signalant.
        print(f"\n[AVERTISSEMENT] Impossible de charger l'image display :")
        traceback.print_exc()
        print("→ Fallback : le SVG display utilisera l'image processed (binaire).\n")
        display_bgr = processed_image

    href_display = _png_to_base64(display_bgr)
    path_display = OUTPUT_DIR / f"{plan_name}_display.svg"
    _write_svg(href_display, w, h, path_display)
    print(f"  → display  SVG : {path_display}")

    return path_processed, path_display