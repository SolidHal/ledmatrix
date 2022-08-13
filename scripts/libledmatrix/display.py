#!/usr/bin/env python3
import asyncio
import logging

from . import image_processing, image_color, overlay, epoch
#TODO importing config before other modules breaks imports for some reason
from . import config

# display a set of frames with overlays which update every cur_epoch
def animated_overlaid(cfg, frames, colors):
    async def framebuffer_handler(cfg, canvases_queue, cur_epoch, ready_event):

        async def SwapOnVSync(canvas, framerate_fraction):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None,  cfg.matrix.SwapOnVSync, canvas, framerate_fraction)

        logging.info("in framebuffer_handler")
        cur_frame = 0
        # let the producer prepare some canvases first
        await ready_event.wait()
        logging.info(f"Starting framebuffer_handler loop at cur_epoch {cur_epoch}")
        canvases = await canvases_queue.get()
        while(True):
            canvas = canvases[cur_frame]
            # blocks until it can swap in the next canvas
            await SwapOnVSync(canvas, cfg.framerate_fraction)
            if cur_frame == len(canvases) - 1:
                cur_frame = 0
            else:
                cur_frame += 1

            if cur_epoch < epoch.Epoch():
                logging.info(f"Time to swap, old cur_epoch {cur_epoch}")
                #TODO do we need to add the cur_epoch to the canvases set so we know we are pulling
                # the canvas set for the cur_epoch we expect?
                canvases = canvases_queue.get_nowait()
                cur_epoch = epoch.Epoch()
                logging.info(f"swapped to new cur_epoch {cur_epoch}")

    async def prepare_canvases(cfg, frames, colors, canvases_queue, cur_epoch, ready_event):
        logging.info("Starting prepare_canvases loop")

        async def enqueue():
            canvases = await image_processing.frames_to_canvases(frames, cfg.matrix, overlays=[overlay.overlay_clock, overlay.overlay_weather], overlay_args=(cfg, colors, cur_epoch))
            logging.info(f"Putting canvases on the queue at cur_epoch {cur_epoch}")
            await canvases_queue.put(canvases)
            logging.info(f"Put canvases on the queue at cur_epoch {cur_epoch}")
            cur_epoch.next()

        # prepare 2 cur_epochs before we let the consumer know we are ready
        # this is to handle the case where we start at 11:40:59
        # and the consumer immediately needs the next cur_epoch
        await enqueue()
        await enqueue()

        logging.info("Setting ready")
        ready_event.set()

        while(True):
            await enqueue()

    async def run(cfg, frames, colors):
        # keep queue small to avoid delays in external updates
        # we will be at most the max size of the queue epochs behind
        canvases_queue = asyncio.Queue(3)
        ready_event = asyncio.Event()

        producer = asyncio.create_task(prepare_canvases(cfg=cfg,
                                                        frames=frames,
                                                        colors=colors,
                                                        canvases_queue=canvases_queue,
                                                        cur_epoch=epoch.Epoch(),
                                                        ready_event=ready_event))
        consumer = asyncio.create_task(framebuffer_handler(cfg=cfg,
                                                           canvases_queue=canvases_queue,
                                                           cur_epoch=epoch.Epoch(),
                                                           ready_event=ready_event))
        await asyncio.gather(producer, consumer)
        await canvases_queue.join()


    asyncio.run(run(cfg, frames, colors))



# display a set of frames
def animated(cfg, frames):
    canvases = image_processing.frames_to_canvases(frames, cfg.matrix)
    cur_frame = 0
    while(True):
        canvas = canvases[cur_frame]
        cfg.matrix.SwapOnVSync(canvas, config.framerate_fraction)
        if cur_frame == len(canvases) - 1:
            cur_frame = 0
        else:
            cur_frame += 1


# display a still image on the matrix with overlays which update every cur_epoch
def static_overlaid(matrix, image):
    image = image_processing.convert("RGB")
    matrix.SetImage(image)

# display a still image on the matrix
def static(matrix, image, dom_colors):
    pass
