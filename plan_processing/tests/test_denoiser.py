# tests/test_denoiser.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from pipeline.loader import load_plan
from pipeline.denoiser import preprocess

image = load_plan("data/plans/PL_03_Plan_niveau2_murs.svg")
gray = preprocess(image)

print(f"Shape : {gray.shape}")
print(f"Dtype : {gray.dtype}")

fig, axes = plt.subplots(1, 2)
axes[0].imshow(image)
axes[0].set_title("Original RGB")
axes[0].axis("off")

axes[1].imshow(gray, cmap="gray")
axes[1].set_title("Prétraitement (gris + blur)")
axes[1].axis("off")

plt.tight_layout()
plt.show()