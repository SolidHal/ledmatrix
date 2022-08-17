#!/usr/bin/env python3

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
    options.pwm_bits=6 # limit color space <1..11> 11 is default
    options.pwm_lsb_nanoseconds=130
    options.limit_refresh_rate_hz=refresh_rate

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
    spotify_api_excluded_devices = []

    ## Config Global Storage ##
    # weather overlay storage
    weather_updated_epoch = None
    cached_weather = None

    # todo overlay storage


    # RGBMatrix storage
    matrix = Matrix(refresh_rate, brightness, luminance_correct)
