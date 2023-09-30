from config import CLIENT_ID, CLIENT_SECRET
from auth_encoding_process import auth_encoding_process
import requests
import json

class API_URIs():
    def __init__(self):
        self.ur_mom = None
    def get_code(_scopes):
        return f"https://accounts.spotify.com/authorize?client_id=63d1854276c04b84a7480fd35791b178&response_type=code&redirect_uri=https://www.coolmathgames.com/&scope={_scopes}"
    def get_access_token(_code, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        Headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Authorization': f'Basic {auth_encoding_process(client_id, client_secret)}',
                   'Cookie': '__Host-device_id=AQDFsVYDXTOuSl1CKj0HMR0IXwE5xVo9UXPAKtp4ZNMcs4QHi4XlRjtu5aexUbhKpptp5DwwlB9qPv1-StXb_SyFiGKXEnPoYb0'}
        return {"URL":f"https://accounts.spotify.com/api/token?grant_type=authorization_code&code={_code}&redirect_uri=https://www.coolmathgames.com/",
                "Headers": Headers,
                "Payload": {}}
    def refresh_access_token(_refresh_token, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        Headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'grant_type': 'refresh_token',
                   'refresh_token': f'{_refresh_token}',
                   'Authorization': f'Basic {auth_encoding_process(client_id, client_secret)}',
                   'Cookie': '__Host-device_id=AQDFsVYDXTOuSl1CKj0HMR0IXwE5xVo9UXPAKtp4ZNMcs4QHi4XlRjtu5aexUbhKpptp5DwwlB9qPv1-StXb_SyFiGKXEnPoYb0; sp_tr=false'}
        return {"URL":f"https://accounts.spotify.com/api/token?grant_type=refresh_token&refresh_token={_refresh_token}",
                "Headers": Headers,
                "Payload": {}}
    def get_personal_information(_user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Scopes = 'user-read-email user-read-private'
        return {"URL":f"https://api.spotify.com/v1/me",
                "Headers": Headers,
                "Payload": {}}
    def get_user_playlists(_user_id, _user_bearer, _limit=50, _offset=0):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/users/{_user_id}/playlists?limit={_limit}&offset={_offset}",
                "Headers": Headers,
                "Payload": {}}
    def get_playlist_items(_playlist_id, _user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/playlists/{_playlist_id}/tracks",
                "Headers": Headers,
                "Payload": {}}
    def get_top_fifteen_artists(_user_bearer, _time_range="medium_term", _limit=20):
        Headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/me/top/artists?time_range=long_term",
                "Headers": Headers,
                "Payload": ""}
    def get_similar_artists(_artist_id, _user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/artists/{_artist_id}/related-artists",
                "Headers": Headers,
                "Payload": {}}
    def create_playlist(_user_id, _user_bearer, _playlist_name='Why u no choose a name?', _playlist_description=None):
        Headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/users/{_user_id}/playlists",
                "Headers": Headers,
                "Payload": json.dumps({"name": f"{_playlist_name}",
                                       "description": f"{_playlist_description}",
                                       "public": False})}
    def get_artist_top_track(_artist_id, _user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        return {"URL": f"https://api.spotify.com/v1/artists/{_artist_id}/top-tracks?market=US",
                "Headers": Headers,
                "Payload": {}}
    def put_items_in_playlist(_user_id, _user_bearer, _playlist_id, _song_uri):
        Headers = {'Authorization': f'Bearer {_user_bearer}',
                   'content-type': 'application/json'}
        return {"URL": f"https://api.spotify.com/v1/users/{_user_id}/playlists/{_playlist_id}/tracks",
                "Headers": Headers,
                "Payload": json.dumps({"uris": _song_uri})}