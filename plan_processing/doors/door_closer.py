import cv2
import numpy as np
import matplotlib.pyplot as plt


def close_doors(image: np.ndarray) -> np.ndarray:
    """
    Affiche l'image et laisse l'utilisateur tracer des segments
    pour fermer les ouvertures de portes.

    Chaque segment est tracé en noir (épaisseur adaptable).
    Clic gauche : pose un point. Au 2ème clic, le segment est tracé.
    Z : annule le dernier segment. Entrée : valide et ferme.

    Paramètres
    ----------
    image : np.ndarray
        Image binaire (H, W), dtype uint8, valeurs 0 ou 255

    Retourne
    --------
    np.ndarray
        Image binaire avec les portes fermées (H, W), dtype uint8
    """

    result = image.copy()
    segments = []
    current_point = []

    fig, ax = plt.subplots()
    ax.imshow(result, cmap="gray")
    ax.set_title("Cliquez 2 points pour fermer une porte. Z pour annuler. Entrée pour valider.")

    drawn_lines = []
    preview_line, = ax.plot([], [], "b--", linewidth=1)

    def _redraw():
        for line in drawn_lines:
            line.remove()
        drawn_lines.clear()

        for seg in segments:
            p1, p2 = seg
            line, = ax.plot([p1[0], p2[0]], [p1[1], p2[1]], "r-", linewidth=2)
            drawn_lines.append(line)

        fig.canvas.draw()

    def _on_click(event):
        if event.inaxes != ax:
            return

        pt = (int(event.xdata), int(event.ydata))

        if len(current_point) == 0:
            current_point.append(pt)
            preview_line.set_data([pt[0]], [pt[1]])
            fig.canvas.draw()

        else:
            p1 = current_point.pop()
            p2 = pt
            segments.append((p1, p2))
            preview_line.set_data([], [])
            _redraw()

    def _on_key(event):
        if event.key == "enter":
            plt.close()

        elif event.key == "z":
            if current_point:
                current_point.clear()
                preview_line.set_data([], [])
                fig.canvas.draw()
            elif segments:
                segments.pop()
                _redraw()

    fig.canvas.mpl_connect("button_press_event", _on_click)
    fig.canvas.mpl_connect("key_press_event", _on_key)

    plt.tight_layout()
    plt.show()

    return _draw_segments(result, segments)


def _draw_segments(image: np.ndarray, segments: list) -> np.ndarray:
    """
    Dessine les segments en noir sur l'image binaire.

    Paramètres
    ----------
    image : np.ndarray
        Image binaire (H, W)
    segments : list
        Liste de tuples ((x1, y1), (x2, y2))

    Retourne
    --------
    np.ndarray
        Image binaire avec les segments tracés en noir
    """

    result = image.copy()

    for p1, p2 in segments:
        cv2.line(result, p1, p2, color=0, thickness=2)

    return result