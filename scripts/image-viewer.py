#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import config


def image_viewer(image_file):

    image = Image.open(image_file)

    matrix = config.Matrix()
    # image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)
    image = image.convert("RGB")
    # image = crop_and_pad(image)

    matrix.SetImage(image)

    try:
        print("Press CTRL-C to stop.")
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
