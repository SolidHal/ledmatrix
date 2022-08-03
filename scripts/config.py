#!/usr/bin/env python3

from rgbmatrix import RGBMatrix, RGBMatrixOptions

brightness = 50
luminance_correct=True
refresh_rate=90

# Global config to be used for all scripts
def Matrix():
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
