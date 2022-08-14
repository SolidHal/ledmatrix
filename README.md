# ledmatrix

a set of tools to work with a rpi + led matricies

- scripts/libledmatrix : a set of modules to support the various scripts
- scripts/libledmatrix/config.py : configuration file for the scripts/libledmatrix
- scripts/image-viewer.py : a simple script to display a static image on the matrix
- scripts/gif-viewer.py : a script to efficiently pre-process and display a gif on the matrix
- scripts/gif-info.py : a scripts to efficiently pre-process and display a gif along with various information overlays on the matrix

requirements:

RGBMatrix python bindings:
https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/bindings/python/README.md

```
pip install click caldav lxml httpx icalendar
apt install libxslt-dev
```


TODO:
- display weather
- display spotify album art when playing
- display images
- pixelart gifs (aesthetic rain)?


## Setup
- write a ledmatrix-env.sh
- source ledmatrix-env.sh
- call setup-spotify.py
- call main-viewer.py
