#!/usr/bin/env python3
import time
import sys
import os

import click
from PIL import Image, GifImagePlugin
from rgbmatrix import RGBMatrix, RGBMatrixOptions

from libledmatrix import display, image_color, image_processing, config

#TODO:
# add weather overlay to animated_overlaid

#TODO:
# add spotify current song album art static_overlaid impl


# compute the frames for the current minute, and the next minute
# show the current minute
# when time moves forward, show the next minute and start computing
# frames for the next minute

def run(image_file, weather_api_key, weather_api_lat, weather_api_lon):
    cfg = config.Config()
    cfg.weather_api_key = weather_api_key
    cfg.weather_api_lat_lon = (weather_api_lat, weather_api_lon)

    gif = Image.open(image_file)
    # get the dominant colors before converting the gif to avoid
    # the padding from altering which colors are dominant
    dom_colors = image_color.dominant_colors_gif(gif)
    fill_matrix = False
    # pre process our frames so we can dedicate our resources to displaying them later
    frames = image_processing.centerfit_gif(gif, cfg.matrix, fill_matrix)
    # Close the gif file to save memory now that we have copied out all of the frames
    print(f"Gif has {gif.n_frames} frames")
    gif.close()

    #TODO provide way load/store preprocessed gifs on disk
    try:
        print("Press CTRL-C to stop.")
        display.animated_overlaid(cfg, frames, dom_colors)

    except KeyboardInterrupt:
        sys.exit(0)

@click.command()
@click.option("--image", type=str, required=True, help="path to the gif to display")
@click.option('--weather_api_key', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_KEY', ''),
              show_default='OPENWEATHER_API_KEY envvar')
@click.option('--weather_api_lat', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_LAT', ''),
              show_default='OPENWEATHER_API_LAT envvar')
@click.option('--weather_api_lon', required=True,
              default=lambda: os.environ.get('OPENWEATHER_API_LON', ''),
              show_default='OPENWEATHER_API_LON envvar')
def main(image, weather_api_key, weather_api_lat, weather_api_lon):
    run(image, weather_api_key, weather_api_lat, weather_api_lon)

if __name__ == "__main__":
    main()
