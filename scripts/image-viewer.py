#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix
from PIL import Image
from libledmatrix import display, image_color, image_processing
from libledmatrix import config


def image_viewer(image_file):

    pil_image = Image.open(image_file)
    cfg = config.Config()
    image = image_processing.centerfit_image(pil_image, cfg.matrix, False)[0]
    pil_image.close()


    try:
        print("Press CTRL-C to stop.")
        display.static(cfg, image)
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
