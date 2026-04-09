# tests/test_loader.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from pipeline.loader import load_plan

image = load_plan("data/plans/PL_03_Plan_niveau2_murs.svg")

print(f"Type    : {type(image)}")
print(f"Shape   : {image.shape}")
print(f"Dtype   : {image.dtype}")
print(f"Min/Max : {image.min()} / {image.max()}")

plt.imshow(image)
plt.title("Loader — image RGB")
plt.axis("off")
plt.show()