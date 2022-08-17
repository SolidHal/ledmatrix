import asyncio
import os
import json
import logging
import requests
import time

import httpx
import spotipy
import spotipy.util as util
from json.decoder import JSONDecodeError



def start_api(username):
    """
    the following must be set:
    SPOTIPY_CLIENT_ID
    SPOTIPY_CLIENT_SECRET
    SPOTIPY_REDIRECT_URI
    """
    # check for env vars
    os.environ["SPOTIPY_CLIENT_ID"]
    os.environ["SPOTIPY_CLIENT_SECRET"]
    os.environ["SPOTIPY_REDIRECT_URI"]
    scope = 'user-read-private user-read-playback-state user-modify-playback-state user-library-read playlist-modify-private playlist-modify-public'

    try:
        token = util.prompt_for_user_token(username, scope)
    except (AttributeError, JSONDecodeError):
        os.remove(f".cache-{username}")
        token = util.prompt_for_user_token(username, scope)

    spotify_api = spotipy.Spotify(auth=token, retries=10, status_retries=10, backoff_factor=1.5)

    return spotify_api

def currently_playing(api):
    playing = api.currently_playing()
    return playing

def currently_playing_song_name(playing):
    if playing:
        if playing.get("is_playing", None):
            return playing.get("item", {}).get("name", None)
    return None


def currently_playing_album_art(playing):

    def download_album_art(url):
        with httpx.Client() as client:
            response = client.get(url)
            return response.read()

    if playing is None:
        return None

    if playing.get("is_playing", None):
        if playing.get("currently_playing_type", None) == "track":
            images = playing.get("item", {}).get("album", {}).get("images", [])
            for image in images:
                if image.get("height") == 300:
                    return download_album_art(image.get("url"))

    return None

def currently_playing_device(api):
    devices = api.devices()

    for device in devices.get("devices", []):
        if device.get("is_active", None):
            return device.get("name")

    return None


def spotify_thread(username, excluded_devices, art_queue, spotify_thread_event):
    def alert_main(song_name=None, album_art=None):
        if album_art is None or device is None:
            logging.info(f"Informing main thread that nothing is playing")
            # alert thread that nothing is playing
            if spotify_thread_event.is_set():
                spotify_thread_event.clear()
        else:
            logging.info(f"Informing main thread that {song_name} is playing")
            # alert thread that something is playing
            art_queue.put(album_art)
            if not spotify_thread_event.is_set():
                spotify_thread_event.set()

    api = start_api(username)
    last_song_name = None

    while(True):
        try:
            playing = currently_playing(api)
            device = currently_playing_device(api)

        except (requests.exceptions.HTTPError, spotipy.exceptions.SpotifyException, requests.exceptions.ReadTimeout) as e:
            # refresh in case our token expired. Next call will then succeed
            api = start_api(username)
            logging.error(f"failed to get currently playing device info from spotify {e}")

        else:
            song_name = currently_playing_song_name(playing)
            album_art = currently_playing_album_art(playing)
            if device in excluded_devices:
                # act like nothing is playing
                last_song_name = None
                alert_main()

            elif last_song_name == song_name:
                # song is still playing nothing to do
                pass

            elif album_art is None or device is None:
                # either failed to get some info, or no longer playing
                last_song_name = None
                alert_main()
            else:
                # we have song info to alert the main thread about
                last_song_name = song_name
                alert_main(song_name, album_art)

        # don't poll too aggressively
        time.sleep(3)

