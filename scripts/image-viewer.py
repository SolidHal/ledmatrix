#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix
from PIL import Image
import config
import display


def image_viewer(image_file):

    image = Image.open(image_file)

    matrix = config.Matrix()

    try:
        print("Press CTRL-C to stop.")
        display.static(matrix, image)
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    image_viewer(image_file)
