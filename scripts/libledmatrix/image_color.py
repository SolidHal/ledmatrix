#!/usr/bin/env python3

from PIL import Image

def invert_color(color):
    return (255 - color[0], 255 - color[1], 255 - color[2])

def complement_color(color):
    # Sum of the min & max of (a, b, c)
    def hilo(a, b, c):
        if c < b: b, c = c, b
        if b < a: a, b = b, a
        if c < b: b, c = c, b
        return a + c

    r = color[0]
    g = color[1]
    b = color[2]
    k = hilo(r, g, b)
    return tuple(k - u for u in (r, g, b))

def contrast_color_bw(color, inverse=False):
    """Returns black or white depend on which
       will contrast better against the provided color
       if inverse is true, the color that is closest will be provided instead
    """
    def diff(color1, color2):
        return (abs(color1[0] - color2[0]) +
               abs(color1[1] - color2[1]) +
               abs(color1[2] - color2[2]))

    white = (255, 255, 255)
    black = (0, 0, 0)
    b_diff = diff(color, black)
    w_diff = diff(color, white)
    if (w_diff > b_diff):
        return white
    return black

def convertRGB(im):
    # must convert to RGB so the mode is correct
    # for the following operations
    # not doing so either results in a B&W image
    # or green bars
    # the matrix API expects an RGB image anyway
    return im.convert('RGB')

def dominant_colors(im):
    im = convertRGB(im)
    colors = im.getcolors()
    colors.sort(key = lambda x: x[0], reverse = True)
    # what if we don't have 3 colors? Return first color instead
    if len(colors) == 1:
        colors = (colors)
    if len(colors) < 3:
        colors.append(colors[0])
        if len(colors) < 3:
            colors.append(colors[0])

    return (colors[0][1],
            colors[1][1],
            colors[2][1])


def dominant_colors_gif(gif):
    # use the dominant colors of the first frame
    # need to make a copy of the gif first to avoid modifying
    # the seek pointer in the original
    gif_copy = gif.copy()
    gif_copy.seek(0)
    return dominant_colors(gif_copy)

