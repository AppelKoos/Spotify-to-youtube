import os
import json
import base64
from datetime import datetime
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
    with open('run_log.txt', 'a') as log:
        log.write('######################################################')
        log.write(f'{datetime.now()} #### Fetching access token...\n')

        try:
            __result = post("https://accounts.spotify.com/api/token", headers=__headers, data=__data)
            __token = json.loads(__result.content)["access_token"]
            log.write(f'{datetime.now()} #### Token fetched\n')
        except Exception as e:
            log.write(f'{datetime.now()} #### Token fetch failed with: {e}\n')
            raise e

    return __token


def get_spotify_playlist(playlist_id: str, token: str):
    """
    uses the spotify playlist id to generate a list with the playlist name and all the tracks
    list ex. ['PLAYLIST_NAME', 'ARTIST - TRACKNAME', 'ARTIST1, ARTIST2 - TRACKNAME']...

    :param playlist_id: spotify playlist id
    :param token: spotify auth token
    :return: list with spotify playlist name and tracks
    """

    with open('run_log.txt', 'a') as log:
        log.write('######################################################')
        log.write(f'{datetime.now()} #### Fetching spotify playlist...\n')

        __fields_url = 'fields=name%2Ctracks.items%28track.artists%28name%29%2C+track.name%29'
        try:
            __result = get(f"https://api.spotify.com/v1/playlists/{playlist_id}?{__fields_url}",
                           headers=get_spotify_auth_header(token))
            __json_result = json.loads(__result.content)
            __playlist = [__json_result['name']]
        except Exception as e:
            log.write(f'{datetime.now()} #### Error with fetching results: {e}\n')
            log.write(f'{datetime.now()} #### {__result}')
            raise e

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

        log.write(f'{datetime.now()} #### Playlist data fetched\n')
        log.write(f'{datetime.now()} #### Fetching Playlist tracks...\n')
        try:
            for _trackitm in __json_result['tracks']['items']:
                __playlist.append(f"{build_artist_names(_trackitm['track']['artists'])} - {_trackitm['track']['name']}")
        except Exception as e:
            log.write(f'{datetime.now()} #### Error with fetching track: {e}\n')

        log.write(f'{datetime.now()} #### All tracks added\n')
        log.write(f'{datetime.now()} #### Spotify playlist details\n')
        log.write(f'##### Playlist name ######\n')
        log.write(f'{__playlist[0]}\n')
        log.write(f'##### Playlist tracks #####\n')
        for _ in __playlist[1:]:
            log.write(f'{_}\n')

    return __playlist


def create_yt_playlist(spotify_playlist: list):
    video_ids = []
    empty_ids = []
    with open('run_log.txt', 'a') as log:
        log.write('######################################################')
        log.write(f'{datetime.now()} #### Fetching YT oauth file...\n')
        try:
            ytmusic = YTMusic(os.getenv('OAUTH_FILE'))
        except Exception as e:
            log.write(f'{datetime.now()} #### Failed creating instance: {e}...\n')
            raise e

        log.write(f'{datetime.now()} #### Instance created\n')
        log.write(f'{datetime.now()} #### {spotify_playlist[0]} #### Creating YouTube playlist...\n')

        for _track in spotify_playlist[1:]:
            yt_tracks = ytmusic.search(_track, filter='songs', limit=1)
            _i = ''
            for _ in yt_tracks:
                try:
                    _i = _['videoId']
                    video_ids.append(_i)
                    log.write(f'#### {spotify_playlist[0]} #### {_track} added with {_["videoId"]}\n')
                    break
                except KeyError:
                    _i = ''
                    log.write(f'{datetime.now()} #### ----KEY ERROR: {_track}----\n')
                    log.write(f'{datetime.now()} #### Retrying with another result...\n')
                    pass
                finally:
                    if _i == '':
                        empty_ids.append(_track)

        ytmusic.create_playlist(title=spotify_playlist[0],
                                description='',
                                privacy_status='PRIVATE',
                                video_ids=video_ids)

        log.write(f'{datetime.now()} #### Youtube playlist created!\n')
        if len(empty_ids) > 0:
            log.write(f'{datetime.now()} #### {spotify_playlist[0]} #### '
                      f"The following songs could not be found and weren't added, manual search is required\n")
            for _ in empty_ids:
                log.write(f'#### {spotify_playlist[0]} #### {_}')


def main():
    load_dotenv()
    playlist_ids = []

    print(f'{datetime.now()} Starting script')
    with open('run_log.txt', 'w') as log:
        log.write(f'{datetime.now()} #### Starting playlist migration\n')
        log.write(f'{datetime.now()} #### Fetching ids from txt file...\n')

        try:
            with open('migration_list.txt', 'r') as m_list:
                for id in m_list:
                    _ = id[:-2] + id[-2:].replace('\n', '')
                    playlist_ids.append(_)
        except Exception as e:
            log.write(f'{datetime.now()} #### Error fetching ids from txt file: {e}\n')
        finally:
            if len(playlist_ids) == 0:
                log.write(f'{datetime.now()} #### No spotify playlist ids found, stopping...\n')
                raise Exception('Empty spotify playlist ids')
        log.write(f'{datetime.now()} #### Spotify playlist ids fetched from txt file\n')

    with open('run_log.txt', 'a') as log:
        log.write(f'{datetime.now()} #### Fetching spotify secrets...\n')
        try:
            client_id = os.getenv('CLIENT_ID')
            client_secret = os.getenv('CLIENT_SECRET')
        except Exception as e:
            log.write(f'{datetime.now()} #### Secret fetch failed with, Exception raised: {e}\n')
            raise e

        log.write(f'{datetime.now()} #### Spotify secrets fetched\n')

    token = get_spotify_token(client_id, client_secret)

    for id in playlist_ids:
        playlist = get_spotify_playlist(id, token)
        create_yt_playlist(playlist)

    print(f'{datetime.now()} Script finished')


if __name__ == "__main__":
    main()
