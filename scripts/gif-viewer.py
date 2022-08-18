#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, GifImagePlugin
from libledmatrix import display, image_color, image_processing
from libledmatrix import config

def gif_viewer(image_file):
    gif = Image.open(image_file)
    cfg = config.Config()
    # pre process our frames so we can dedicate our resources to displaying them later
    fill_matrix = False
    frames = image_processing.centerfit_gif(gif, cfg.matrix, fill_matrix)
    # Close the gif file to save memory now that we have copied out all of the frames
    gif.close()

    #TODO provide way to pre-process gifs and load/store them on disk
    try:
        print("Press CTRL-C to stop.")
        display.animated(cfg, frames)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    gif_viewer(image_file)
