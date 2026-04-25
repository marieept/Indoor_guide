import json
import math
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from skimage.morphology import skeletonize
from scipy import spatial
from tkinter import simpledialog
import tkinter as tk
import os
from pathlib import Path
import base64, io
from PIL import Image as PILImage

# Absolute path to the directory containing this file
GRAPH_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

def _extract_img_from_svg(svg_path, grayscale =True):
    """ Extracts the embedded base64 image from an SVG file and returns it as a numpy array"""

    #Parse the SVG file as XML
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Find <image> element with or without XML namespace
    img_el = None
    for child in root.iter():
        if child.tag.endswith("}image") or child.tag == "image":
            img_el = child
            break
    
    if img_el is None:
        print(f"[DEBUG] Contenu brut du SVG :")
        print(ET.tostring(root, encoding="unicode")[:500])
        raise RuntimeError(f"Aucun élément <image> trouvé dans {svg_path}")
    
    # Get the image data from the href attribute
    # xlink:href is the old SVG standard, href is the new one
    href = (img_el.get("href") 
            or img_el.get("{http://www.w3.org/1999/xlink}href", ""))
    
    # Decode base64 image data
    # The href looks like "data:image/png;base64,XXXX..." so we split on the comma
    b64_data = href.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_data)
    
    # Open the image bytes with PIL and convert to numpy array
    pil_img = PILImage.open(io.BytesIO(img_bytes))
    if grayscale:
        pil_img = pil_img.convert("L")
        return np.array(pil_img)
    else:
        #Convert RGB to BGR for OpenCV
        pil_img = pil_img.convert("RGB")
        arr = np.array(pil_img)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def configure():
    """ Loads the configuration from config.json and reads the dimension of each floor's SVG"""
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Read the width and height of each floor'SVG file
    for floor in config['etages']:
        tree = ET.parse(floor['svg'])
        root = tree.getroot()
        floor['width'] = int(float(root.attrib['width']))
        floor['height'] = int(float(root.attrib['height']))

    return config

def squelettize(floor):
    """ Loads the floor's SVG and applies skeletonization to extract the navigation skeleton"""

    img = _extract_img_from_svg(floor["svg"], grayscale=True)
 
    if img is None:
        print(f"Erreur : impossible de lire {floor['svg']}")
        exit()

    # Resize to 25% to speed up processinf and fit on screen
    img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)

    # Convert to color to be able to draw colored circles and lines later
    img_color = cv2.cvtColor(img_small.copy(), cv2.COLOR_GRAY2RGB)

    # Binary image with values 0 and 1 to check if a path is clear
    _, navigable = cv2.threshold(img_small, 127, 1, cv2.THRESH_BINARY)

    # Skeletonize the binary image
    skeleton = skeletonize(navigable.astype(bool)) # returns a boolean array (True/False)
    skel = skeleton.astype(np.uint8) # converted to int

    return img_small, img_color, navigable, skel

def fuse_nodes(nodes, min_dist=20):
    """ Fuses nodes that are too close to each other into a single node"""

    fused = []
    used  = set()
    for i, (x1, y1) in enumerate(nodes):
        if i in used:
            continue

        # Group all nodes close enough to the current one
        group = [(x1, y1)] # Start a group with the current node
        for j, (x2, y2) in enumerate(nodes):
            if j != i and j not in used:
                # Check if the other node is close enough
                if abs(x1-x2) < min_dist and abs(y1-y2) < min_dist:
                    group.append((x2, y2))
                    used.add(j) # Mark as used so it won't start its own group
        used.add(i) # Mark current node as used

        # Replace the group with a single node at the average position
        fused.append((int(np.mean([p[0] for p in group])),
                      int(np.mean([p[1] for p in group]))))
    return fused

