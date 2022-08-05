#!/usr/bin/env python3
import time
import sys

from PIL import Image, GifImagePlugin
from rgbmatrix import RGBMatrix, RGBMatrixOptions

import config
import color
import display
import image


#TODO:
# add weather overlay to animated_overlaid

#TODO:
# add spotify current song album art static_overlaid impl


# compute the frames for the current minute, and the next minute
# show the current minute
# when time moves forward, show the next minute and start computing
# frames for the next minute

def gif_info(image_file):
    gif = Image.open(image_file)
    matrix = config.Matrix()
    # get the dominant colors before converting the gif to avoid
    # the padding from altering which colors are dominant
    dom_colors = color.dominant_colors_gif(gif)
    fill_matrix = False
    # pre process our frames so we can dedicate our resources to displaying them later
    frames = image.centerfit_gif(gif, matrix, fill_matrix)
    # Close the gif file to save memory now that we have copied out all of the frames
    print(f"Gif has {gif.n_frames} frames")
    gif.close()

    #TODO provide way load/store preprocessed gifs on disk
    try:
        print("Press CTRL-C to stop.")
        display.animated_overlaid(matrix, frames, dom_colors)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    gif_info(image_file)
