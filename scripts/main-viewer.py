#!/usr/bin/env python3

import time
import sys
import os
import logging
import pathlib

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
            logging.info(f"Processed {f} as a gif with {len(frames)} frames")

            frameset = FrameSet(frames, dom_colors)
            frameset_list.append(frameset)

        else:
            # then we are working with a static image
            dom_colors = image_color.dominant_colors(im)
            fill_matrix = False
            frames = image_processing.centerfit_image(im, cfg.matrix, fill_matrix)
            logging.info(f"Processed {f} as a static image with {len(frames)} frames")

            frameset = FrameSet(frames, dom_colors)
            frameset_list.append(frameset)

        im.close()

    return frameset_list


def run(cfg, image_dir_path):
    cfg.spotify_api = spotify.start_api(cfg.spotify_api_username)
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
def main(image_dir, weather_api_key, weather_api_lat, weather_api_lon, spotify_api_username):
    cfg = config.Config()
    cfg.weather_api_key = weather_api_key
    cfg.weather_api_lat = weather_api_lat
    cfg.weather_api_lon = weather_api_lon
    cfg.spotify_api_username = spotify_api_username

    image_dir_path = pathlib.Path(image_dir)

    run(cfg, image_dir_path)


if __name__ == "__main__":
    main()


#TODO:
# add spotify current song album art static_overlaid impl

# take a directory to images/gifs
#TODO store the preprocessed info somehow on disk as a cache to save on startup time?
# preprocess these to a struct of
# - frames
# - dom_colors
# call this a FrameSet object

# call the collection for these structs a: frameset_list?

# store the index of the current FrameSet object
# after (5?) minutes start using the next FrameSet object
# rollover to repeat all available images/gifs

#TODO might need to shorten epoch so this is responsive? Or we can have a check more frequently in the main SetImage loop?
# check for music playing on spotify
# have config option for ignored devices
# if music is playing, get the album art for the current song, process it, and display it
# instead of displaying what is in the canvas queue
# when music stops, empty to canvas queue, and pickup where the image loop left off
# we could continue filling/draining the canvas queue to more quickly start displaying the
# image/info screen when music stops but doing a dry start should be fast enough in most cases
