#!/usr/bin/env python3
import asyncio
import datetime
import logging
import io
import os
import threading
import queue
import pathlib
import pickle

from PIL import Image, GifImagePlugin

from . import spotify
from . import image_processing, image_color, overlay, epoch, weather
#TODO importing config before other modules breaks imports for some reason
from . import config


class FrameSet():
    def __init__(self, frames, colors, filename):
        self._frames = frames
        self._colors = colors
        self._filename = filename

    def frames(self):
        return self._frames

    def colors(self):
        return self._colors

    def filename(self):
        return self._filename

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
    canvases = asyncio.run(image_processing.frames_to_canvases(frames, cfg.matrix))
    cur_frame = 0
    while(True):
        canvas = canvases[cur_frame]
        cfg.matrix.SwapOnVSync(canvas, cfg.framerate_fraction)
        cur_frame = next_index(cur_frame, canvases)

# display a still image on the matrix with overlays which update every cur_epoch
def static_overlaid(matrix, image):
    image = image_processing.convert("RGB")
    matrix.SetImage(image)

# display a still image on the matrix
def static(cfg, image):
    cfg.matrix.SetImage(image)

def frameset_overlaid_and_spotify(cfg, frameset_list):
    async def prepare_canvases(cfg, frameset_list, canvases_queue, cur_epoch, ready_event, spotify_playing):
        logging.info("Starting prepare_canvases loop")

        async def enqueue(frameset):
            logging.info(f"Preparing canvases at cur_epoch {cur_epoch} for file {frameset.filename()} with {len(frameset.frames())} frames")
            canvases = await image_processing.frames_to_canvases(frameset.frames(), cfg.matrix, overlays=[overlay.overlay_clock, overlay.overlay_weather], overlay_args=(cfg, frameset.colors(), cur_epoch))
            logging.info(f"Putting canvases on the queue at cur_epoch {cur_epoch} for file {frameset.filename()} with {len(frameset.frames())} frames")
            await canvases_queue.put(canvases)
            logging.info(f"Put canvases on the queue at cur_epoch {cur_epoch} for file {frameset.filename()} with {len(frameset.frames())} frames")
            cur_epoch.next()

        num_epochs = 0
        # current frameset to use
        frameset_index = 0

        # prepare 2 cur_epochs before we let the consumer know we are ready
        # this is to handle the case where we start at 11:40:59
        # and the consumer immediately needs the next cur_epoch
        await enqueue(frameset_list[frameset_index])
        num_epochs+=1
        await enqueue(frameset_list[frameset_index])
        num_epochs+=1
        await enqueue(frameset_list[frameset_index])
        num_epochs+=1

        logging.info("Setting ready")
        ready_event.set()

        while(True):
            # move to the next frameset if the current frameset has been shown enough
            # but only if we were actually displaying it
            # if spotify is playing we aren't actually showing the epochs that are being enqueued
            if num_epochs >= cfg.epochs_per_frameset and not spotify_playing.is_set():
                num_epochs = 0
                frameset_index = next_index(frameset_index, frameset_list)

            await enqueue(frameset_list[frameset_index])
            num_epochs+=1

    async def prepare_spotify(cfg, spotify_canvases_queue, cur_epoch, spotify_playing):
        #TODO could support overlays on album art eventually, so continue taking an epoch just in case
        logging.info("Starting prepare_spotify loop")

        q = queue.Queue(1)
        spotify_thread_event = threading.Event()

        logging.info(f"prepare cache path = {cfg.spotify_api_token_cache_path}")

        spotify_t = threading.Thread(target=spotify.spotify_thread, args=(cfg.spotify_api_username, cfg.spotify_api_token_cache_path, cfg.spotify_api_excluded_devices, q, spotify_thread_event), daemon=True)
        spotify_t.start()


        async def enqueue(album_art):
            async def process_image(album_art):
                loop = asyncio.get_event_loop()
                bytes_album_art = await loop.run_in_executor(None, io.BytesIO, album_art)
                pil_album_art = await loop.run_in_executor(None, Image.open, bytes_album_art)
                frames = await loop.run_in_executor(None, image_processing.centerfit_image, pil_album_art, cfg.matrix, False)
                await loop.run_in_executor(None, pil_album_art.close)
                return frames

            frames = await process_image(album_art)
            canvases = await image_processing.frames_to_canvases(frames, cfg.matrix)

            logging.info(f"Putting spotify album art on queue")
            await spotify_canvases_queue.put(canvases)
            if not spotify_playing.is_set():
                logging.info("Setting spotify playing")
                spotify_playing.set()


        while(True):
            if spotify_thread_event.is_set():
                # get album art from thread queue and process it
                try:
                    album_art = q.get(block=False)
                except queue.Empty:
                    # no new album art to process
                    pass
                else:
                    # let us get interrupted before doing the enqueue work
                    await asyncio.sleep(0.001)
                    await enqueue(album_art)
            else:
                # nothing is playing, clear our state
                if spotify_playing.is_set():
                    logging.info("Clearing spotify playing")
                    spotify_playing.clear()

            await asyncio.sleep(1)



    async def framebuffer_handler(cfg, canvases_queue, spotify_canvases_queue, cur_epoch, ready_event, spotify_playing):

        async def SwapOnVSync(canvas, framerate_fraction):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None,  cfg.matrix.SwapOnVSync, canvas, framerate_fraction)

        def DeleteCanvases(canvas_list, cfg):
            if not canvas_list:
                return
            for c in canvas_list:
                cfg.matrix.DeleteFrameCanvas(c)

        logging.info("in framebuffer_handler")
        cur_frame = 0
        set_still = False
        old_spoityf_canvas_list = None
        spotify_canvas_list = None
        # let the producer prepare some canvases first
        await ready_event.wait()
        logging.info(f"Starting framebuffer_handler loop at cur_epoch {cur_epoch}")
        # update brightness now that we likely have sunset/sunrise data
        # TODO: BUG: the first epoch still uses the default brightness, which is annoying
        if cfg.cached_weather is not None:
            adaptive_brightness(cfg)
        old_canvases = None
        canvases = await canvases_queue.get()
        while(True):
            if not spotify_playing.is_set():
                if len(canvases) > 1:
                    canvas = canvases[cur_frame]
                    # blocks until it can swap in the next canvas
                    await SwapOnVSync(canvas, cfg.framerate_fraction)
                    cur_frame = next_index(cur_frame, canvases)
                elif not set_still:
                    set_still = True
                    logging.info("Set still image")
                    await SwapOnVSync(canvases[0], 1)
                else:
                    # give the producer a chance to make progress
                    await asyncio.sleep(0.0001)
            else:
                # timeout waiting so we return to showing the main canvases if spotify is no longer playing
                # otherwise we have no way to tell why we don't yet have a canvas on the queue
                # it could be that music stopped while we were waiting
                # or the same song is still playing
                old_spotify_canvas_list = spotify_canvas_list
                spotify_canvas_list = None
                try:
                    spotify_canvas_list = await asyncio.wait_for(spotify_canvases_queue.get(), 2)
                except asyncio.exceptions.TimeoutError:
                    pass
                if spotify_canvas_list is not None:
                    # we have some album art, show it.
                    await SwapOnVSync(spotify_canvas_list[0], 1)
                    # clean up unused spotify canvases
                    # can't just delete what we swapped out, since the old canvas
                    # could be from the other producer
                    DeleteCanvases(old_spotify_canvas_list, cfg)


            # continue draining the main queue, even if we aren't showing the canvases
            # since its easier than pausing & restarting the producer at the correct epoch
            if cur_epoch < epoch.Epoch():
                logging.info(f"Time to swap, old cur_epoch {cur_epoch}")
                #TODO do we need to add the cur_epoch to the canvases set so we know we are pulling
                # the canvas set for the cur_epoch we expect?
                # Only start deleting canvases when they are 2 epochs old to avoid
                # deleting things we are still using
                DeleteCanvases(old_canvases, cfg)
                old_canvases = canvases
                canvases = canvases_queue.get_nowait()
                cur_frame = 0
                set_still = False
                cur_epoch = epoch.Epoch()
                logging.info(f"swapped to new cur_epoch {cur_epoch}")
                if cfg.cached_weather is not None:
                    adaptive_brightness(cfg)


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


