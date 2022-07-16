


library:
https://github.com/hzeller/rpi-rgb-led-matrix


notes on python performance from library:
```
If you can prepare the animation you want to show, then you can either prepare images and then use the much faster call to SetImage(), or can fill entire offscreen-frames (create with CreateFrameCanvas()) and then swap with SwapOnVSync() (this is the fastest method).
```
