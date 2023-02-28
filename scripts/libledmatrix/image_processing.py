#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont, GifImagePlugin
from rgbmatrix import graphics
import asyncio

from . import epoch, image_color, overlay


# center crop the image on our matrix
def crop(im, width, height):
    if im.mode != 'RGB':
        raise RuntimeError("image must be converted to RGB mode first!")
    im_width, im_height = im.size   # Get dimensions
    left = (im_width - width)//2
    top = (im_height - height)//2
    right = (im_width + width)//2
    bottom = (im_height + height)//2
    return im.crop((left, top, right, bottom))

# pad the image to the size of our matrix
def pad(im, width, height):
    if im.mode != 'RGB':
        raise RuntimeError("image must be converted to RGB mode first!")
    im_width, im_height = im.size
    padded = Image.new("RGB", (width, height), 0)
    left = (width - im_width)//2
    top = (height - im_height)//2
    padded.paste(im, (left, top))
    return padded


# if the image is a different aspect ratio
# than our matrix, center crop it to fit
# then padd the blank space to avoid green bars
# expects im to already be converted!
def crop_and_pad(im, matrix):
    if im.mode != 'RGB':
        raise RuntimeError("image must be converted to RGB mode first!")
    im = crop(im, matrix.width, matrix.height)
    im = pad(im, matrix.width, matrix.height)
    return im

def resize(im, matrix, fill_matrix):
    thumbnail_multiplier = 1
    if fill_matrix:
        thumbnail_multiplier = 1.2

    im.thumbnail((matrix.width*thumbnail_multiplier, matrix.height*thumbnail_multiplier), Image.ANTIALIAS)
    return im

def centerfit_image(im, matrix, fill_matrix):
    frames = []
    frame = im.copy()
    # resize before converting colorspace to maintain as much color info as possible
    frame = resize(frame, matrix, fill_matrix)
    frame = image_color.convertRGB(frame)
    frame = crop_and_pad(frame, matrix)
    frames.append(frame)
    return frames

def resize_crop_pad_gif(gif, matrix, fill_matrix):
    print(f"n_frames = {gif.n_frames}")
    frames = []
    for frame_index in range(0, gif.n_frames):
        gif.seek(frame_index)
        frame = gif.copy()

        # resize before converting colorspace to maintain as much color info as possible
        frame = resize(frame, matrix, fill_matrix)
        frame = image_color.convertRGB(frame)
        frame = crop_and_pad(frame, matrix)

        canvas = matrix.CreateFrameCanvas()
        canvas.SetImage(frame)
        frames.append(canvas)

    return frames

def centerfit_gif(gif, matrix, fill_matrix):
    #Resize a gif to center it on our matrix
    # and converts its colorspace to RGB
    # if fill_matrix is set, crop the gif to fill the matrix instead of padding it
    frames = []
    for frame_index in range(0, gif.n_frames):
        gif.seek(frame_index)
        frame = gif.copy()
        # resize before converting colorspace to maintain as much color info as possible
        frame = resize(frame, matrix, fill_matrix)
        frame = image_color.convertRGB(frame)
        frame = crop_and_pad(frame, matrix)
        frames.append(frame)
    return frames

def optimize_frame_count(frames, max_frames):
    def do_optimize(frames):
        # remove every other frame
        return frames[::2]

    while (len(frames) > max_frames):
        frames = do_optimize(frames)

    return frames


async def frames_to_canvases(frames, matrix, overlays=[], overlay_args=()):
    # Process the provided frames to a set of canvases
    # apply any provided overlays
    # overlay_args is a tuple of arguments to pass to the overlay functions
    canvases = []
    for frame in frames:
        # apply our overlays first
        frame = await overlay.apply_overlays(frame, overlays, overlay_args)
        await asyncio.sleep(0.001)
        canvas = matrix.CreateFrameCanvas()
        await asyncio.sleep(0.001)
        canvas.SetImage(frame)
        await asyncio.sleep(0.001)
        canvases.append(canvas)
        # sleep for a millisecond to avoid blocking for too long
        await asyncio.sleep(0.001)

    return canvases


def frames_to_canvases_sync(frames, matrix):
    # Process the provided frames to a set of canvases
    canvases = []
    for frame in frames:
        canvas = matrix.CreateFrameCanvas()
        canvas.SetImage(frame)
        canvases.append(canvas)
    return canvases

