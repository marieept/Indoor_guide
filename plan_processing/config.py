
# Paramètres globaux du pipeline
# Modifie ici pour ajuster le comportement sans toucher au code
# -------------------------------------------------------------

#class in python, use for file path
from pathlib import Path
# used for interaction with th os
import os

# Path
# ----------------------
BASE_DIR    = Path(__file__).parent #represent the root of the project
DATA_DIR    = BASE_DIR / "data" / "plans"   #file in
OUTPUT_DIR  = BASE_DIR / "output/final" #file out

# Poppler — require by pdf2image (PDF et SVG)
#POPPLER_PATH = r"C:\Users\boris\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

#we try to read the environnement variable and if not we take the hard path
POPPLER_PATH = os.environ.get(
    "POPPLER_PATH",
    r"C:\Users\marie\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
)
#  if poppler doesn't exist there is error
if not os.path.isdir(POPPLER_PATH):
    raise EnvironmentError(
        "\nPOPPLER_PATH n'est pas défini. Exemple sous Windows :\n"
        '    $env:POPPLER_PATH = "C:\\chemin\\vers\\poppler\\Library\\bin"'
    )



# SVG size output
# fix size of svg plan
SVG_WIDTH =1200
SVG_HEIGHT =900

# Binarized

# threshold value between 0 and 255
#every pixel over the value become white, and under the value become black
BINARIZE_THRESHOLD=128

# Morphology

# size of kernel  closing/opening
MORPH_KERNEL_SIZE = 3   # odd value

# Number repetition
MORPH_ITERATIONS=2  #more repetition equal to less noise


