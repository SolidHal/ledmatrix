#!/usr/bin/env python3
import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions

def Matrix(refresh_rate, brightness, luminance_correct):
    options = RGBMatrixOptions()
    # Configuration for the matrix
    options.rows = 64
    options.cols = 64
    options.chain_length = 2
    options.parallel = 2
    options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'

    options.show_refresh_rate=False

    # give us a chance to maintain a consistent frame rate without flickering
    # options.pwm_lsb_nanoseconds=90
    # options.scan_mode=1
    # options.pwm_dither_bits=1

    # options.pwm_bits=8 # limit color space <1..11> 11 is default
    # This is required when processing + displaying at the same time

    options.pwm_lsb_nanoseconds=130
    options.limit_refresh_rate_hz=refresh_rate

    options.drop_privileges = False

    matrix = RGBMatrix(options = options)
    matrix.brightness = brightness
    matrix.luminanceCorrect = luminance_correct

    # print(f"matrix width = {matrix.width}")
    # print(f"matrix height = {matrix.height}")

    return matrix


# Global config to be used for all scripts
class Config():
    ## Options ##
    # matrix options
    brightness = 80
    luminance_correct=True
    # anything below 100 looks flickery
    refresh_rate=100

    # display options
    fps = 6 # fps for animations on the display
    framerate_fraction = refresh_rate / fps
    epochs_per_frameset = 4 # number of epochs to show an image/gif for

    # image_processing options
    max_frames = 360 # maximum number of frames in a a gif

    # weather overlay options
    weather_api_key = None
    weather_api_lat = None
    weather_api_lon = None

    # todo overlay options
    todo_caldav_url = None
    todo_caldav_username = None
    todo_caldav_password = None

    # spotify options
    spotify_api_username = None
    spotify_api_token_cache_path = None
    spotify_api_excluded_devices = []

    # adaptive brightness options

    # before sunrise, after sunset set the display to this brightness
    nighttime_brightness = 20
    if nighttime_brightness < 1:
        raise RuntimeError(f"nighttime_brightness {nighttime_brightness} cannot be < 1")

    # time before sunset, after sunrise to partially dim the display
    partial_delta = datetime.timedelta(hours = 1)
    partial_brightness = brightness - 30
    if partial_brightness < 1:
        raise RuntimeError(f"partial_brightness {partial_brightness} cannot be < 1")


    ## Config Global Storage ##
    # weather overlay storage
    weather_updated_epoch = None
    cached_weather = None

    # todo overlay storage


    # RGBMatrix storage
    matrix = Matrix(refresh_rate, brightness, luminance_correct)