def frameset_and_spotify(cfg, canvases):

    async def prepare_spotify(cfg, spotify_canvases_queue, spotify_playing):
        logging.info("Starting prepare_spotify loop")

        q = queue.Queue(1)
        spotify_thread_event = threading.Event()

        logging.info(f"prepare cache path = {cfg.spotify_api_token_cache_path}")

        spotify_t = threading.Thread(target=spotify.spotify_thread, args=(cfg.spotify_api_username, cfg.spotify_api_token_cache_path, cfg.spotify_api_excluded_devices, q, spotify_thread_event), daemon=True)
        spotify_t.start()


        async def enqueue(album_art):
            async def process_image(album_art):
                loop = asyncio.get_event_loop()
                bytes_album_art = await loop.run_in_executor(None, io.BytesIO, album_art)
                pil_album_art = await loop.run_in_executor(None, Image.open, bytes_album_art)
                frames = await loop.run_in_executor(None, image_processing.centerfit_image, pil_album_art, cfg.matrix, False)
                await loop.run_in_executor(None, pil_album_art.close)
                return frames

            frames = await process_image(album_art)
            canvases = await image_processing.frames_to_canvases(frames, cfg.matrix)

            logging.info(f"Putting spotify album art on queue")
            await spotify_canvases_queue.put(canvases)
            if not spotify_playing.is_set():
                logging.info("Setting spotify playing")
                spotify_playing.set()


        while(True):
            if spotify_thread_event.is_set():
                # get album art from thread queue and process it
                try:
                    album_art = q.get(block=False)
                except queue.Empty:
                    # no new album art to process
                    pass
                else:
                    # let us get interrupted before doing the enqueue work
                    await asyncio.sleep(0.001)
                    await enqueue(album_art)
            else:
                # nothing is playing, clear our state
                if spotify_playing.is_set():
                    logging.info("Clearing spotify playing")
                    spotify_playing.clear()

            await asyncio.sleep(1)



    async def framebuffer_handler(cfg, canvases, spotify_canvases_queue, spotify_playing):

        async def SwapOnVSync(canvas, framerate_fraction):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None,  cfg.matrix.SwapOnVSync, canvas, framerate_fraction)

        def DeleteCanvases(canvas_list, cfg):
            if not canvas_list:
                return
            for c in canvas_list:
                cfg.matrix.DeleteFrameCanvas(c)

        logging.info("in framebuffer_handler")
        cur_frame = 0
        set_still = False
        old_spoityf_canvas_list = None
        spotify_canvas_list = None
        # let the producer prepare some canvases first
        logging.info(f"Starting framebuffer_handler loop")

        while(True):
            if not spotify_playing.is_set():
                if len(canvases) > 1:
                    canvas = canvases[cur_frame]
                    # blocks until it can swap in the next canvas
                    await SwapOnVSync(canvas, cfg.framerate_fraction)
                    cur_frame = next_index(cur_frame, canvases)
                elif not set_still:
                    set_still = True
                    logging.info("Set still image")
                    await SwapOnVSync(canvases[0], 1)
                else:
                    # give the producer a chance to make progress
                    await asyncio.sleep(0.0001)
            else:
                # timeout waiting so we return to showing the main canvases if spotify is no longer playing
                # otherwise we have no way to tell why we don't yet have a canvas on the queue
                # it could be that music stopped while we were waiting
                # or the same song is still playing
                old_spotify_canvas_list = spotify_canvas_list
                spotify_canvas_list = None
                try:
                    spotify_canvas_list = await asyncio.wait_for(spotify_canvases_queue.get(), 2)
                except asyncio.exceptions.TimeoutError:
                    pass
                if spotify_canvas_list is not None:
                    # we have some album art, show it.
                    await SwapOnVSync(spotify_canvas_list[0], 1)
                    # clean up unused spotify canvases
                    # can't just delete what we swapped out, since the old canvas
                    # could be from the other producer
                    DeleteCanvases(old_spotify_canvas_list, cfg)

    async def run(cfg, canvases):
        spotify_canvases_queue = asyncio.Queue(1)
        spotify_playing = asyncio.Event()

        spotify_producer = asyncio.create_task(prepare_spotify(cfg=cfg,
                                                       spotify_canvases_queue=spotify_canvases_queue,
                                                       spotify_playing=spotify_playing))
        consumer = asyncio.create_task(framebuffer_handler(cfg=cfg,
                                                           canvases=canvases,
                                                           spotify_canvases_queue=spotify_canvases_queue,
                                                           spotify_playing=spotify_playing))
        await asyncio.gather(spotify_producer, consumer)

    asyncio.run(run(cfg, canvases))



