# tests/test_binarizer.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from pipeline.loader import load_plan
from pipeline.denoiser import preprocess
from pipeline.binarizer import binarize

image = load_plan("data/plans/PL_03_Plan_niveau2_murs.svg")
gray = preprocess(image)

binary_otsu     = binarize(gray, method="otsu")
binary_adaptive = binarize(gray, method="adaptive")

fig, axes = plt.subplots(1, 3)

axes[0].imshow(gray, cmap="gray")
axes[0].set_title("Prétraitement")
axes[0].axis("off")

axes[1].imshow(binary_otsu, cmap="gray")
axes[1].set_title("Otsu")
axes[1].axis("off")

axes[2].imshow(binary_adaptive, cmap="gray")
axes[2].set_title("Adaptive")
axes[2].axis("off")

plt.tight_layout()
plt.show()