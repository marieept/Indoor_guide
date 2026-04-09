# tests/test_morphology.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from pipeline.loader import load_plan
from pipeline.denoiser import preprocess
from pipeline.binarizer import binarize
from pipeline.morphology import clean

image = load_plan("data/plans/PL_03_Plan_niveau2_murs.svg")
gray = preprocess(image)
binary = binarize(gray)
cleaned = clean(binary)

fig, axes = plt.subplots(1, 2)

axes[0].imshow(binary, cmap="gray")
axes[0].set_title("Avant morphologie")
axes[0].axis("off")

axes[1].imshow(cleaned, cmap="gray")
axes[1].set_title("Après morphologie")
axes[1].axis("off")

plt.tight_layout()
plt.show()