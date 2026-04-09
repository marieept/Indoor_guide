# tests/test_scale.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from pipeline.loader import load_plan
from pipeline.denoiser import preprocess
from pipeline.binarizer import binarize
from pipeline.morphology import clean
from boundary.contour import apply_boundary
from doors.door_closer import close_doors
from calibration.scale import resize_to_target

image = load_plan("data/plans/PL_03_Plan_niveau2_murs.svg")
gray = preprocess(image)
binary = binarize(gray)
#cleaned = clean(binary)
bounded = apply_boundary(binary)
closed = close_doors(bounded)
scaled = resize_to_target(closed)

print(f"Shape avant : {closed.shape}")
print(f"Shape après : {scaled.shape}")

fig, axes = plt.subplots(1, 2)

axes[0].imshow(closed, cmap="gray")
axes[0].set_title(f"Avant ({closed.shape[1]}x{closed.shape[0]})")
axes[0].axis("off")

axes[1].imshow(scaled, cmap="gray")
axes[1].set_title(f"Après ({scaled.shape[1]}x{scaled.shape[0]})")
axes[1].axis("off")

plt.tight_layout()
plt.show()