def process_images(cfg, image_dir: pathlib.Path):
    processed_image_cache = image_dir / "processed_cache"
    processed_image_cache.mkdir(exist_ok=True)

    p = image_dir.glob('**/*')
    # include all image files, excluding our frameset cache
    image_files = [x for x in p if (x.is_file() and not x.is_relative_to(processed_image_cache))]

    frameset_list = []


    frameset_extension = f"{cfg.max_frames}_frame_frameset"
    p = processed_image_cache.glob('*.*')
    processed_image_cache_files = [x.name for x in p if x.is_file()]

    for f in image_files:
        cached_image_name = f"{f.stem}.{frameset_extension}"
        cached_image_path = processed_image_cache / cached_image_name

        if cached_image_name in processed_image_cache_files:
            # load the frameset and append it
            with open(cached_image_path, "rb") as cache:
                frameset = pickle.load(cache)
                frameset_list.append(frameset)
            logging.info(f"Loaded image from cache: {cached_image_path} with {len(frameset.frames())} frames")

        else:
            im = Image.open(f)
            if hasattr(im, "n_frames"):
                # then we are working with a gif
                # get the dominant colors before converting the gif to avoid
                # the padding from altering which colors are dominant
                dom_colors = image_color.dominant_colors_gif(im)
                fill_matrix = False
                # pre process our frames so we can dedicate our resources to displaying them later
                frames = image_processing.centerfit_gif(im, cfg.matrix, fill_matrix)
                frames = image_processing.optimize_frame_count(frames, cfg.max_frames)
                logging.info(f"Processed {f} as a gif with {len(frames)} frames")

                frameset = FrameSet(frames, dom_colors, f)

                with open(cached_image_path, "wb") as cache:
                    logging.info(f"Caching to {cached_image_path}")
                    pickle.dump(frameset, cache)

                frameset_list.append(frameset)

            else:
                # then we are working with a static image
                dom_colors = image_color.dominant_colors(im)
                fill_matrix = False
                frames = image_processing.centerfit_image(im, cfg.matrix, fill_matrix)
                logging.info(f"Processed {f} as a static image with {len(frames)} frames")

                frameset = FrameSet(frames, dom_colors, f)

                with open(cached_image_path, "wb") as cache:
                    logging.info(f"Caching to {cached_image_path}")
                    pickle.dump(frameset, cache)

                frameset_list.append(frameset)
            im.close()

    return frameset_list

def adaptive_brightness(cfg):
    if cfg.cached_weather is None:
        logging.info(f"No weather data, not adjusting brightness")
        return

    dtnow = datetime.datetime.now()
    sunrise = weather.to_sunrise(cfg.cached_weather)
    sunset = weather.to_sunset(cfg.cached_weather)
    new_brightness  = 0

    # if before sunrise, or after sunset, set to minimum brightness
    # if after sunrise, and before sunset set to full brightness
    # if within 1 hour after sunrise, or 1 hour before sunset, set to partial brightness
    if dtnow > sunrise and dtnow < sunset:
        if dtnow > (sunrise + cfg.partial_delta) and dtnow < (sunset - cfg.partial_delta):
            # then daytime, use full brightness
            new_brightness = cfg.brightness
        else:
            # then dawn/dusk, use partial brightness
            new_brightness = cfg.partial_brightness
    else:
        # then nighttime, use minimum brightness
        new_brightness = cfg.nighttime_brightness

    if cfg.matrix.brightness != new_brightness:
        logging.info(f"Set matrix brightness to {new_brightness}")
        # setting the matrix brightness also updates the brightness of all
        # created canvases in the cpp code
        cfg.matrix.brightness = new_brightness

    return
