#!/usr/bin/env python3


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
from libledmatrix.display import FrameSet
#TODO importing config before other modules breaks imports for some reason
from libledmatrix import config

logging.basicConfig(level=logging.INFO,)


def process_images(cfg, image_dir: pathlib.Path):
    p = image_dir.glob('**/*')
    image_files = [x for x in p if x.is_file()]

    frameset_list = []

    for f in image_files:
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
            frameset_list.append(frameset)

        else:
            # then we are working with a static image
            dom_colors = image_color.dominant_colors(im)
            fill_matrix = False
            frames = image_processing.centerfit_image(im, cfg.matrix, fill_matrix)
            logging.info(f"Processed {f} as a static image with {len(frames)} frames")

            frameset = FrameSet(frames, dom_colors, f)
            frameset_list.append(frameset)

        im.close()

    return frameset_list


def run(cfg, image_dir_path):
    # ensure we can connect to spotify
    # spotify.start_api(cfg.spotify_api_username, cfg.spotify_api_token_cache_path)
    frameset_list = process_images(cfg, image_dir_path)
    if len(frameset_list) < 1:
        raise RuntimeException(f"No loadable images found in {image_dir_path}")


    #TODO provide way load/store preprocessed gifs on disk
    try:
        print("Press CTRL-C to stop.")
        display.frameset_overlaid_and_spotify(cfg, frameset_list)

    except KeyboardInterrupt:
        sys.exit(0)




@click.command()
@click.option("--image_dir", type=str, required=True, help="path to the directory of images to display")
@click.option('--weather_api_key', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_KEY', ''),
              show_default='OPENWEATHER_API_KEY envvar')
@click.option('--weather_api_lat', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_LAT', ''),
              show_default='OPENWEATHER_API_LAT envvar')
@click.option('--weather_api_lon', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_LON', ''),
              show_default='OPENWEATHER_API_LON envvar')
@click.option('--spotify_api_username', required=True,
              default=lambda: os.environ.get('SPOTIFY_API_USERNAME', ''),
              show_default='SPOTIFY_API_USERNAME envvar')
@click.option('--spotify_api_token_cache_path', required=False,
              default=lambda: os.environ.get('SPOTIFY_API_TOKEN_CACHE_PATH', ''),
              show_default='SPOTIFY_API_TOKEN_CACHE_PATH envvar')
@click.option('--spotify_api_excluded_devices', required=False,
              default=lambda: os.environ.get('SPOTIFY_API_EXCLUDED_DEVICES', ''),
              show_default='SPOTIFY_API_EXCLUDED_DEVICES envvar')
def main(image_dir, weather_api_key, weather_api_lat, weather_api_lon, spotify_api_username, spotify_api_token_cache_path, spotify_api_excluded_devices):
    cfg = config.Config()
    cfg.weather_api_key = weather_api_key
    cfg.weather_api_lat = weather_api_lat
    cfg.weather_api_lon = weather_api_lon
    cfg.spotify_api_username = spotify_api_username
    cfg.spotify_api_token_cache_path = spotify_api_token_cache_path

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
