#!/usr/bin/env python3

import sys
import time
import logging
from PIL import Image, ImageDraw, ImageFont, GifImagePlugin

from . import weather, image_color, epoch, calendar_dav
#TODO importing config before other modules breaks imports for some reason
from . import config

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
    # place in top right corner
    im_copy.paste(overlay_im, (0,0))
    return im_copy


async def overlay_weather(im, cfg, colors, target_epoch):
    if not cfg.weather_api_key or not cfg.weather_api_lat or not cfg.weather_api_lon:
        raise RuntimeError("api key and city must be set")

    if cfg.weather_updated_epoch is None:
        cfg.weather_updated_epoch = target_epoch

    # update if we either don't have the weather info, or 5 epochs have passed
    if cfg.cached_weather is None or target_epoch > epoch.delta(cfg.weather_updated_epoch, 5):
        cur_weather = await weather.get_weather(cfg.weather_api_key, cfg.weather_api_lat, cfg.weather_api_lon)
        # else we failed to get a weather update. Just wait for the next one and use the cached weather instead
        if cur_weather is not None:
            logging.info(f"updated weather: {cur_weather}")
            cfg.cached_weather = cur_weather

    # if we failed to get weather, and don't have any cached, just return and wait for the next epoch
    if cfg.cached_weather is None:
        return im

    icon = weather.to_icon(cfg.cached_weather)
    temp = weather.to_temp(cfg.cached_weather)

    rect_height = 14
    rect_width = 28
    weather_font = ImageFont.load("libledmatrix/pillow-fonts/weather-12.pil")
    font = ImageFont.load("libledmatrix/pillow-fonts/helvR12.pil")
    overlay_im = Image.new("RGB", (rect_width+1, rect_height+1))
    draw = ImageDraw.Draw(overlay_im)
    # use the 1st and 2nd most dominant colors for the rectangle & frame
    draw.rectangle((0, 0, rect_width, rect_height), fill=colors[0], outline=colors[1])
    draw.text((1,0), temp, font=font, fill=image_color.contrast_color_bw(colors[0]))
    draw.text((15,2), icon, font=weather_font, fill=image_color.contrast_color_bw(colors[0]))

    im_copy = im.copy()
    # place in top left corner
    im_copy.paste(overlay_im, (127 - rect_width,0))
    return im_copy



# overlay a todos list from a caldav server
# displays "due" todos
async def overlay_todos(im, cfg, colors, target_epoch):
    #TODO check if the cfg vals are set
    # if not cfg.weather_api_key or not cfg.weather_api_lat or not cfg.weather_api_lon:
    #     raise RuntimeError("api key and city must be set")
    todos = await calendar_dav.get_todos(cfg.todo_caldav_url, cfg.todo_caldav_username, cfg.todo_caldav_password)
    #TODO get the items due today, display those first
    # then if there are more past due items, display those next

    return im

# overlays a calendar events list for the day
async def overlay_calendar(im, cfg, colors, target_epoch):
    #TODO check if the cfg vals are set
    # if not cfg.weather_api_key or not cfg.weather_api_lat or not cfg.weather_api_lon:
    #     raise RuntimeError("api key and city must be set")
    return im
