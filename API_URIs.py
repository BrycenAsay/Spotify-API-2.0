from config import CLIENT_ID, CLIENT_SECRET
from auth_encoding_process import auth_encoding_process
import time
import os
import requests
import json

def error_handling(message, _url, _headers, _payload):
    #error handling in case an API response isn't of code 200
    if 'error' in message:
        try:
            #error handling for rate limit error
            if message['error']['status'] == 429:
                print('THERE WAS A RATE LIMIT ERROR!')
                while 'error' in message:
                    time.sleep(900)
                    message = requests.request("GET", _url, headers=_headers, data=_payload)
                return message.json()
            # default error if message in the response is actually provided
            print(f"There was a {message['error']['status']} error boiii :P --> \"{message['error']['message']}!\"")
        except:
            # default error if a message is not provided in response message
            print(f"There was an error boiii :P --> \"{message['error']}\"")
        quit()
    else:
        return message

def send_request(_url, _headers, _payload, is_post=False, is_get=False, is_put=False):
    if is_get:
        response = requests.request("GET", _url, headers=_headers, data=_payload)
    elif is_post:
        response = requests.request("POST", _url, headers=_headers, data=_payload)
    elif is_put:
        response = requests.request("PUT", _url, headers=_headers, data=_payload, timeout=10)
    else:
        return "ERROR! Please provide POST or GET request, or update code to handle requests outside of 'GET' and 'POST!'"
    
    if response.status_code == 429:
        while 'retry-after' in response.headers:
            time_to_sleep = int(response.headers['retry-after']) + 30
            for i in range(time_to_sleep):
                os.system('cls')
                print(f'F*** YOU SPOTIFY RATE LIMIT! YOU HAVE TO WAIT {time_to_sleep} STILL :((')
                time.sleep(1)
                time_to_sleep -= 1
            
    if is_get:
        response = requests.request("GET", _url, headers=_headers, data=_payload)
    elif is_post:
        response = requests.request("POST", _url, headers=_headers, data=_payload)
    elif is_put:
        response = requests.request("PUT", _url, headers=_headers, data=_payload, timeout=15)
    else:
        return "ERROR! Please provide POST or GET request, or update code to handle requests outside of 'GET' and 'POST!'"

    if (is_get) or (is_post):
        unclean_data = response.json()
        return error_handling(unclean_data, _url, _headers, _payload)

class API_URIs():
    def __init__(self):
        self.ur_mom = None
    def get_code(_scopes):
        return f"https://accounts.spotify.com/authorize?client_id=63d1854276c04b84a7480fd35791b178&response_type=code&redirect_uri=https://www.coolmathgames.com/&scope={_scopes}"
    
    def get_access_token(_code, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        Headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Authorization': f'Basic {auth_encoding_process(client_id, client_secret)}',
                   'Cookie': '__Host-device_id=AQDFsVYDXTOuSl1CKj0HMR0IXwE5xVo9UXPAKtp4ZNMcs4QHi4XlRjtu5aexUbhKpptp5DwwlB9qPv1-StXb_SyFiGKXEnPoYb0'}
        Url = f"https://accounts.spotify.com/api/token?grant_type=authorization_code&code={_code}&redirect_uri=https://www.coolmathgames.com/"
        Payload = {}
        return send_request(Url, Headers, Payload, is_post=True)
    
    def refresh_access_token(_refresh_token, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        Headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'grant_type': 'refresh_token',
                   'refresh_token': f'{_refresh_token}',
                   'Authorization': f'Basic {auth_encoding_process(client_id, client_secret)}',
                   'Cookie': '__Host-device_id=AQDFsVYDXTOuSl1CKj0HMR0IXwE5xVo9UXPAKtp4ZNMcs4QHi4XlRjtu5aexUbhKpptp5DwwlB9qPv1-StXb_SyFiGKXEnPoYb0; sp_tr=false'}
        Url = f"https://accounts.spotify.com/api/token?grant_type=refresh_token&refresh_token={_refresh_token}"
        Payload = {}
        return send_request(Url, Headers, Payload, is_post=True)
    
    def get_personal_information(_user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Scopes = 'user-read-email user-read-private'
        Url = f"https://api.spotify.com/v1/me"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def get_user_playlists(_user_id, _user_bearer, _limit=50, _offset=0, _url_override=False, _url_offset_val=None):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        if not _url_override:
            Url = f"https://api.spotify.com/v1/users/{_user_id}/playlists?limit={_limit}&offset={_offset}"
        else:
            Url = _url_offset_val
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def get_playlist_items(_playlist_id, _user_bearer, _url_override=False, _url_offset_val=None):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        if not _url_override:
            Url = f"https://api.spotify.com/v1/playlists/{_playlist_id}/tracks"
        else:
            Url = _url_offset_val
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def get_top_fifteen_artists(_user_bearer, _time_range="medium_term", _limit=20):
        Headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/me/top/artists?time_range=long_term"
        Payload = ""
        return send_request(Url, Headers, Payload, is_get=True)
    
    def get_similar_artists(_artist_id, _user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/artists/{_artist_id}/related-artists"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def create_playlist(_user_id, _user_bearer, _playlist_name='Why u no choose a name?', _playlist_description=None):
        Headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/users/{_user_id}/playlists"
        Payload = json.dumps({"name": f"{_playlist_name}",
                                       "description": f"{_playlist_description}",
                                       "public": False})
        return send_request(Url, Headers, Payload, is_post=True)
    
    def get_artist_top_track(_artist_id, _user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/artists/{_artist_id}/top-tracks?market=US"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def put_items_in_playlist(_user_id, _user_bearer, _playlist_id, _song_uri):
        Headers = {'Authorization': f'Bearer {_user_bearer}',
                   'content-type': 'application/json'}
        Url = f"https://api.spotify.com/v1/users/{_user_id}/playlists/{_playlist_id}/tracks"
        Payload = json.dumps({"uris": _song_uri})
        return send_request(Url, Headers, Payload, is_post=True)
    
    def get_user_queue(_user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/me/player/queue"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def update_playlist_items(_user_id, _user_bearer, _playlist_id, _item_idx, _ib_item_idx):
        Headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/playlists/{_playlist_id}/tracks"
        Payload = json.dumps({"range_start": _item_idx, "insert_before": _ib_item_idx})
        return send_request(Url, Headers, Payload, is_put=True)
    
    def get_avaliable_genre_seeds(_user_bearer):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)
    
    def update_playlist_image(_user_bearer, _playlist_id, _b64_img):
        Headers = {
        'Content-Type': 'text/plain',
        'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/playlists/{_playlist_id}/images"
        Payload = _b64_img
        return send_request(Url, Headers, Payload, is_put=True)

    def get_recomendations_genre(_user_bearer, song_attr, _limit=10, _seed_genres=None):
        Headers = {'Authorization': f'Bearer {_user_bearer}'}
        Url = f"https://api.spotify.com/v1/recommendations?limit={_limit}&seed_genres={_seed_genres}&target_popularity={song_attr['t_pop']}"
        Payload = {}
        return send_request(Url, Headers, Payload, is_get=True)