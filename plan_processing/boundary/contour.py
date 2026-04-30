
import cv2
import numpy as np
import matplotlib.pyplot as plt


def apply_boundary(image: np.ndarray):
    """
    Display an image and the user draw a polygon arround the building.
    Everything out of the polygon become black
    :param binary image (H, W)
    :return binary image with outdoor in black
    """

    points = [] # points click list (tuple)

    #creation matplotlib window
    fig, ax = plt.subplots()    #fig= window, ax= zone display image
    ax.imshow(image, cmap="gray")
    ax.set_title("Cliquez pour délimiter le bâtiment. Entrée pour valider, Z pour annuler le dernier point.")

    #prepare 2 graphics empty elements
    polygon_line = ax.plot([], [], "r-")[0]   #line connect dots
    dots = ax.plot([], [], "ro", markersize=4)[0] #dots

    #connect events to functions
    fig.canvas.mpl_connect("button_press_event",lambda event: on_click(event, ax, points, polygon_line, dots, fig))
    fig.canvas.mpl_connect("key_press_event", lambda event: on_key(event, points, polygon_line, dots, fig))

    plt.tight_layout()
    plt.show()

    #when the window is closed, applied the mask and return the result
    return apply_mask(image, points)

def update_drawing(points, polygon_line, dots, fig):
    """
    actualise the update of polygon and points after every click
    """
    if len(points) < 2:
        #if less 2 doors, impossible to draw a line
        polygon_line.set_data([],[])
    else:
        #list dots position, all points --> comeback to the fist dot
        # and close the polygon by drawing a line
        xs = []
        ys =[]
        for p in points:
            xs.append(p[0])
            ys.append(p[1])
        xs.append(points[0][0])
        ys.append(points[0][1])
        polygon_line.set_data(xs, ys)

    #list and display dots
    xs_dots =[]
    ys_dots=[]
    for p in points:
        xs_dots.append(p[0])
        ys_dots.append(p[1])
    dots.set_data(xs_dots, ys_dots)
    fig.canvas.draw()

def on_click(event, ax, points, polygon_line, dots, fig):

    #if not in image zone, ignore
    if event.inaxes != ax:
        return
    #add point to the list
    points.append((int(event.xdata), int(event.ydata)))
    #actualise the new polygone
    update_drawing(points, polygon_line, dots, fig)

def on_key(event, points, polygon_line, dots, fig):
    if event.key == "enter" and len(points) >= 3:
        plt.close()
    elif event.key == "z" and len(points) > 0:
        points.pop()
        update_drawing(points, polygon_line, dots, fig)

def apply_mask(image: np.ndarray, points: list):
    """
    create a mask from the polygon on the image
    indoor stay as before
    outdoor become white like a wall
    """
    #create a black image (zero) same size
    mask = np.zeros_like(image)

    #conversion points list to array numpy of int 32bits because this function need 32 bits
    pts = np.array(points, dtype=np.int32)
    #polygone inside is white
    cv2.fillPoly(mask, [pts], 255)

    #keep only the pixels of the image that are also white in the mask
    #the outside becoming black
    result = cv2.bitwise_and(image, mask)

    # exterior is white now
    exterior = cv2.bitwise_not(mask)
    #merge
    result = cv2.bitwise_or(result, exterior)

    return result