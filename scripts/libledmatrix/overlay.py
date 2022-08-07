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

#TODO add todo list overlay

async def apply_overlays(frame, overlays=[], overlay_args=()):
    # apply any provided overlays
    # overlay_args is a tuple of arguments to pass to the overlay functions
    overlaid_im = frame
    for overlay in overlays:
        overlaid_im = await overlay(overlaid_im, *overlay_args)

    return overlaid_im


async def overlay_clock(im, cfg, colors, target_epoch):
    if not len(colors) >= 3:
        raise ValueError("Need at least 3 colors to overlay a clock")

    rect_height = 14
    rect_width = 32
    font = ImageFont.load("libledmatrix/pillow-fonts/helvR12.pil")
    overlay_im = Image.new("RGB", (rect_width+1, rect_height+1))
    draw = ImageDraw.Draw(overlay_im)
    # use the 1st and 2nd most dominant colors for the rectangle & frame
    draw.rectangle((0, 0, rect_width, rect_height), fill=colors[0], outline=colors[1])
    time_str = time.strftime("%I:%M", time.localtime(target_epoch.seconds()))
    # use a color we know will contrast wtih the rectangle fill color for the time
    draw.text((1,0), time_str, font=font, fill=image_color.contrast_color_bw(colors[0]))
    im_copy = im.copy()
    im_copy.paste(overlay_im, (0,0))
    return im_copy


async def overlay_weather(im, cfg, colors, target_epoch):
    if not cfg.weather_api_key or not cfg.weather_api_lat_lon:
        raise RuntimeError("api key and city must be set")

    if cfg.weather_updated_epoch == None:
        cfg.weather_updated_epoch = target_epoch

    # update if we either don't have the weather info, or 60 epochs have passed
    if cfg.cached_weather is None or target_epoch > epoch.delta(cfg.weather_updated_epoch, 60):
        exclude = "minutely,hourly,alerts"
        #TODO add configurable units
        units="imperial"
        URL = f"https://api.openweathermap.org/data/2.5/weather?lat={cfg.weather_api_lat_lon[0]}&lon={cfg.weather_api_lat_lon[1]}&units={units}&appid={cfg.weather_api_key}"
        data = None
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            if response.status_code != 200:
                logging.info(f"Failed to get weather info: {response}, api_key = {cfg.weather_api_key}, lat = {cfg.weather_api_lat_lon[0]}, lon = {cfg.weather_api_lat_lon[1]}")
                return im
            data = response.json()

        #TODO get icon set for the different weather states
        weather = data["weather"]
        # print(data["weather"])
        #TODO put the temp on the overlay
        temp = data["main"]["temp"]
        print(temp)

        cfg.cached_weather = {"temp": temp}


    # rect_height = 14
    # rect_width = 32
    rect_height = 128
    rect_width = 128
    weather_font = ImageFont.load("libledmatrix/pillow-fonts/weather-12.pil")
    font = ImageFont.load("libledmatrix/pillow-fonts/helvR12.pil")
    overlay_im = Image.new("RGB", (rect_width+1, rect_height+1))
    draw = ImageDraw.Draw(overlay_im)
    # use the 1st and 2nd most dominant colors for the rectangle & frame
    draw.rectangle((0, 0, rect_width, rect_height), fill=colors[0], outline=colors[1])
    #TODO put each weather glyph next to the temp and make sure they are vertically and horizontally spaced property
    draw.text((1,0), "89", font=font, fill=image_color.contrast_color_bw(colors[0]))
    draw.text((16,0), "ABCDEF", font=weather_font, fill=image_color.contrast_color_bw(colors[0]))
    draw.text((1,30), "GHIJK", font=weather_font, fill=image_color.contrast_color_bw(colors[0]))


    im_copy = im.copy()
    im_copy.paste(overlay_im, (60,0))
    return im_copy

