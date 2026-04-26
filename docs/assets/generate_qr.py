#Generates a QR code for each room, stair and elevator in the graph

import json
import qrcode
import os

# Absolute path to the directory containing this file
os.chdir(os.path.dirname(os.path.abspath(__file__))) # Se placer dans le dossier où est le script

BASE_URL = "https://marieept.github.io/Indoor_guide/index.html" # base URL for QR codes
JSON_FILE = "graph.json" # graph file containing the nodes
OUTPUT_DIR = "qr_codes" # output directory for the QR codes

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the graph
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data.get("nodes", [])

# Generate a QR code for each room, stair and elevator
valid_types = ["room", "stair", "elevator"]

for node in nodes:
    if node.get("type") in valid_types:
        node_id = node["id"]
        label = node.get("label", node_id)
        
        # Build the URL with the node id as the start parameter
        url = f"{BASE_URL}?start={node_id}"
        
        # Save the QR code as a PNG file
        filename = os.path.join(OUTPUT_DIR, f"{label}.png")
        img = qrcode.make(url)
        img.save(filename)
        
        print(f"QR Code créé : {label}")