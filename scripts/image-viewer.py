#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image


def image_viewer(image_file):

    image = Image.open(image_file)

    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 64  #TODO change this to 128 when all 4 are hooked up
    options.cols = 128
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'

    matrix = RGBMatrix(options = options)

    # Make image fit our screen.
    image.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)

    matrix.SetImage(image.convert('RGB'))

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
