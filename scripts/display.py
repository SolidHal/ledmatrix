#!/usr/bin/env python3
import asyncio
import logging

from rgbmatrix import RGBMatrix

import config
import image
import overlay
from epoch import Epoch


# display a set of frames with overlays which update every epoch
def animated_overlaid(matrix, frames, colors):
    logging.basicConfig(level=logging.INFO,)
    async def framebuffer_handler(matrix, canvases_queue, epoch, ready_event):

        async def SwapOnVSync(canvas, framerate_fraction):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None,  matrix.SwapOnVSync, canvas, framerate_fraction)

        logging.info("in framebuffer_handler")
        cur_frame = 0
        # let the producer prepare some canvases first
        await ready_event.wait()
        logging.info(f"Starting framebuffer_handler loop at epoch {epoch}")
        canvases = await canvases_queue.get()
        while(True):
            canvas = canvases[cur_frame]
            # blocks until it can swap in the next canvas
            await SwapOnVSync(canvas, config.framerate_fraction)
            if cur_frame == len(canvases) - 1:
                cur_frame = 0
            else:
                cur_frame += 1

            if epoch < Epoch():
                logging.info(f"Time to swap, old epoch {epoch}")
                #TODO do we need to add the epoch to the canvases set so we know we are pulling
                # the canvas set for the epoch we expect?
                canvases = canvases_queue.get_nowait()
                epoch = Epoch()
                logging.info(f"swapped to new epoch {epoch}")

    async def prepare_canvases(matrix, frames, colors, canvases_queue, epoch, ready_event):
        logging.info("Starting prepare_canvases loop")

        async def enqueue():
            canvases = await image.frames_to_canvases(frames, matrix, overlays=[overlay.overlay_clock], overlay_args=(colors, epoch))
            logging.info(f"Putting canvases on the queue at epoch {epoch}")
            await canvases_queue.put(canvases)
            logging.info(f"Put canvases on the queue at epoch {epoch}")
            epoch.next()

        # prepare 2 epochs before we let the consumer know we are ready
        # this is to handle the case where we start at 11:40:59
        # and the consumer immediately needs the next epoch
        await enqueue()
        await enqueue()

        logging.info("Setting ready")
        ready_event.set()

        while(True):
            await enqueue()

    async def run(matrix, frames, colors):
        canvases_queue = asyncio.Queue(5)
        ready_event = asyncio.Event()

        producer = asyncio.create_task(prepare_canvases(matrix=matrix,
                                                        frames=frames,
                                                        colors=colors,
                                                        canvases_queue=canvases_queue,
                                                        epoch=Epoch(),
                                                        ready_event=ready_event))
        consumer = asyncio.create_task(framebuffer_handler(matrix=matrix,
                                                           canvases_queue=canvases_queue,
                                                           epoch=Epoch(),
                                                           ready_event=ready_event))
        await asyncio.gather(producer, consumer)
        await canvases_queue.join()


    asyncio.run(run(matrix, frames, colors))



# display a set of frames
def animated(matrix, frames):
    canvases = image.frames_to_canvases(frames, matrix)
    cur_frame = 0
    while(True):
        canvas = canvases[cur_frame]
        matrix.SwapOnVSync(canvas, config.framerate_fraction)
        if cur_frame == len(canvases) - 1:
            cur_frame = 0
        else:
            cur_frame += 1


# display a still image on the matrix with overlays which update every epoch
def static_overlaid(matrix, image):
    image = image.convert("RGB")
    matrix.SetImage(image)

# display a still image on the matrix
def static(matrix, image, dom_colors):
    pass
