#!/usr/bin/env python3
import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, GifImagePlugin, ImageDraw
from threading import Thread, Event
from queue import Queue
import logging
import copy
import concurrent.futures

import config
import image
import overlays
import color
from epoch import Epoch




# compute the frames for the current minute, and the next minute
# show the current minute
# when time moves forward, show the next minute and start computing
# frames for the next minute

logging.basicConfig(level=logging.INFO, format='(%(threadName)-9s) %(message)s',)

def gif_info(image_file):
    gif = Image.open(image_file)
    matrix = config.Matrix()
    # pre process our frames so we can dedicate our resources to displaying them later
    fill_matrix = False
    dom_colors = color.dominant_colors_gif(gif)
    frames = image.centerfit_gif(gif, matrix, fill_matrix)
    # Close the gif file to save memory now that we have copied out all of the frames
    gif.close()


    def framebuffer_handler(canvases_queue, epoch, ready_event):
        logging.info("in framebuffer_handler")
        # play gifs at 6 fps
        fps = 8
        framerate_fraction = config.refresh_rate / fps
        cur_frame = 0

        # let the producer prepare some canvases first
        ready_event.wait()
        logging.info(f"Starting framebuffer_handler loop at epoch {epoch}")
        canvases = canvases_queue.get_nowait()
        while(True):
            canvas = canvases[cur_frame]
            # blocks until it can swap in the next canvas
            matrix.SwapOnVSync(canvas, framerate_fraction)
            if cur_frame == len(canvases) - 1:
                cur_frame = 0
            else:
                cur_frame += 1

            if epoch < Epoch():
                # swap our canvases to the next set
                # assumes the producer can create a set of canvases in < 1 minute
                # otherwise we will drain the queue and error
                logging.info(f"Time to swap, old epoch {epoch}")
                #TODO do we need to add the epoch to the canvases set so we know we are pulling
                # the canvas set for the epoch we expect?
                canvases = canvases_queue.get_nowait()
                epoch = Epoch()
                logging.info(f"swapped to new epoch {epoch}")

    def prepare_canvases(frames, canvases_queue, epoch, ready_event):
        logging.info("Starting prepare_canvases loop")

        canvases = image.frames_to_canvases(frames, matrix, overlays=[overlays.overlay_clock], overlay_args=(dom_colors, epoch))
        logging.info(f"Putting canvases on the queue at epoch {epoch}")
        canvases_queue.put(canvases)
        logging.info(f"Put canvases on the queue at epoch {epoch}")
        epoch.next()


        canvases = image.frames_to_canvases(frames, matrix, overlays=[overlays.overlay_clock], overlay_args=(dom_colors, epoch))
        logging.info(f"Putting canvases on the queue at epoch {epoch}")
        canvases_queue.put(canvases)
        logging.info(f"Put canvases on the queue at epoch {epoch}")
        epoch.next()

        ready_event.set()

        while(True):
            canvases = image.frames_to_canvases(frames, matrix, overlays=[overlays.overlay_clock], overlay_args=(dom_colors, epoch))
            logging.info(f"Putting canvases on the queue at epoch {epoch}")
            canvases_queue.put(canvases)
            logging.info(f"Put canvases on the queue at epoch {epoch}")
            epoch.next()

    #TODO provide way to pre-process gifs and load/store them on disk
    try:
        print("Press CTRL-C to stop.")
        canvases_queue = Queue(maxsize=4)
        ready_event = Event()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(prepare_canvases, frames, canvases_queue, Epoch(), ready_event)
            executor.submit(framebuffer_handler, canvases_queue, Epoch(), ready_event)

        while(True):
            time.sleep(60000)


    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    gif_info(image_file)
