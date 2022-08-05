#!/usr/bin/env python3
import time
import httpx
import json
import logging
from PIL import Image, ImageDraw, ImageFont, GifImagePlugin

from libledmatrix import config, epoch, image_color

## Overlay args:
# - im : the image to place the overlay on
# - cfg : the libledmatrix.config.Config() object to get global information from
# - colors : the colors to use for the overlay
# - epoch : the Epoch() to create this overlay for, stored in minutes

async def apply_overlays(frame, overlays=[], overlay_args=()):
    # apply any provided overlays
    # overlay_args is a tuple of arguments to pass to the overlay functions
    overlaid_im = frame
    for overlay in overlays:
        overlaid_im = await overlay(overlaid_im, *overlay_args)

    return overlaid_im


async def overlay_clock(im, cfg, colors, epoch):
    if not len(colors) >= 3:
        raise ValueError("Need at least 3 colors to overlay a clock")

    rect_height = 14
    rect_width = 32
    font = ImageFont.load("libledmatrix/pillow-fonts/helvR12.pil")
    overlay_im = Image.new("RGB", (rect_width+1, rect_height+1))
    draw = ImageDraw.Draw(overlay_im)
    # use the 1st and 2nd most dominant colors for the rectangle & frame
    draw.rectangle((0, 0, rect_width, rect_height), fill=colors[0], outline=colors[1])
    time_str = time.strftime("%I:%M", time.localtime(epoch.seconds()))
    # use a color we know will contrast wtih the rectangle fill color for the time
    draw.text((1,0), time_str, font=font, fill=image_color.contrast_color_bw(colors[0]))
    im_copy = im.copy()
    im_copy.paste(overlay_im, (0,0))
    return im_copy


async def overlay_weather(im, cfg, colors, epoch):
    if not cfg.weather_api_key or not cfg.weather_api_lat_lon:
        raise RuntimeError("api key and city must be set")

    # update if we either don't have the weather info, or 60 epochs have passed
    if cfg.cached_weather is None or epoch > epoch.delta(cfg.updated_epoch, 60):
        exclude = "minutely,hourly,alerts"
        URL = f"https://api.openweathermap.org/data/3.0/onecall?lat={cfg.weather_api_lat_lon[0]}&lon={cfg.weather_api_lat_lon[0]}&exclude={exclude}&appid={cfg.weather_api_key}"
        data = None
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            if response.status_code != 200:
                logging.info(f"Failed to get weather info: {response}, api_key = {cfg.weather_api_key}, lat = {cfg.weather_api_lat_lon[0]}, lon = {cfg.weather_api_lat_lon[1]}")
                return im
            data = reponse.json()

        temp = data["main"]["temp"]
        weather = data["main"]["weather"]
        logging.info(f"temp = {temp}, weather = {weather}")

        



    im_copy = im.copy()
    # im_copy.paste(overlay_im, (0,0))
    return im_copy

