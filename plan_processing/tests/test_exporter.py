# tests/test_exporter.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.loader import load_plan
from pipeline.denoiser import preprocess
from pipeline.binarizer import binarize
from pipeline.morphology import clean
from boundary.contour import apply_boundary
from doors.door_closer import close_doors
from calibration.scale import resize_to_target
from output.svg_exporter import export

file_path = Path("data/plans/PL_03_Plan_niveau2_murs.svg")

image = load_plan(file_path)
gray = preprocess(image)
binary = binarize(gray)
cleaned = clean(binary)
bounded = apply_boundary(cleaned)
closed = close_doors(bounded)
scaled = resize_to_target(closed)



path_processed, path_display = export(scaled, file_path, "plan_test")

print(f"SVG traité    : {path_processed}")
print(f"SVG affichage : {path_display}")

print(f"Traité existe    : {path_processed.exists()}")
print(f"Affichage existe : {path_display.exists()}")