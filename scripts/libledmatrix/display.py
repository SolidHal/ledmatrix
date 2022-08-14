#!/usr/bin/env python3
import asyncio
import logging

from . import image_processing, image_color, overlay, epoch
#TODO importing config before other modules breaks imports for some reason
from . import config


class FrameSet():
    def __init__(self, frames, colors):
        self._frames = frames
        self._colors = colors

    def frames(self):
        return self._frames

    def colors(self):
        return self._colors

    def is_static(self):
        if len(self._frames) > 1:
            return False
        return True

    def is_animated(self):
        return not self.is_static()

# helper to support looping an index around a list
def next_index(index, indexed_list):
    if index == len(indexed_list) - 1:
        return 0
    return index + 1

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
            cur_frame = next_index(cur_frame, canvases)

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


    asyncio.run(run(cfg, frames, colors))



# display a set of frames
def animated(cfg, frames):
    canvases = image_processing.frames_to_canvases(frames, cfg.matrix)
    cur_frame = 0
    while(True):
        canvas = canvases[cur_frame]
        cfg.matrix.SwapOnVSync(canvas, config.framerate_fraction)
        cur_frame = next_index(cur_frame, canvases)

# display a still image on the matrix with overlays which update every cur_epoch
def static_overlaid(matrix, image):
    image = image_processing.convert("RGB")
    matrix.SetImage(image)

# display a still image on the matrix
def static(matrix, image, dom_colors):
    pass

def frameset_overlaid_and_spotify(cfg, frameset_list):


    async def prepare_canvases(cfg, frameset_list, canvases_queue, cur_epoch, ready_event, spotify_playing):
        logging.info("Starting prepare_canvases loop")

        async def enqueue(frames, colors):
            canvases = await image_processing.frames_to_canvases(frames, cfg.matrix, overlays=[overlay.overlay_clock, overlay.overlay_weather], overlay_args=(cfg, colors, cur_epoch))
            logging.info(f"Putting canvases on the queue at cur_epoch {cur_epoch}")
            await canvases_queue.put(canvases)
            logging.info(f"Put canvases on the queue at cur_epoch {cur_epoch}")
            cur_epoch.next()


        # wait 3 epochs before switching to the next frameset
        next_frameset_num_epochs = 3
        num_epochs = 0
        # current frameset to use
        frameset_index = 0

        # prepare 2 cur_epochs before we let the consumer know we are ready
        # this is to handle the case where we start at 11:40:59
        # and the consumer immediately needs the next cur_epoch
        await enqueue(frameset_list[frameset_index].frames(), frameset_list[frameset_index].colors())
        num_epochs+=1
        await enqueue(frameset_list[frameset_index].frames(), frameset_list[frameset_index].colors())
        num_epochs+=1

        logging.info("Setting ready")
        ready_event.set()

        while(True):
            # move to the next frameset if the current frameset has been shown enough
            # but only if we were actually displaying it
            # if spotify is playing we aren't actually showing the epochs that are being enqueued
            if num_epochs == next_frameset_num_epochs and not spotify_playing.is_set():
                num_epochs = 0
                frameset_index = next_index(frameset_index, frameset_list)

            await enqueue(frameset_list[frameset_index].frames(), frameset_list[frameset_index].colors())
            num_epochs+=1

    async def prepare_spotify(cfg, spotify_canvases_queue, cur_epoch, spotify_playing):
        #TODO could support overlays on album art eventually, so continue taking an epoch just in case
        logging.info("Starting prepare_spotify loop")


        # TODO check if music is playing, if it is, prepare our canvas and then set spotify_playing
        # so the consumer and other producer know
        # if it isn't, await a few seconds before checking again

        while(True):
            print(cfg.spotify_api.currently_playing())
            print(cfg.spotify_api.devices())
            await asyncio.sleep(3)



    async def framebuffer_handler(cfg, canvases_queue, spotify_canvases_queue, cur_epoch, ready_event, spotify_playing):

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
            if not spotify_playing.is_set():
                canvas = canvases[cur_frame]

                #TODO if our canvases list only has 1 frame, we can chill out a bit here
                # and simply show that frame until the next epoch
                # instead of swapping it every vsync

                # blocks until it can swap in the next canvas
                await SwapOnVSync(canvas, cfg.framerate_fraction)
                cur_frame = next_index(cur_frame, canvases)

            else:
                # timeout waiting so we return to showing the main canvases if spotify is no longer playing
                # otherwise we have no way to tell why we don't yet have a canvas on the queue
                # it could be that music stopped while we were waiting
                # or the same song is still playing
                canvas = await asyncio.wait_for(spotify_canvases_queue.get(), 2)
                if canvas is not None:
                    # we have some album art, show it.
                    await SwapOnVSync(canvas, 1)

            # continue draining the main queue, even if we aren't showing the canvases
            # since its easier than pausing & restarting the producer at the correct epoch
            if cur_epoch < epoch.Epoch():
                logging.info(f"Time to swap, old cur_epoch {cur_epoch}")
                #TODO do we need to add the cur_epoch to the canvases set so we know we are pulling
                # the canvas set for the cur_epoch we expect?
                canvases = canvases_queue.get_nowait()
                cur_epoch = epoch.Epoch()
                logging.info(f"swapped to new cur_epoch {cur_epoch}")

    async def run(cfg, frameset_list):
        # keep queue small to avoid delays in external updates
        # we will be at most the max size of the queue epochs behind
        canvases_queue = asyncio.Queue(3)
        spotify_canvases_queue = asyncio.Queue(1)
        ready_event = asyncio.Event()
        spotify_playing = asyncio.Event()

        producer = asyncio.create_task(prepare_canvases(cfg=cfg,
                                                        frameset_list=frameset_list,
                                                        canvases_queue=canvases_queue,
                                                        cur_epoch=epoch.Epoch(),
                                                        ready_event=ready_event,
                                                        spotify_playing=spotify_playing))
        spotify_producer = asyncio.create_task(prepare_spotify(cfg=cfg,
                                                       spotify_canvases_queue=spotify_canvases_queue,
                                                       cur_epoch=epoch.Epoch(),
                                                       spotify_playing=spotify_playing))
        consumer = asyncio.create_task(framebuffer_handler(cfg=cfg,
                                                           canvases_queue=canvases_queue,
                                                           spotify_canvases_queue=spotify_canvases_queue,
                                                           cur_epoch=epoch.Epoch(),
                                                           ready_event=ready_event,
                                                           spotify_playing=spotify_playing))
        await asyncio.gather(producer, spotify_producer, consumer)

    asyncio.run(run(cfg, frameset_list))






    # have additional producer that checks spotify for playing music and tells the main producer to pause when music is playing
    # spotify producer should prepare its frameset & canvas, then set the spotify_event
    # which tells the main producer to await
    # and tells the consumer to start checking for updates more often, and just to use a static image instead of SwapOnVsync
    # the spotify producer then clears the queue and puts its frameset onto it
    # we can use ready_event to ensure the consumer waits for the spotify producer to be ready
    # modify this logic a bit, maybe have the spotify producer use a dedicated queue
    # then the main producer can continue filling the main queue, and the consumer can continue draining the main queue every epoch
    # so that we can go back to displaying the images as soon as music has stopped
    # this has the added benefit of not needing to worry about race conditions when clearing the main queue when switching producers


    # how to switch back from spotify to normal producer
    # when in spotify mode the consumer constantly waits on the spotify queue for a new canvas to push
    # if it gets one, before showing it, it first checks that "spotify_playing" event is set
    # if it is no longer set, the consumer should return to the normal producers queue
