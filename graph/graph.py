import json
import math
import xml.etree.ElementTree as ET
import cv2
from wand.image import Image
import numpy as np
from skimage.morphology import skeletonize
from scipy import spatial
from tkinter import simpledialog, messagebox
import tkinter as tk
import os
from pathlib import Path

GRAPH_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMP_PNG = str(GRAPH_DIR / "temp.png")

import base64, io
from PIL import Image as PILImage

def _extract_img_from_svg(svg_path: str, grayscale: bool = True) -> np.ndarray:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Chercher <image> avec ou sans namespace
    img_el = None
    for child in root.iter():
        if child.tag.endswith("}image") or child.tag == "image":
            img_el = child
            break
    
    if img_el is None:
        print(f"[DEBUG] Contenu brut du SVG :")
        print(ET.tostring(root, encoding="unicode")[:500])
        raise RuntimeError(f"Aucun élément <image> trouvé dans {svg_path}")
    
    href = (img_el.get("href") 
            or img_el.get("{http://www.w3.org/1999/xlink}href", ""))
    
    b64_data = href.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_data)
    
    pil_img = PILImage.open(io.BytesIO(img_bytes))
    if grayscale:
        pil_img = pil_img.convert("L")
        return np.array(pil_img)
    else:
        pil_img = pil_img.convert("RGB")
        arr = np.array(pil_img)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def configure():
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Lire les dimensions depuis chaque SVG
    for floor in config['etages']:
        tree = ET.parse(floor['svg'])
        root = tree.getroot()
        floor['width'] = int(float(root.attrib['width']))
        floor['height'] = int(float(root.attrib['height']))

    return config

