#!/usr/bin/env python3

import click
import os
import logging
import time

from libledmatrix import spotify

logging.basicConfig(level=logging.INFO,)


@click.command()
@click.option('--spotify_api_username', required=True,
              default=lambda: os.environ.get('SPOTIFY_API_USERNAME', ''),
              show_default='SPOTIFY_API_USERNAME envvar')
def main(spotify_api_username):
    api = spotify.start_api(spotify_api_username)

    while(True):
        time.sleep(5)
        api.currently_playing()
        api.devices()






if __name__ == "__main__":
    main()
