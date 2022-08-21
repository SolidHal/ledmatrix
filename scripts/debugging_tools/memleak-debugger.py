#!/usr/bin/env python3
import time
import sys
import faulthandler

from memory_profiler import profile

from rgbmatrix import RGBMatrix
from PIL import Image
from libledmatrix import display, image_color, image_processing
from libledmatrix import config


@profile
def image_viewer(image_file):

    pil_image = Image.open(image_file)
    cfg = config.Config()
    image = image_processing.centerfit_image(pil_image, cfg.matrix, False)[0]
    pil_image.close()


    canvases = []
    canvases2 = []

    faulthandler.enable()
    def prepare_and_show(canva, cfg):
        for va in canva:
            cfg.matrix.DeleteFrameCanvas(va)

        canva = []
        for n in range(0,100):
            c = cfg.matrix.CreateFrameCanvas()
            c.SetImage(image)
            canva.append(c)

        for c in canva:
            cfg.matrix.SwapOnVSync(c)

        return canva

    print(f"Created {len(canvases)} canvases")
    # time.sleep(30)

    print("Displaying canvases")
    try:
        print("Press CTRL-C to stop.")

        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)
        canvases = prepare_and_show(canvases, cfg)
        canvases2 = prepare_and_show(canvases2, cfg)


    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    image_viewer(image_file)