def squelettize(floor):
    """
    with Image(filename=floor["svg"]) as wimg:
        wimg.resize(floor["width"], floor["height"])
        wimg.format="png"
        wimg.save(filename=TEMP_PNG)
        img = cv2.imread(TEMP_PNG, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print(f"Erreur : impossible de lire {floor['svg']}")
        exit()
    """

    """svg_path = floor["svg"]
    png_fallback = str(Path(svg_path).with_suffix(".png"))
 
    if os.path.exists(png_fallback):
        img = cv2.imread(png_fallback, cv2.IMREAD_GRAYSCALE)
    else:
        with Image(filename=svg_path) as wimg:
            wimg.resize(floor["width"], floor["height"])
            wimg.format = "png"
            wimg.save(filename=TEMP_PNG)
        img = cv2.imread(TEMP_PNG, cv2.IMREAD_GRAYSCALE)"""
    
    img = _extract_img_from_svg(floor["svg"], grayscale=True)
 
    if img is None:
        print(f"Erreur : impossible de lire {floor['svg']}")
        exit()

    #On réduit la taille de l'image pour être plus rapide et rentrer sur l'écran
    img_small = cv2.resize(img, (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)

    #Pour tracer les cercles en couleur après, l'image doit être en couleur
    img_color = cv2.cvtColor(img_small.copy(), cv2.COLOR_GRAY2RGB)

    #Version binaire avec des valeurs 0 et 1 pour vérifier si un chemin est libre
    _, navigable = cv2.threshold(img_small, 127, 1, cv2.THRESH_BINARY)

    """#Version binaire avec des valeurs 0 et 255 pour l'érosion
    _, binary = cv2.threshold(img_small, 127, 255, cv2.THRESH_BINARY)

    #Pour s'éloigner des murs
    kernel = np.ones((5,5), np.uint8)
    binary_eroded= cv2.erode(binary, kernel, iterations=5)"""

    skeleton = skeletonize(navigable.astype(bool)) #retourne un tableau de booléens (True/False)
    skel = skeleton.astype(np.uint8) #conversion en entiers

    return img_small, img_color, navigable, skel

def fuse_nodes(nodes, min_dist=20):
    fused = []
    used  = set()
    for i, (x1, y1) in enumerate(nodes):
        if i in used:
            continue
        group = [(x1, y1)]
        for j, (x2, y2) in enumerate(nodes):
            if j != i and j not in used:
                if abs(x1-x2) < min_dist and abs(y1-y2) < min_dist:
                    group.append((x2, y2))
                    used.add(j)
        used.add(i)
        fused.append((int(np.mean([p[0] for p in group])),
                      int(np.mean([p[1] for p in group]))))
    return fused

def detect_nodes(skel, floor):
    first_nodes=[]
    for y in range(1, skel.shape[0] -1):
        for x in range(1, skel.shape[1] -1):
            if skel[y,x]==1: #si un pixel est blanc
                neighboors = np.sum(skel[y-1:y+2, x-1:x+2]) -1

                if neighboors >= 3 or neighboors==1 :
                #c'est une intersection ou une extrémité
                    first_nodes.append((x,y))

    nodes_coord= fuse_nodes(first_nodes)
    nodes = []
    for i, (x,y) in enumerate(nodes_coord):
        nodes.append({"id": f"{floor['prefix']}_n{i}",
                      "x": x*4,
                      "y": y*4,
                      "floor": floor["floor"]
                      })
    return nodes

def get_nearest_node(x,y,nodes):
    min_d = float('inf')
    closest = None

    for n in nodes:
        d= math.sqrt((n['x']//4 - x)**2 + (n['y']//4 - y)**2)
        if d<= min_d:
            min_d=d
            closest= n
    return closest, min_d

def _load_display_img(floor):
    img_display = _extract_img_from_svg(floor["svg_display"], grayscale=False)
    if img_display is None:
        print(f"Erreur : impossible de lire l'image display étage {floor['floor']}")
        exit()
    return cv2.resize(img_display, (0, 0), fx=0.25, fy=0.25)

def edit_nodes(nodes, img_color, floor):
    img_nav = img_color.copy()
    all_nodes = nodes.copy()
    nb_nodes = [len(nodes)]

    for n in all_nodes:
        cv2.circle(img_nav, (n["x"]//4, n["y"]//4),4, (255,100,0),-1)

    def click(event, x,y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
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
            closest, min_d = get_nearest_node(x, y, all_nodes)
            if closest is not None and min_d < 20:
                all_nodes.remove(closest)
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
    nom_lower = nom.lower()
    
    # Toilettes standardisées
    if "toilettes" in nom_lower or "wc" in nom_lower:
        if "femmes" in nom_lower or "f" in nom_lower:
            return f"Toilettes femmes {floor_number}"
        elif "hommes" in nom_lower or "h" in nom_lower:
            return f"Toilettes hommes {floor_number}"
        elif "pmr" in nom_lower:
            return f"Toilettes PMR {floor_number}"
        else:
            return f"Toilettes {floor_number}"

    # Simplifier les autres salles (ex: "Salle 1.3 porte 1" -> "Salle 1.3")
    parts = nom.split(" ")
    if "porte" in parts:
        idx = parts.index("porte")
        return " ".join(parts[:idx])
    else:
        return nom

def put_rooms(floor):
    img_display = _load_display_img(floor)
    img_rooms = img_display.copy()

    rooms= []
    rooms_count=[0]

    def click_rooms(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:

            root = tk.Tk()
            root.withdraw()  # cache la fenêtre tkinter principale
            nom = simpledialog.askstring("Salle", "Nom de la salle :")
            root.destroy()

            if nom :
                node_id = f"{floor['prefix']}_s{rooms_count[0]}"
                rooms.append({
                    "id": node_id,
                    "x": x * 4,
                    "y": y * 4,
                    "floor": floor['floor'],
                    "label": nom,  # affichage complet
                    "alias": make_alias(nom, floor['floor']),  # utilisé uniquement pour la recherche
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
    img_display = _load_display_img(floor)
    img_tran = img_display.copy()

    transitions= []

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
                    "transition_id": unique_id,
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
    img_display = _load_display_img(floor)
    img_pmr = img_display.copy()

    selection=[None]

    for n in nodes:
        cv2.circle(img_pmr, (n['x']//4, n['y']//4), 3, (255, 100, 0), -1)

    def click_pmr(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            closest, min_d = get_nearest_node(x, y, nodes)

            if selection[0] is None:
                #Premier clic
                selection[0] = closest
                cv2.circle(img_pmr, (closest['x'] // 4, closest['y'] // 4), 6, (0, 255, 255), -1)
            else:
                #Deuxième clic : on crée l'année
                n1 = selection[0]
                n2 = closest

                edges.append({
                    "from": n1['id'],
                    "to": n2['id'],
                    "weight": euclidian_distance(n1['x'], n1['y'], n2['x'], n2['y']),
                    "floor": floor['floor'],
                    "type": "steps"
                })
                cv2.circle(img_pmr, (n2['x']//4, n2['y']//4), 6, (0, 255, 255), -1)
                cv2.line(img_pmr, (n1['x']//4, n1['y']//4),(n2['x']//4, n2['y']//4), (0, 255, 255), 1)
                selection[0]=None
            cv2.imshow(titre, img_pmr)

    titre = f"Étage {floor['floor']} - Marches PMR | Clic gauche = sélectionner deux noeuds | Q = terminer"
    cv2.namedWindow(titre, cv2.WINDOW_NORMAL)
    cv2.imshow(titre, img_pmr)
    cv2.setMouseCallback(titre, click_pmr)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return edges

def euclidian_distance(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def path_clear(nav_nodes, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    lenght = int(euclidian_distance(x1, y1, x2, y2))

    if lenght==0:
        return True

    for i in range(lenght+1):
        t = i/lenght #0<t<1
        x= int(x1 + t* (x2-x1))
        y= int(y1 + t* (y2-y1))

        if 0<=y< nav_nodes.shape[0] and 0<=x< nav_nodes.shape[1] : #bien dans le bâtiment
            if nav_nodes[y,x]==0:
                return False

    return True

def generate_edges(nodes, navigable, floor):
    coord_list =[]
    for n in nodes:
        coord_list.append((n['x'] // 4, n['y'] // 4))

    tree = spatial.KDTree(coord_list)
    edges=[]
    seen= set() #liste sans doublon

    for i, p in enumerate(coord_list):
        index = tree.query_ball_point(p, r=700) #retourn les positions dans coord_list des points qui sont dans le rayon
        for j in index:
            if i!=j and (min(i,j), max(i,j)) not in seen : #force le plus petit index en premier pour repérer A->B et B->A
               if path_clear(navigable, p, coord_list[j]):
                   seen.add((min(i,j), max(i,j)))
                   edges.append({
                       "from": nodes[i]['id'],
                       "to": nodes[j]['id'],
                       "weight": euclidian_distance(coord_list[i][0]*4,coord_list[i][1]*4, coord_list[j][0]*4,coord_list[j][1]*4),
                       "floor": floor['floor']
                   })

    return edges

def connect_nodes(nodes, rooms, transitions, edges, floor):
    for room in rooms:
        closest, min_d = get_nearest_node(room['x']//4, room['y']//4,nodes)
        if closest:
            edges.append({
                "from": room['id'],
                "to": closest['id'],
                "weight": euclidian_distance(room['x'], room['y'], closest['x'], closest['y']),
                "floor": floor['floor']
            })

    for transition in transitions:
        closest, min_d = get_nearest_node(transition['x']//4, transition['y']//4,nodes)
        if closest:
            edges.append({
                "from": transition['id'],
                "to": closest['id'],
                "weight": euclidian_distance(transition['x'], transition['y'], closest['x'], closest['y']),
                "floor": floor['floor']
            })
    return edges

def merge_and_save(all_nodes, all_edges, config):
    #Grouper les transitions par transition_id
    transitions = []
    for n in all_nodes:
        if n.get('type') == 'stair' or n.get('type')== 'elevator': #get car les noeuds de navigation n'ont pas de type
            transitions.append(n)
    groups={}
    for transition in transitions:
        transition_id = transition.get('transition_id')
        if transition_id not in groups:
            groups[transition_id]=[]
        groups[transition_id].append(transition)

    #Relier les transitions du même id
    for transition_id, group in groups.items():
        group_sorted= sorted(group, key=lambda n: n['floor']) #trie les noeuds par étage croissant
        for i in range(len(group_sorted) - 1): #parcourt les paires consécutives (0 et 1, 1 et 2 ...)
            n1 = group_sorted[i]
            n2 = group_sorted[i + 1]
            all_edges.append({
                "from": n1['id'],
                "to": n2['id'],
                "weight": 200,
                "type": n1['type'],
                "inter_floor": True
            })

    #Sauvegarde
    graph = {"nodes": all_nodes, "edges": all_edges}
   
    with open(config["output"], 'w') as f:
        json.dump(graph, f, indent=2)

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
        edges = connect_nodes(nav_nodes, rooms, transitions, edges, floor)

        for n in nav_nodes + rooms + transitions:
            all_nodes.append(n)

        for e in edges:
            all_edges.append(e)

    merge_and_save(all_nodes, all_edges, config)