import os
import spotipy



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