def detect_nodes(skel, floor):
    """ Detects nodes from the skeleton image. A node is either an intersection or an endpoint"""
    first_nodes=[]
    for y in range(1, skel.shape[0] -1):
        for x in range(1, skel.shape[1] -1):
            if skel[y,x]==1: # white pixel = part of the skeleton
                # Sum all values in the 3x3 area (0 or 1) to count white neighbors
                neighboors = np.sum(skel[y-1:y+2, x-1:x+2]) -1 # -1 to exclude the pixel itself

                # Intersection (>=3 neighbors) or endpoint (1 neighbor)
                if neighboors >= 3 or neighboors==1 :
                    first_nodes.append((x,y))

    # Fuse nodes that are too close from each other
    nodes_coord= fuse_nodes(first_nodes)

    # Convert to node dictionaries with id, position scaled back to original size, and floor
    nodes = []
    for i, (x,y) in enumerate(nodes_coord):
        nodes.append({"id": f"{floor['prefix']}_n{i}",
                      "x": x*4, # x4 because the image was resized to 25%
                      "y": y*4,
                      "floor": floor["floor"]
                      })
    return nodes

def get_nearest_node(x,y,nodes):
    """ Returns the nearest node the given (x,y) position and its distance. 
    Coordinates are divided by 4 because the display image is at 25% of the original size"""
    min_d = float('inf')
    closest = None

    for n in nodes:
        d= math.sqrt((n['x']//4 - x)**2 + (n['y']//4 - y)**2)
        if d<= min_d:
            min_d=d
            closest= n
    return closest, min_d

def _load_display_img(floor):
    """ Loads the display SVG of the floor and resizes it to 25%"""

    img_display = _extract_img_from_svg(floor["svg_display"], grayscale=False)
    if img_display is None:
        print(f"Erreur : impossible de lire l'image display étage {floor['floor']}")
        exit()

    # Resize to 25% to match the size of the processed image
    return cv2.resize(img_display, (0, 0), fx=0.25, fy=0.25)

def edit_nodes(nodes, img_color, floor):
    """ Opens an interactive window to manually ad or remove navigation nodes"""
    img_nav = img_color.copy()
    all_nodes = nodes.copy()
    nb_nodes = [len(nodes)] # wrapped in a list to allow modification

    # Draw existinf nodes in blue
    for n in all_nodes:
        cv2.circle(img_nav, (n["x"]//4, n["y"]//4),4, (255,100,0),-1)

    # Callback function for mouse events
    def click(event, x,y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Add a new node at the clicked position
            node_id = f"{floor['prefix']}_n{nb_nodes[0]}"
            all_nodes.append({
                "id": node_id,
                "x": x*4,
                "y": y*4,
                "floor": floor['floor']
            })
            cv2.circle(img_nav, (x,y),6, (0,0,255), -1)
            nb_nodes[0]+= 1
            cv2.imshow(titre, img_nav)

        elif event == cv2.EVENT_RBUTTONDOWN:
            # Remove the nearest node if close enough
            closest, min_d = get_nearest_node(x, y, all_nodes)
            if closest is not None and min_d < 20:
                all_nodes.remove(closest)
                # Redraw all remaining nodes
                img_nav[:]=img_color[:]
                for n in all_nodes:
                    cv2.circle(img_nav, (n['x']//4, n['y']//4), 4, (255, 100,0), -1)
                cv2.imshow(titre, img_nav)

    titre = f"Etage {floor['floor']} - Noeuds _ G: Ajouter, D: Supprimer, Q : Terminer"
    cv2.namedWindow(titre, cv2.WINDOW_NORMAL)
    cv2.imshow(titre, img_nav)
    cv2.setMouseCallback(titre, click)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return all_nodes

def make_alias(nom, floor_number):
    """ Generates a simplified alias for a room name, used for search
    Example :
     "Toilettes F0 Femmes 1" -> "Toilettes femmes 0"
     "Salle 1.2 Porte 1" -> "Salle 1.2"
    """
    nom_lower = nom.lower()
    
    # Standardize toilet names by adding gender and floor number
    if "toilettes" in nom_lower or "wc" in nom_lower:
        genre = ""
        if "femmes" in nom_lower:
            genre = "femmes "
        elif "hommes" in nom_lower:
            genre = "hommes "
        elif "pmr" in nom_lower:
            genre = "PMR "
        return f"Toilettes {genre}{floor_number}"
    
    # Remove "Porte X" suffix from room names (e.g.: "Salle 1.3 Porte 1" -> "Salle 1.3")
    parts = nom.split()
    nom_lower_parts = nom_lower.split()
    if "porte" in nom_lower_parts:
        idx = nom_lower_parts.index("porte")
        return " ".join(parts[:idx])
    
    return nom

def put_rooms(floor):
    """ Opens an interactive window to manually place rooms on the floor plan"""
    img_display = _load_display_img(floor)
    img_rooms = img_display.copy()

    rooms= []
    rooms_count=[0] # wrapped in a list to allow modification

    # Callback for mouse events
    def click_rooms(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            #Open a tkinter dialog to ask the room name
            #tk.Tk() is created and destroyed each time to avoid conflict with OpenCV
            root = tk.Tk()
            root.withdraw()  # hide the main tkinter window
            nom = simpledialog.askstring("Salle", "Nom de la salle :")
            root.destroy()

            if nom :
                node_id = f"{floor['prefix']}_s{rooms_count[0]}"
                rooms.append({
                    "id": node_id,
                    "x": x * 4,
                    "y": y * 4,
                    "floor": floor['floor'],
                    "label": nom,  # full name, displayed in the interface
                    "alias": make_alias(nom, floor['floor']),  # simplified name, used for search
                    "type": "room"
                })
                cv2.circle(img_rooms, (x, y), 6, (0, 0, 255), -1)
                cv2.putText(img_rooms,nom, (x+8, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 5)
                rooms_count[0] += 1
                cv2.imshow(titre, img_rooms)

    titre = f"Etage {floor['floor']} - Salles _ G: Placer, Q : Terminer"
    cv2.namedWindow(titre, cv2.WINDOW_NORMAL)
    cv2.imshow(titre, img_rooms)
    cv2.setMouseCallback(titre, click_rooms)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return rooms

def put_transitions(floor):
    """ Opens an interactive window to manually place transitions (stairs, elevators)"""
    img_display = _load_display_img(floor)
    img_tran = img_display.copy()

    transitions= []

    # Callback for mouse events
    def click_tran(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:

            root = tk.Tk()
            root.withdraw()
            node_type = simpledialog.askstring("Transition", "Type (escalier/ascenseur) :")
            unique_id = simpledialog.askstring("Transition", "Identifiant unique (ex: escl_nord) :")
            root.destroy()

            if node_type :
                label = simpledialog.askstring("Transition", "Nom affiché (ex: Escalier Nord) :")

                node_id = f"{floor['prefix']}_t_{unique_id}"

                # Convert French type names to English
                if node_type == 'escalier':
                    node_type = 'stair'
                elif node_type == 'ascenseur':
                    node_type = 'elevator'
                transitions.append({
                    "id": node_id,
                    "x": x * 4,
                    "y": y * 4,
                    "floor": floor['floor'],
                    "type": node_type,
                    "transition_id": unique_id, #used to connect transitions between floors
                    "label": label if label else unique_id
                })
                cv2.circle(img_tran, (x, y), 6, (0, 0, 255), -1)
                cv2.putText(img_tran,unique_id, (x+8, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 1)
                cv2.imshow(titre, img_tran)

    titre = f"Etage {floor['floor']} - Transitions _ G: Placer, Q : Terminer"
    cv2.namedWindow(titre, cv2.WINDOW_NORMAL)
    cv2.imshow(titre, img_tran)
    cv2.setMouseCallback(titre, click_tran)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return transitions

def put_stairs_pmr(nodes, edges, floor):
    """ Opens an interactive window to manually mark stair steps that are not accessible to PMR.
    Click on two nodes to create a  "steps" edge between them"""

    img_display = _load_display_img(floor)
    img_pmr = img_display.copy()

    selection=[None] # wrapped in a list to allow modification

    # Draw all existing nodes in blue
    for n in nodes:
        cv2.circle(img_pmr, (n['x']//4, n['y']//4), 3, (255, 100, 0), -1)

    # Callback for mouse events
    def click_pmr(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            closest, min_d = get_nearest_node(x, y, nodes)

            if selection[0] is None:
                # First clic : select the first node
                selection[0] = closest
                cv2.circle(img_pmr, (closest['x'] // 4, closest['y'] // 4), 6, (0, 255, 255), -1)
            else:
                # Second click : create a "steps" edge between the two nodes
                n1 = selection[0]
                n2 = closest

                edges.append({
                    "from": n1['id'],
                    "to": n2['id'],
                    "weight": euclidian_distance(n1['x'], n1['y'], n2['x'], n2['y']),
                    "floor": floor['floor'],
                    "type": "steps" # this type is filtered out in PMR mode
                })
                cv2.circle(img_pmr, (n2['x']//4, n2['y']//4), 6, (0, 255, 255), -1)
                cv2.line(img_pmr, (n1['x']//4, n1['y']//4),(n2['x']//4, n2['y']//4), (0, 255, 255), 1)
                selection[0]=None # reset selection for the next pair
            cv2.imshow(titre, img_pmr)

    titre = f"Étage {floor['floor']} - Marches PMR | Clic gauche = sélectionner deux noeuds | Q = terminer"
    cv2.namedWindow(titre, cv2.WINDOW_NORMAL)
    cv2.imshow(titre, img_pmr)
    cv2.setMouseCallback(titre, click_pmr)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return edges

def euclidian_distance(x1,y1,x2,y2):
    """ Returns the Euclidean distance between two points"""
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def path_clear(nav_nodes, p1, p2):
    """ Checks if a straight line between two point is navigable (no walls)"""
    x1, y1 = p1
    x2, y2 = p2
    lenght = int(euclidian_distance(x1, y1, x2, y2))

    if lenght==0:
        return True

    for i in range(lenght+1):
        # t goes from 0 to 1, used to interpolate between p1 and p2
        t = i/lenght
        x= int(x1 + t* (x2-x1))
        y= int(y1 + t* (y2-y1))

        if 0<=y< nav_nodes.shape[0] and 0<=x< nav_nodes.shape[1] : # check bounds
            if nav_nodes[y,x]==0: # 0 = wall
                return False

    return True

def generate_edges(nodes, navigable, floor):
    """ Generates edges between nodes that are close enough and have a clear path between them"""
    
    # Build a list of coordinates at 25% scale for KDTree and path_clear
    coord_list =[]
    for n in nodes:
        coord_list.append((n['x'] // 4, n['y'] // 4))

    # KDTree allows efficient nearest neighbor search
    tree = spatial.KDTree(coord_list)
    edges=[]
    seen= set() # stores already porecessed pairs to avoid duplicate edges (A->B and B->A)

    for i, p in enumerate(coord_list):
        # Find all nodes within a radius of 300 pixels
        index = tree.query_ball_point(p, r=300)
        for j in index:
            # Always store the pair as (min, max) to detect duplicates regardless of direction
            if i!=j and (min(i,j), max(i,j)) not in seen :
               if path_clear(navigable, p, coord_list[j]):
                   seen.add((min(i,j), max(i,j)))
                   edges.append({
                       "from": nodes[i]['id'],
                       "to": nodes[j]['id'],
                       # Weight is computed at full scale (x4) to get real pixel distances
                       "weight": euclidian_distance(coord_list[i][0]*4,coord_list[i][1]*4, coord_list[j][0]*4,coord_list[j][1]*4),
                       "floor": floor['floor']
                   })

    return edges

def connect_nodes(nodes, rooms, transitions, edges, floor, navigable):
    """ Connects rooms and transitions to the nearest navigation node with a clear path"""

    for room in rooms:
        # Sort navigation nodes by distance to the room
        candidates = sorted(nodes, key=lambda n: euclidian_distance(
            room['x']//4, room['y']//4, n['x']//4, n['y']//4))
        
        # Try the 5 nearest nodes and connect to the first one with a clear path
        for closest in candidates[:5]:
            if path_clear(navigable, (room['x']//4, room['y']//4),
                                      (closest['x']//4, closest['y']//4)):
                edges.append({
                    "from": room['id'],
                    "to": closest['id'],
                    "weight": euclidian_distance(room['x'], room['y'],
                                                  closest['x'], closest['y']),
                    "floor": floor['floor']
                })
                break # stop after the first valid connection

    for transition in transitions:
        # Same logic for transitions
        candidates = sorted(nodes, key=lambda n: euclidian_distance(
            transition['x']//4, transition['y']//4, n['x']//4, n['y']//4))
        
        for closest in candidates[:5]:
            if path_clear(navigable, (transition['x']//4, transition['y']//4),
                                      (closest['x']//4, closest['y']//4)):
                edges.append({
                    "from": transition['id'],
                    "to": closest['id'],
                    "weight": euclidian_distance(transition['x'], transition['y'],
                                                  closest['x'], closest['y']),
                    "floor": floor['floor']
                })
                break

    return edges

def merge_and_save(all_nodes, all_edges, config):
    """ Connects transitions (stairs, elevators) between floors and saves the final graph to a JSON file"""
    
    # Extract all stair and elevator nodes froma ll floors
    transitions = []
    for n in all_nodes:
        # .get() is used because navigation nodes don't have a 'type' field
        if n.get('type') == 'stair' or n.get('type')== 'elevator':
            transitions.append(n)

    # Group transition by transition_id to find matching stairs/elevators
    groups={}
    for transition in transitions:
        transition_id = transition.get('transition_id')
        if transition_id not in groups:
            groups[transition_id]=[]
        groups[transition_id].append(transition)

    # Connect transitions of the same id between consecutive floors
    for transition_id, group in groups.items():
        group_sorted= sorted(group, key=lambda n: n['floor']) # sort by floor ascending
        for i in range(len(group_sorted) - 1): #iterate over consecutive pairs (0 et 1, 1 et 2 ...)
            n1 = group_sorted[i]
            n2 = group_sorted[i + 1]
            all_edges.append({
                "from": n1['id'],
                "to": n2['id'],
                "weight": 200, # fixed cost for changing floor
                "type": n1['type'],
                "inter_floor": True # flag used by the pathfinding to handle floor changes — not currently used by the frontend
            })

    # Save the final graph to a JSON file
    graph = {"nodes": all_nodes, "edges": all_edges}
   
    with open(config["output"], 'w') as f:
        json.dump(graph, f, indent=2)

# Entry point when running directly
# Processes each floor sequentially and saves the final graph to a JSON file
if __name__ == "__main__":
    os.chdir(GRAPH_DIR)
    config = configure()
    all_nodes = []
    all_edges= []

    for floor in config['etages']:
        img_small, img_color,navigable, skel = squelettize(floor)
        nodes = detect_nodes(skel, floor)
        nav_nodes = edit_nodes(nodes, img_color, floor)
        rooms = put_rooms(floor)
        transitions = put_transitions(floor)
        edges = generate_edges(nav_nodes, navigable, floor)
        edges = put_stairs_pmr(nav_nodes, edges, floor)
        edges = connect_nodes(nav_nodes, rooms, transitions, edges, floor, navigable)

        for n in nav_nodes + rooms + transitions:
            all_nodes.append(n)

        for e in edges:
            all_edges.append(e)

    merge_and_save(all_nodes, all_edges, config)