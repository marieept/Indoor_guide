"""
Boris MOCK
boris.mock@isen-ouest.yncrea.fr
-------------------------------

"""
import sys
from pathlib import Path

from pipeline.process_plan import process


def main():
    if len(sys.argv) < 2:
        print("Usage : python main.py <chemin_du_plan>")
        print("Exemple : python main.py data/plans/batiment_A.png")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Erreur : fichier introuvable : {file_path}")
        sys.exit(1)

    process(file_path)


if __name__ == "__main__":
    main()