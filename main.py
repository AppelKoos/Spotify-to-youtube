import os
import json
import base64
from ytmusicapi import YTMusic
from dotenv import load_dotenv
from requests import post, get


def get_spotify_auth_header(token):
    return {"Authorization": "Bearer " + token}


def get_spotify_token(client_id, client_secret):
    __auth_string = client_id + ":" + client_secret
    __auth_base64 = str(base64.b64encode(__auth_string.encode("utf-8")), "utf-8")

    __headers = {
        "Authorization": "Basic " + __auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    __data = {"grant_type": "client_credentials"}
    __result = post("https://accounts.spotify.com/api/token", headers=__headers, data=__data)

    return json.loads(__result.content)["access_token"]


def get_spotify_playlist(playlist_id: str, token: str):
    """
    uses the spotify playlist id to generate a list with the playlist name and all the tracks
    list ex. ['PLAYLIST_NAME', 'ARTIST - TRACKNAME', 'ARTIST1, ARTIST2 - TRACKNAME']...

    :param playlist_id: spotify playlist id
    :param token: spotify auth token
    :return: list with spotify playlist name and tracks
    """

    __fields_url = 'fields=name%2Ctracks.items%28track.artists%28name%29%2C+track.name%29'
    __result = get(f"https://api.spotify.com/v1/playlists/{playlist_id}?{__fields_url}",
                   headers=get_spotify_auth_header(token))
    __json_result = json.loads(__result.content)

    __playlist = [__json_result['name']]

    def build_artist_names(track_artists):
        _out = ''
        if len(track_artists) == 1:
            _out = track_artists[0]['name']
        else:
            _list_artists = []
            for _a in track_artists:
                _list_artists.append(_a['name'])
            _artisti = iter(_list_artists)
            _artist = str(next(_artisti))
            for _a in _artisti:
                _artist += ', ' + _a
            _out += _artist

        return _out

    for _trackitm in __json_result['tracks']['items']:
        __playlist.append(f"{build_artist_names(_trackitm['track']['artists'])} - {_trackitm['track']['name']}")

    return __playlist


def main():
    load_dotenv()
    # ytmusic = YTMusic(os.getenv('OAUTH_FILE'))

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    print(client_id, client_secret)
    token = get_spotify_token(client_id, client_secret)
    print(token)

    playlist = get_spotify_playlist("37i9dQZF1EQn4jwNIohw50", token)

    print("##### Playlist name ######")
    print(playlist[0])
    print("##### Playlist tracks #####")
    for _ in playlist[1:]:
        print(_)


if __name__ == "__main__":
    main()
