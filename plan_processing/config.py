# ─────────────────────────────────────────────
# Paramètres globaux du pipeline
# Modifie ici pour ajuster le comportement sans toucher au code
# ─────────────────────────────────────────────

from pathlib import Path
import os

# ─── Chemins ───────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data" / "plans"
OUTPUT_DIR  = BASE_DIR / "output/final"

# Poppler — requis par pdf2image (PDF et SVG)
#POPPLER_PATH = r"C:\Users\boris\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
POPPLER_PATH = os.environ.get(
    "POPPLER_PATH",
    r"C:\Users\marie\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
)

if not os.path.isdir(POPPLER_PATH):
    raise EnvironmentError(
        "\nPOPPLER_PATH n'est pas défini. Exemple sous Windows :\n"
        '    $env:POPPLER_PATH = "C:\\chemin\\vers\\poppler\\Library\\bin"'
    )



# ─── Taille de sortie SVG ──────────────────────────────────────────────────────

# Taille fixe des 2 SVG livrés à Marie
# Le plan est redimensionné en conservant les proportions (letterbox)
SVG_WIDTH  = 1200  # px
SVG_HEIGHT = 900   # px

# ─── Binarisation ─────────────────────────────────────────────────────────────

# Seuil pour le seuillage global (0-255)
# Si le plan est en niveaux de gris, tout pixel > BINARIZE_THRESHOLD → blanc
BINARIZE_THRESHOLD = 128

# ─── Morphologie ──────────────────────────────────────────────────────────────

# Taille du kernel pour l'érosion/dilatation (nettoyage des contours)
MORPH_KERNEL_SIZE = 3  # px, toujours impair

# Nombre d'itérations pour la fermeture morphologique
MORPH_ITERATIONS = 2


#IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI"

#os.environ["MAGICK_HOME"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI"
