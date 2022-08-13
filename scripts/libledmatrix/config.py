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

    # options.pixel_mapper_config="U-mapper"
    # options.pixel_mapper_config="U-mapper;Rotate:180"
    # options.show_refresh_rate=True
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
    brightness = 100
    luminance_correct=True
    refresh_rate=90

    # display options
    fps = 8 # fps for animations on the display
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

    ## Config Global Storage ##
    # weather overlay storage
    weather_updated_epoch = None
    cached_weather = None

    # todo overlay storage


    # RGBMatrix storage
    matrix = Matrix(refresh_rate, brightness, luminance_correct)
