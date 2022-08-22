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


    framedata1 = []
    framedata2 = []


    offscreen_canvas = cfg.matrix.CreateFrameCanvas()
    faulthandler.enable()

    def prepare(offscreen_canvas):
        framedata = []
        for n in range(0,100):
            offscreen_canvas.SetImage(image)
            data = offscreen_canvas.Serialize()
            framedata.append(data)

        return framedata

    def show(offscreen_canvas, framedata):
        for data in framedata:
            offscreen_canvas.Deserialize(data)
            offscreen_canvas = cfg.matrix.SwapOnVSync(offscreen_canvas)

    print("Displaying canvases")
    try:
        print("Press CTRL-C to stop.")


        # offscreen_canvas = cfg.matrix.CreateFrameCanvas()
        # offscreen_canvas.SetImage(image)
        # data = offscreen_canvas.Serialize()
        # canvas = cfg.matrix.CreateFrameCanvas()
        # canvas.Deserialize(data)

        # cfg.matrix.SwapOnVSync(canvas)
        # while(True):
        #     time.sleep(100)


        framedata1 = prepare(offscreen_canvas)
        show(offscreen_canvas ,framedata1)
        framedata2 = prepare(offscreen_canvas)
        show(offscreen_canvas, framedata2)
        framedata1 = prepare(offscreen_canvas)
        show(offscreen_canvas ,framedata1)
        framedata2 = prepare(offscreen_canvas)
        show(offscreen_canvas, framedata2)
        framedata1 = prepare(offscreen_canvas)
        show(offscreen_canvas ,framedata1)
        framedata2 = prepare(offscreen_canvas)
        show(offscreen_canvas, framedata2)
        framedata1 = prepare(offscreen_canvas)
        show(offscreen_canvas ,framedata1)
        framedata2 = prepare(offscreen_canvas)
        show(offscreen_canvas, framedata2)



    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Require an image argument")
    else:
        image_file = sys.argv[1]
    image_viewer(image_file)
