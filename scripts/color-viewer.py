#!/usr/bin/env python3
import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions
import config

def color_viewer():
    matrix = config.Matrix()

    try:
        print("Press CTRL-C to stop.")
        matrix.Fill(155,155,155)
        while(True):
            time.sleep(1000)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    color_viewer()
