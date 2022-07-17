#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, GifImagePlugin


def gif_viewer(image_file):

    gif = Image.open(image_file)

    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 64  #TODO change this to 128 when all 4 are hooked up
    options.cols = 128
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'

    matrix = RGBMatrix(options = options)

    # Make image fit our screen.

    # center crop the image on our matrix
    def crop(im):
        width, height = im.size   # Get dimensions

        left = int((width - matrix.width)/2)
        top = int((height - matrix.height)/2)
        right = int((width + matrix.width)/2)
        bottom = int((height + matrix.height)/2)
        return im.crop((left, top, right, bottom))

    # pad the image to the size of our matrix
    def pad(im):
        im_width, im_height = im.size
        padded = Image.new(im.mode, (matrix.width, matrix.height), 0)
        left = int((matrix.width - im_width)/2)
        top = int((matrix.height - im_height)/2)
        padded.paste(im, (left, top))
        return padded

    # if the image is a different aspect ratio
    # than our matrix, center crop it to fit
    # then padd the blank space to avoid green bars
    def crop_and_pad(im):
        # must convert to RGB so the mode is correct
        # for the following operations
        # not doing so either results in a B&W image
        # or green bars
        # the matrix API expects an RGB image anyway
        im = im.convert('RGB')
        im = crop(im)
        im = pad(im)
        return im

    # pre process our frames so we can dedicate our resources to displaying them later
    print(f"n_frames = {gif.n_frames}")
    frames_range = range(0, gif.n_frames)
    frames = []
    for frame_index in frames_range:
        gif.seek(frame_index)
        frame = gif.copy()
        frame.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)
        frame = crop_and_pad(frame)
        frames.append(frame)

    cur_frame = 0
    try:
        print("Press CTRL-C to stop.")
        while(True):
            # TODO we could make this more efficient by copying the frames into Canvases first
            frame = frames[cur_frame]
            matrix.SetImage(frame)
            if cur_frame == gif.n_frames - 1:
                cur_frame = 0
            else:
                cur_frame += 1
            time.sleep(0.1)

    # cur_frame = 0
    # try:
    #     print("Press CTRL-C to stop.")
    #     while(True):
    #         # TODO we could make this more efficient by copying the frames into Canvases first
    #         gif.seek(cur_frame)
    #         gif_copy = gif.copy()
    #         gif_copy.thumbnail((matrix.width, matrix.height), Image.ANTIALIAS)
    #         matrix.SetImage(gif_copy.convert('RGB'))
    #         if cur_frame == gif.n_frames - 1:
    #             cur_frame = 0
    #         else:
    #             cur_frame += 1
    #         time.sleep(0.5)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    gif_viewer(image_file)
