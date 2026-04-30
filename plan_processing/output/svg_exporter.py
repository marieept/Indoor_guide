"""
Export 2 SVG files:
    - ..._processed.svg : processing plan (black and white) for the graph
    - ..._display.svg : display on web site

PNG are embedded directly into the SVG using base64 encoding.
"""

import base64
import traceback
from pathlib import Path
import cv2
import numpy as np
from config import OUTPUT_DIR, SVG_WIDTH, SVG_HEIGHT

from pipeline.loader import load_plan


def png_to_base64(image: np.ndarray) -> str:
    """a numpy array in PNG base64 -> SVG"""
    success, buffer = cv2.imencode(".png", image) # encode image numpy in PNG in memory
    if not success:
        raise RuntimeError("Impossible d'encoder l'image en PNG.")
    b64 = base64.b64encode(buffer).decode("utf-8") # convert PNG bytes in text base64
    return f"data:image/png;base64,{b64}"


def write_svg(href: str, width: int, height: int, output_path: Path) -> None:
    """writes an SVG file with the image embedded in base64"""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{width}" height="{height}"\n'
        f'     viewBox="0 0 {width} {height}">\n'
        f'  <image href="{href}"\n'
        f'         x="0" y="0"\n'
        f'         width="{width}" height="{height}"/>\n'
        f'</svg>\n'
    )
    output_path.write_text(svg, encoding="utf-8") #write the svg on the computer


def load_display_image(original_path: Path, h: int, w: int):
    """loads the image via the pipeline and resizes it if necessary"""

    load = load_plan(original_path)  # PNG, JPG, SVG, PDF
    img_bgr = cv2.cvtColor(load, cv2.COLOR_RGB2BGR)

    if img_bgr.shape[:2] != (h, w):  # resize if dimensions are different
        img_bgr = cv2.resize(img_bgr, (w, h), interpolation=cv2.INTER_AREA)

    return img_bgr


def export(processed_image: np.ndarray, original_path: Path, plan_name: str):
    """
    Export 2 SVG since image cleaned.
    :return tuple[Path, Path] (path_processed_svg, path_display_svg)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    h, w = processed_image.shape[:2]

    # SVG clean
    href_processed = png_to_base64(processed_image) # binary image -> base64
    path_processed = OUTPUT_DIR / f"{plan_name}_processed.svg" #path output file
    write_svg(href_processed, w, h, path_processed) # write on computer
    print(f"  → processed SVG : {path_processed}")

    # SVG display
    try:
        display_bgr = load_display_image(original_path, h, w) # try to load image
    except Exception:
        print(f"\n ATTENTION IMPOSSIBLE DE CHARGER L'IMAGE DISPLAY")
        traceback.print_exc()
        print("Le SVG display utilisera l'image processed\n")
        display_bgr = processed_image

    href_display = png_to_base64(display_bgr)
    path_display = OUTPUT_DIR / f"{plan_name}_display.svg"
    write_svg(href_display, w, h, path_display)
    print(f"  → display  SVG : {path_display}")

    return path_processed, path_display # return 2 svg paths