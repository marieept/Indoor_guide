import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import time
import cv2

# Absolute path to the directory containing this file
ROOT = Path(__file__).parent.resolve()
os.chdir(ROOT)

# Add plan_processinf/ and graph/ to the Python path so their modules can be imported
sys.path.insert(0, str(ROOT / "plan_processing"))
from plan_processing.pipeline.process_plan import process

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
def configure():
    """ Loads the configuration from config.json"""
    
    config_path = ROOT / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"config.json introuvable dans {ROOT}")
    
    with open(config_path, "r") as f:
        config = json.load(f)

    for floor in config["etages"]:
        if "svg_display" not in floor:
            raise KeyError(f"'svg_display' manquant dans config.json")
        svg_path = ROOT / floor["svg_display"]
        if not svg_path.exists():
            raise FileNotFoundError(f"fichier introuvable : {svg_path}")
    return config

def clean_floor(floor):
    """ Runs the cleaning pipeline on a floor's SVG and computes the scale ratio
    between the original file and the processed output"""

    original_svg = floor["svg_display"] # relative path to the original SVG from config.json
    path_processed, path_display = process(file_path=str(ROOT / original_svg))

    # Update floor with the paths to the processed and display SVG
    floor["svg"] = str(path_processed)
    floor["svg_display"] = str(path_display)

    # Read dimensions of the original SVG (before cleaning)
    tree_orig = ET.parse(str(ROOT / original_svg))
    root_orig = tree_orig.getroot()
    orig_w = float(root_orig.attrib["width"])
    orig_h = float(root_orig.attrib["height"])

    # Read dimensions of the processed SVG (after cleaning)
    tree_proc = ET.parse(str(path_processed))
    root_proc = tree_proc.getroot()
    proc_w = float(root_proc.attrib["width"])
    proc_h = float(root_proc.attrib["height"])

    # Store processed dimensions (used by graph.py so it has to be like the processed SVG)
    floor["width"]   = int(proc_w)
    floor["height"]  = int(proc_h)

    # Scale ratio to convert node coordinates from processed space to original space
    # Applied at the end of build_graph_for_floor so that coordinates match the display
    floor["scale_x"] = orig_w / proc_w
    floor["scale_y"] = orig_h / proc_h


def build_graph_for_floor(floor):
    """ Runs all graph construction steps for a single floor"""

    # Get scale ratio computed in clean_floor, default 1
    sx = floor.get("scale_x", 1.0)
    sy = floor.get("scale_y", 1.0)

    # Step 1 : skeletonize the cleaned SVG the extract the navigation skeleton
    img_small, img_color, navigable, skel = squelettize(floor)

    # Step 2 : detect nodes from the skeleton
    nodes = detect_nodes(skel, floor)

    # Step 3 : manually add or remove navigation nodes
    nav_nodes = edit_nodes(nodes, img_color, floor)

    # Step 4 : manually place rooms and transitions
    rooms = put_rooms(floor)
    transitions = put_transitions(floor)

    # Step 5 : generate edges between navigation nodes
    edges = generate_edges(nav_nodes, navigable, floor)

    # Step 6 : manually mark stair steps not accessible to PRM (person with reduced mobility)
    edges = put_stairs_pmr(nav_nodes, edges, floor)

    # Step 7 : connect rooms and transitions to the nearest navigation node
    edges = connect_nodes(nav_nodes, rooms, transitions, edges, floor, navigable)

    all_floor_nodes = nav_nodes + rooms + transitions

    # Draw edges on a debug image to visually see the graph
    debug_img = img_color.copy()
    nodes_for_display = nav_nodes + rooms + transitions

    # img_color is in processed space, so coordinates must be too
    # so it must be done before scaling
    for edge in edges:
        # Find the two nodes connected by this edge
        n1 = None
        n2 = None
        for n in nodes_for_display:
            if n["id"] == edge["from"]:
                n1 = n
            if n["id"] == edge["to"]:
                n2 = n
            if n1 and n2: #both nodes found
                break

        x1, y1 = int(n1["x"]) //4, int(n1["y"])//4
        x2, y2 = int(n2["x"]) //4, int(n2["y"])//4

        # Draw the edge
        cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Save the debug image
    cv2.imwrite(str(ROOT / "output" / f"debug_edges_floor_{floor['floor']}.png"), debug_img)

    # Apply scale ratio to node coordinates and edges weights
    # Because the image displayed on the website is the original
    for n in all_floor_nodes:
        n["x"] = int(n["x"] * sx)
        n["y"] = int(n["y"] * sy)

    # Average scale ratio for edge weights
    scale_w = (sx + sy) / 2
    for e in edges:
        if "weight" in e:
            e["weight"] = e["weight"] * scale_w

    return all_floor_nodes, edges

def run_full_pipeline():
    """ Runs the full pipeline for all floors : cleaning, graph construction and saving"""

    config = configure()
    all_nodes = []
    all_edges = []

    # Create the output directory if it doesn't exist
    Path(config["output"]).parent.mkdir(parents=True, exist_ok=True)

    for floor in config["etages"]:
        print(f"Etage {floor['floor']}...")

        # Step 1 : clean the floor plan
        t0= time.time()
        clean_floor(floor)
        t1 =time.time()
        print(f"[PERF] Nettoyage etage {floor['floor']} : {(t1-t0)*1000:.2f} ms")

        # Step 2 : build the graph for this floor
        t2= time.time()
        floor_nodes, floor_edges = build_graph_for_floor(floor)
        t3= time.time()
        print(f"[PERF] Construction graphe etage {floor['floor']} : {(t3-t2)*1000:.2f} ms")

        all_nodes.extend(floor_nodes)
        all_edges.extend(floor_edges)

        print(f"Etage {floor['floor']} termine ({len(floor_nodes)} noeuds, {len(floor_edges)} aretes)")

    # Convert output path to absolute path before saving
    config["output"] = str(ROOT / config["output"])
    merge_and_save(all_nodes, all_edges, config)

if __name__ == "__main__":
    run_full_pipeline()