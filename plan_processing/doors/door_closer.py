import cv2
import numpy as np
import matplotlib.pyplot as plt


def close_doors(image: np.ndarray):
    """
    Displays the image and draws segments
    to close door openings.
    Each segment is drawn in black.
    Left click: places a point. On the second click, the segment is drawn.
    Z: cancels the last segment. Enter: confirms and closes.
    """

    result = image.copy()
    segments = []
    current_point = []

    fig, ax = plt.subplots()
    ax.imshow(result, cmap="gray")
    ax.set_title("Cliquez 2 points pour fermer une porte. Z pour annuler. Entrée pour valider.")

    drawn_lines = []

    fig.canvas.mpl_connect("button_press_event", lambda event: on_click(event, ax,current_point,segments,drawn_lines,fig))
    fig.canvas.mpl_connect("key_press_event", lambda event: on_key(event, current_point, segments, drawn_lines, ax,fig))

    plt.tight_layout()
    plt.show()

    return draw_segments(result, segments)

def redraw(segments, drawn_lines, ax, fig):
    for line in drawn_lines:
        line.remove()
    drawn_lines.clear()

    #redraw every line check
    for seg in segments:
        p1, p2 = seg
        line, = ax.plot([p1[0], p2[0]], [p1[1], p2[1]], "r-", linewidth=2) #draw between p1 et p2
        drawn_lines.append(line)

    fig.canvas.draw()

def on_click(event, ax, current_point, segments, drawn_lines, fig):
    if event.inaxes != ax:
        return

    pt = (int(event.xdata), int(event.ydata))

    if len(current_point) == 0:
        current_point.append(pt)
        fig.canvas.draw()

    else:
        p1 = current_point.pop()
        p2 = pt
        segments.append((p1, p2))
        redraw(segments, drawn_lines, ax, fig)

def on_key(event, current_point, segments, drawn_lines, ax, fig):
    if event.key == "enter":
        plt.close()

    elif event.key == "z":
        if current_point:
            current_point.clear()
            fig.canvas.draw()
        elif segments:
            segments.pop()
            redraw(segments, drawn_lines, ax, fig)

def draw_segments(image: np.ndarray, segments: list):
    """
    draw line in black
    """

    result = image.copy()

    for p1, p2 in segments:
        cv2.line(result, p1, p2, color=255, thickness=8)

    return result