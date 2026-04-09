import json
import qrcode
import os

# === CONFIG ===
os.chdir(os.path.dirname(os.path.abspath(__file__))) # Se placer dans le dossier où est le script
BASE_URL = "https://marieept.github.io/Indoor_guide/index.html"  # URL de base pour les QR codes
JSON_FILE = "graph_.json"               # Fichier JSON contenant les nodes
OUTPUT_DIR = "qr_codes"                # Dossier où seront sauvegardés les QR codes

# Créer le dossier de sortie si il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === CHARGEMENT DU JSON ===
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data.get("nodes", [])

# === FILTRER LES NODES PERTINENTS ===
valid_types = ["room", "stair", "elevator"]

for node in nodes:
    if node.get("type") in valid_types:
        node_id = node["id"]
        label = node.get("label", node_id)
        
        # URL directe avec l'ID exact du node
        url = f"{BASE_URL}?start={node_id}"
        
        # Nom du fichier QR code = ID du node
        filename = os.path.join(OUTPUT_DIR, f"{label}.png")
        
        # Générer et sauvegarder le QR code
        img = qrcode.make(url)
        img.save(filename)
        
        print(f"QR Code créé : {label}")

print("Tous les QR codes ont été générés avec les bons IDs.")