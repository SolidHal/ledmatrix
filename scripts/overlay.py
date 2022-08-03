#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont, GifImagePlugin
import time
import color
from epoch import Epoch


## Overlay args:
# - im : the image to place the overlay on
# - colors : the colors to use for the overlay
# - epoch : the Epoch() to create this overlay for, stored in minutes

def apply_overlays(frame, overlays=[], overlay_args=()):
    # apply any provided overlays
    # overlay_args is a tuple of arguments to pass to the overlay functions
    overlaid_im = frame
    for overlay in overlays:
        overlaid_im = overlay(overlaid_im, *overlay_args)

    return overlaid_im


def overlay_clock(im, colors, epoch):
    if not len(colors) >= 3:
        raise ValueError("Need at least 3 colors to overlay a clock")

    rect_height = 14
    rect_width = 32
    font = ImageFont.load("pillow-fonts/helvR12.pil")
    overlay_im = Image.new("RGB", (rect_width+1, rect_height+1))
    draw = ImageDraw.Draw(overlay_im)
    # use the 1st and 2nd most dominant colors for the rectangle & frame
    draw.rectangle((0, 0, rect_width, rect_height), fill=colors[0], outline=colors[1])
    time_str = time.strftime("%I:%M", time.localtime(epoch.seconds()))
    # use a color we know will contrast wtih the rectangle fill color for the time
    draw.text((1,0), time_str, font=font, fill=color.contrast_color_bw(colors[0]))
    im_copy = im.copy()
    im_copy.paste(overlay_im, (0,0))
    return im_copy
