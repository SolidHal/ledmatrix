#!/usr/bin/env python3

import asyncio
import time
import sys
import os
import logging
import pathlib
import random

import click
from PIL import Image, GifImagePlugin

from libledmatrix import spotify
from libledmatrix import display, image_color, image_processing
#TODO importing config before other modules breaks imports for some reason
from libledmatrix import config

logging.basicConfig(level=logging.INFO,)


def run(cfg, image_dir_path):
    # ensure we can connect to spotify
    # spotify.start_api(cfg.spotify_api_username, cfg.spotify_api_token_cache_path)
    frameset_list = display.process_images(cfg, image_dir_path)
    random.shuffle(frameset_list)
    if len(frameset_list) < 1:
        raise RuntimeException(f"No loadable images found in {image_dir_path}")

    logging.info("converting frames to canavses....")
    canvases = []
    # process the framesets into canvases, if we have < 360 frames, repeat the set until we have 360
    for frameset in frameset_list:
        c = image_processing.frames_to_canvases_sync(frameset.frames(), cfg.matrix)
        # if we have less than 360 frames, append the set until we have > 360
        for i in range(0, 360//len(frameset.frames())):
            canvases = canvases + c

    logging.info("frames converted to canvases")

    try:
        print("Press CTRL-C to stop.")
        display.frameset_and_spotify(cfg, canvases)

    except KeyboardInterrupt:
        sys.exit(0)




@click.command()
@click.option("--image_dir", type=str, required=True, help="path to the directory of images to display")
@click.option('--spotify_api_username', required=True,
              default=lambda: os.environ.get('SPOTIFY_API_USERNAME', ''),
              show_default='SPOTIFY_API_USERNAME envvar')
@click.option('--spotify_api_token_cache_path', required=False,
              default=lambda: os.environ.get('SPOTIFY_API_TOKEN_CACHE_PATH', ''),
              show_default='SPOTIFY_API_TOKEN_CACHE_PATH envvar')
@click.option('--spotify_api_excluded_devices', required=False,
              default=lambda: os.environ.get('SPOTIFY_API_EXCLUDED_DEVICES', ''),
              show_default='SPOTIFY_API_EXCLUDED_DEVICES envvar')
def main(image_dir, spotify_api_username, spotify_api_token_cache_path, spotify_api_excluded_devices):
    cfg = config.Config()
    cfg.spotify_api_username = spotify_api_username
    cfg.spotify_api_token_cache_path = spotify_api_token_cache_path

    # no weather data, so just use a reasonable default for brightness
    cfg.matrix.brightness = cfg.partial_brightness

    # show each frameset for roughly a minute
    # at ~6 fps for gifs, that means we can show 6*60=360 frames
    cfg.max_frames = 360

    if isinstance(spotify_api_excluded_devices, list):
        cfg.spotify_api_excluded_devices = spotify_api_excluded_devices
    else:
        if ";" in spotify_api_excluded_devices:
            cfg.spotify_api_excluded_devices = spotify_api_excluded_devices.split(";")
        else:
            cfg.spotify_api_excluded_devices.append(spotify_api_excluded_devices)

    image_dir_path = pathlib.Path(image_dir)

    run(cfg, image_dir_path)


if __name__ == "__main__":
    main()

