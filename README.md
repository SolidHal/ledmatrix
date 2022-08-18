# ledmatrix

a set of tools to work with a rpi + led matricies

- scripts/libledmatrix : a set of modules to support the various scripts
- scripts/libledmatrix/config.py : configuration file for the scripts/libledmatrix
- scripts/image-viewer.py : a simple script to display a static image on the matrix
- scripts/gif-viewer.py : a script to efficiently pre-process and display a gif on the matrix
- scripts/gif-info.py : a script to efficiently pre-process and display a gif along with various information overlays on the matrix
- scripts/main-viewer.py : display gifs/still images along with various information overlaid. Switches to spotify album art when music is playing

requirements:

RGBMatrix python bindings:
https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/bindings/python/README.md

```
pip install click caldav lxml httpx icalendar spotipy
apt install libxslt-dev
```

## Setup
- write a ledmatrix-env.sh
- source ledmatrix-env.sh
- call setup-spotify.py
- call main-viewer.py


can be autostarted on dietpi using:
```
/var/lib/dietpi/dietpi-autostart/custom.sh
```
