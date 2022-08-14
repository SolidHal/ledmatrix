import asyncio
import os
import json
import logging
import requests

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

async def currently_playing(cfg):
    try:
        loop = asyncio.get_event_loop()
        playing = await loop.run_in_executor(None,  cfg.spotify_api.currently_playing)
    except (requests.exceptions.HTTPError, spotipy.exceptions.SpotifyException, requests.exceptions.ReadTimeout) as e:
        # refresh in case our token expired. Next call will then succeed
        cfg.spotify_api = start_api(cfg.spotify_api_username)
        logging.error(f"failed to get currently playing from spotify {e}")
        return None

    return playing

def currently_playing_song_name(cfg, playing):
    if playing:
        if playing.get("is_playing", None):
            return playing.get("item", {}).get("name", None)
    return None


async def currently_playing_album_art(cfg, playing):

    async def download_album_art(url):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.read()

    if playing is None:
        return None

    if playing.get("is_playing", None):
        if playing.get("currently_playing_type", None) == "track":
            images = playing.get("item", {}).get("album", {}).get("images", [])
            for image in images:
                if image.get("height") == 300:
                    return await download_album_art(image.get("url"))

    return None

async def currently_playing_device(cfg):
    try:
        loop = asyncio.get_event_loop()
        devices = await loop.run_in_executor(None,  cfg.spotify_api.devices)

    except (requests.exceptions.HTTPError, spotipy.exceptions.SpotifyException, requests.exceptions.ReadTimeout) as e:
        # refresh in case our token expired. Next call will then succeed
        cfg.spotify_api = start_api(cfg.spotify_api_username)
        logging.error(f"failed to get currently playing device info from spotify {e}")
        return None

    for device in devices.get("devices", []):
        if device.get("is_active", None):
            return device.get("name")

    return None
