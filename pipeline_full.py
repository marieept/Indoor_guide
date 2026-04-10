import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import base64, io
from PIL import Image as PILImage

# Racine du projet
ROOT = Path(__file__).parent.resolve()
os.chdir(ROOT)

# Imports partie plan_processing/
sys.path.insert(0, str(ROOT / "plan_processing"))
from plan_processing.pipeline.process_plan import process

# Imports partie graph/
sys.path.insert(0, str(ROOT / "graph"))
from graph import (
    squelettize,
    detect_nodes,
    edit_nodes,
    put_rooms,
    put_transitions,
    put_stairs_pmr,
    generate_edges,
    connect_nodes,
    merge_and_save,
)

# Chargement de config.json
def configure() -> dict:
    config_path = ROOT / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"config.json introuvable dans {ROOT}\n"
            f"Créez-le en suivant le format décrit en en-tête de ce fichier."
        )
    with open(config_path, "r") as f:
        config = json.load(f)

    for floor in config["etages"]:
        if "svg_display" not in floor:
            raise KeyError(
                f"Étage {floor.get('floor', '?')} : "
                f"'svg_display' manquant dans config.json"
            )
        svg_path = ROOT / floor["svg_display"]
        if not svg_path.exists():
            raise FileNotFoundError(
                f"Étage {floor.get('floor', '?')} : "
                f"fichier introuvable : {svg_path}"
            )
    return config

# Étape 1 : nettoyage via la pipeline du collègue
def clean_floor(floor: dict):
    source = floor["svg_display"]
    path_processed, path_display = process(file_path=str(ROOT / source))

    floor["svg"]         = str(path_processed)
    floor["svg_display"] = str(path_display)

    # Lire les dimensions originales et processed pour calculer le ratio
    tree_orig = ET.parse(str(ROOT / source))
    root_orig = tree_orig.getroot()
    orig_w = float(root_orig.attrib["width"])
    orig_h = float(root_orig.attrib["height"])

    tree_proc = ET.parse(str(path_processed))
    root_proc = tree_proc.getroot()
    proc_w = float(root_proc.attrib["width"])
    proc_h = float(root_proc.attrib["height"])

    floor["width"]   = int(proc_w)
    floor["height"]  = int(proc_h)
    # Ratio pour rescaler les coords vers l'espace original (= espace display)
    floor["scale_x"] = orig_w / proc_w
    floor["scale_y"] = orig_h / proc_h

# Étapes 2-N : graph interactif
def build_graph_for_floor(floor: dict):
    """
    Exécute toutes les étapes de graph.py pour un étage.
        - Squelettisation  sur floor["svg"]         (SVG nettoyé)
        - Affichage salles sur floor["svg_display"]  (SVG avec portes)
    """
    sx = floor.get("scale_x", 1.0)
    sy = floor.get("scale_y", 1.0)

    img_small, img_color, navigable, skel = squelettize(floor)
    nodes = detect_nodes(skel, floor)
    nav_nodes = edit_nodes(nodes, img_color, floor)
    rooms = put_rooms(floor)
    transitions = put_transitions(floor)

    edges = generate_edges(nav_nodes, navigable, floor)
    edges = put_stairs_pmr(nav_nodes, edges, floor)
    edges = connect_nodes(nav_nodes, rooms, transitions, edges, floor)

    all_floor_nodes = nav_nodes + rooms + transitions

    import cv2

    # Image de debug (copie)
    debug_img = img_color.copy()

    # ⚠️ IMPORTANT : utiliser les noeuds AVANT scaling
    nodes_for_display = nav_nodes + rooms + transitions

    for e in edges:
        n1 = next(n for n in nodes_for_display if n["id"] == e["from"])
        n2 = next(n for n in nodes_for_display if n["id"] == e["to"])

        x1, y1 = int(n1["x"]) //4, int(n1["y"])//4
        x2, y2 = int(n2["x"]) //4, int(n2["y"])//4

        # Dessin de l'arête
        cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Sauvegarde de l'image
    cv2.imwrite(f"debug_edges_floor_{floor['floor']}.png", debug_img)

    # Rescaling des noeuds ET des poids en tout dernier
    for n in all_floor_nodes:
        n["x"] = int(n["x"] * sx)
        n["y"] = int(n["y"] * sy)

    scale_w = (sx + sy) / 2
    for e in edges:
        if "weight" in e:
            e["weight"] = e["weight"] * scale_w

    return all_floor_nodes, edges

# Pipeline principale
def run_full_pipeline():
    config = configure()
    all_nodes = []
    all_edges = []

    for floor in config["etages"]:
        print(f"Etage {floor['floor']}...")
        clean_floor(floor)

        floor_nodes, floor_edges = build_graph_for_floor(floor)

        all_nodes.extend(floor_nodes)
        all_edges.extend(floor_edges)

        print(f"Etage {floor['floor']} termine ({len(floor_nodes)} noeuds, {len(floor_edges)} aretes)")

    config["output"] = str(ROOT / config["output"])
    merge_and_save(all_nodes, all_edges, config)
    print(f"Graphe sauvegarde -> {config['output']}")

if __name__ == "__main__":
    run_full_pipeline()