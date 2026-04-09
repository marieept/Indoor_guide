import cv2
import numpy as np
import matplotlib.pyplot as plt


def apply_boundary(image: np.ndarray) -> np.ndarray:
    """
    Affiche l'image et laisse l'utilisateur dessiner un polygone
    autour du bâtiment. Tout ce qui est à l'extérieur du polygone
    devient noir.

    Paramètres
    ----------
    image : np.ndarray
        Image binaire (H, W), dtype uint8, valeurs 0 ou 255

    Retourne
    --------
    np.ndarray
        Image binaire avec l'extérieur masqué en noir (H, W), dtype uint8
    """

    points = []

    fig, ax = plt.subplots()
    ax.imshow(image, cmap="gray")
    ax.set_title("Cliquez pour délimiter le bâtiment. Entrée pour valider, Z pour annuler le dernier point.")

    polygon_line, = ax.plot([], [], "r-")
    dots, = ax.plot([], [], "ro", markersize=4)

    def _update_drawing():
        if len(points) < 2:
            polygon_line.set_data([], [])
        else:
            xs = [p[0] for p in points] + [points[0][0]]
            ys = [p[1] for p in points] + [points[0][1]]
            polygon_line.set_data(xs, ys)

        dots.set_data([p[0] for p in points], [p[1] for p in points])
        fig.canvas.draw()

    def _on_click(event):
        if event.inaxes != ax:
            return
        points.append((int(event.xdata), int(event.ydata)))
        _update_drawing()

    def _on_key(event):
        if event.key == "enter" and len(points) >= 3:
            plt.close()
        elif event.key == "z" and len(points) > 0:
            points.pop()
            _update_drawing()

    fig.canvas.mpl_connect("button_press_event", _on_click)
    fig.canvas.mpl_connect("key_press_event", _on_key)

    plt.tight_layout()
    plt.show()

    return _apply_mask(image, points)


def _apply_mask(image: np.ndarray, points: list) -> np.ndarray:
    """
    Crée un masque à partir du polygone et l'applique sur l'image.

    Paramètres
    ----------
    image : np.ndarray
        Image binaire (H, W)
    points : list
        Liste de tuples (x, y) définissant le polygone

    Retourne
    --------
    np.ndarray
        Image binaire avec l'extérieur du polygone mis à noir
    """

    mask = np.zeros_like(image)

    pts = np.array(points, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)

    result = cv2.bitwise_and(image, mask)

    return result