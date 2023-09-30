import requests
import time
import pandas as pd
from API_URIs import API_URIs
from OAuth import refresh_access_token
from sqlalchemy import create_engine, text
import logging
import json
from config import DATABASE, HOST, USER, PASSWORD

engine = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

def error_handling(message, _url, _headers, _payload, SOME_DISPLAY_NAME=None, SCOPES=None):
    #error handling in case an API response isn't of code 200
    if 'error' in message:
        try:
            #error handling for rate limit error
            if message['error']['status'] == 429:
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

def retrieve_user_auth(some_display_name, _scopes):
    # refreshes, and THEN retrieves the user_id and access token for a given user from the database
    for i in range(2):
        Scopes = _scopes
        scope_exists = False
        with engine.connect() as conn:
            sql = text(f"SELECT user_id, scope FROM user_info WHERE display_name = '{some_display_name}'")
            try:
                yes = conn.execute(sql)
                conn.commit()
                for row in yes:
                    user_id = row[0]
                    if Scopes == row[1]:
                        scope_exists = True
                if scope_exists == False:
                    print(f"ERROR, correct auth for specified scopes does not exist. Please have the user authenticate under scopes: {Scopes} and try again")
                    quit()
                sql = text(f"SELECT access_token, scope FROM user_info WHERE scope = '{Scopes}' AND user_id = '{user_id}'")
                yes = conn.execute(sql)
                for row in yes:
                    access_token = row[0]
                conn.close()
            except Exception as e:
                logging.error('did not work: ', e)
                conn.rollback()
                conn.close()
            if i == 0:
                refresh_access_token(user_id, Scopes)
    return access_token, user_id

def retrieve_user_playlist_ids(some_display_name):
    # Retrieves the list of playlist ids from the database
    playlist_ids = []
    with engine.connect() as conn:
        sql = text(f"SELECT playlist_ids FROM `{some_display_name}s_playlists`")
        try:
            yes = conn.execute(sql)
            conn.commit()
            for row in yes:
                playlist_ids.append(row[0])
            conn.close()
            return playlist_ids
        except Exception as e:
            logging.error('did not work: ', e)
            conn.rollback()
            conn.close()

def get_user_playlists(_display_name):
    # retreieve user id and proper access_token for user
    Scopes = 'playlist-read-private playlist-read-collaborative'
    user_info = retrieve_user_auth(_display_name, Scopes)
    access_token = user_info[0]
    user_id = user_info[1]

    # set up lists for data we want to store from playlists
    playlist_names = []
    playlist_ids = []
    playlist_owners = []
    num_of_tracks = []

    # set up API details and make a call, make sure to check for errors
    get_user_playlists_API_deets = API_URIs.get_user_playlists(user_id, access_token)
    url = get_user_playlists_API_deets['URL']
    headers = get_user_playlists_API_deets['Headers']
    payload = get_user_playlists_API_deets['Payload']
    response = requests.request("GET", url, headers=headers, data=payload)
    unclean_data = response.json()
    pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)

    # parse through the JSON and store desired data into lists
    for item in pure_data['items']:
        playlist_names.append(item['name'])
        playlist_ids.append(item['id'])
        num_of_tracks.append(item['tracks']['total'])
        playlist_owners.append(item['owner']['display_name'])

    # make calls, parse JSON, and store data until there are no more pages to paginate to
    while pure_data['next'] != None:
        url = pure_data['next']
        response = requests.request("GET", url, headers=headers, data=payload)
        unclean_data = response.json()
        pure_data = error_handling(unclean_data, url, headers, payload)
        for item in pure_data['items']:
            playlist_names.append(item['name'])
            playlist_ids.append(item['id'])
            num_of_tracks.append(item['tracks']['total'])
            playlist_owners.append(item['owner']['display_name'])

    # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
    user_playlists_info_dict = {'playlist_names':playlist_names, 'playlist_ids':playlist_ids, 'playlist_owners':playlist_owners, 'num_of_tracks':num_of_tracks}
    user_playlists_info_df = pd.DataFrame(user_playlists_info_dict)
    user_playlists_info_df.to_sql(f'{_display_name}s_playlists', engine)

def get_playlist_tracks(_display_name):
    # retreieve user id and proper access_token for user
    Scopes = 'playlist-read-private playlist-read-collaborative'
    user_info = retrieve_user_auth(_display_name, Scopes)
    playlist_ids = retrieve_user_playlist_ids(_display_name)
    access_token = user_info[0]
    user_id = user_info[1]

    # set up lists for data we want to store from playlists
    song_id = []
    song_name = []
    added_on = []
    released_on = []
    artist = []
    song_length = []
    popularity = []
    is_explicit = []
    album_or_single = []
    album_name = []
    num_of_album_tracks = []
    track_number = []

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    for playlist_id in playlist_ids:
        get_playlist_items_API_deets = API_URIs.get_playlist_items(playlist_id, access_token)
        url = get_playlist_items_API_deets['URL']
        headers = get_playlist_items_API_deets['Headers']
        payload = get_playlist_items_API_deets['Payload']
        response = requests.request("GET", url, headers=headers, data=payload)
        unclean_data = response.json()
        pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)

        # parse through JSON and store desired data into lists
        for item in pure_data['items']:
            song_id.append(item['track']['id'])
            song_name.append(item['track']['name'])
            added_on.append(item['added_at'])
            released_on.append(item['track']['album']['release_date'])
            in_case_multiple_artists = []
            for _artist in item['track']['artists']:
                in_case_multiple_artists.append(_artist['name'])
            artist.append(', '.join(in_case_multiple_artists))
            song_length.append(item['track']['duration_ms'])
            popularity.append(item['track']['popularity'])
            is_explicit.append(item['track']['explicit'])
            album_or_single.append(item['track']['album']['album_type'])
            album_name.append(item['track']['album']['name'])
            num_of_album_tracks.append(item['track']['album']['total_tracks'])
            track_number.append(item['track']['track_number'])
        
        # continue to do the same thing until there are no more pages to paginate through
        while pure_data['next'] != None:
            url = pure_data['next']
            response = requests.request("GET", url, headers=headers, data=payload)
            unclean_data = response.json()
            pure_data = error_handling(unclean_data, url, headers, payload)
            for item in pure_data['items']:
                song_id.append(item['track']['id'])
                song_name.append(item['track']['name'])
                added_on.append(item['added_at'])
                released_on.append(item['track']['album']['release_date'])
                in_case_multiple_artists = []
                for _artist in item['track']['artists']:
                    in_case_multiple_artists.append(_artist['name'])
                artist.append(', '.join(in_case_multiple_artists))
                song_length.append(item['track']['duration_ms'])
                popularity.append(item['track']['popularity'])
                is_explicit.append(item['track']['explicit'])
                album_or_single.append(item['track']['album']['album_type'])
                album_name.append(item['track']['album']['name'])
                num_of_album_tracks.append(item['track']['album']['total_tracks'])
                track_number.append(item['track']['track_number'])
    
    # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
    playlist_items_info_dict = {'song_id':song_id, 'song_name':song_name, 'added_on':added_on, 'released_on':released_on, 'artist':artist, 'song_length':song_length, 
                                'popularity':popularity, 'is_explicit':is_explicit, 'album_or_single':album_or_single, 'album_name':album_name, 
                                'number_of_album_tracks':num_of_album_tracks, 'track_number':track_number}
    playlist_items_info_df = pd.DataFrame(playlist_items_info_dict)
    playlist_items_info_df.to_sql(f'{_display_name}s_tracks_wdup', engine)

def make_user_recommendations_playlist(_display_name):
    # retreieve user id and proper access_token for user
    Scopes = 'user-top-read'
    user_info = retrieve_user_auth(_display_name, Scopes)
    access_token = user_info[0]
    user_id = user_info[1]

    # set up lists for data we want to store from playlists
    artist_id = []
    artist_uri = []
    artist_name = []
    artist_popularity = []
    artist_genres = []

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    get_user_playlists_API_deets = API_URIs.get_top_fifteen_artists(access_token)
    url = get_user_playlists_API_deets['URL']
    Headers = get_user_playlists_API_deets['Headers']
    payload = get_user_playlists_API_deets['Payload']
    response = requests.request("GET", url, headers=Headers, data=payload)
    unclean_data = response.json()
    pure_data = error_handling(unclean_data, url, Headers, payload, user_id, Scopes)

    # parse through JSON and store desired data into lists
    for item in pure_data['items']:
        artist_id.append(item['id'])
        artist_uri.append(item['uri'])
        artist_name.append(item['name'])
        artist_popularity.append(item['popularity'])
        in_case_multiple_genres = []
        for _genre in item['genres']:
            in_case_multiple_genres.append(_genre)
        artist_genres.append(', '.join(in_case_multiple_genres))
    
    try:
        # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
        info_dict = {'artist_id':artist_id, 'artist_uri':artist_uri, 'artist_name':artist_name, 'artist_genres':artist_genres, 'artist_popularity':artist_popularity}
        info_df = pd.DataFrame(info_dict)
        info_df.to_sql(f'{_display_name}s_top_artists', engine)
    except:
        print('Top fifteen table already exists, moving on')
    
    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    master_lyst = []
    similar_artists_ids = []
    for _artist_id in artist_id:
        get_API_deets = API_URIs.get_similar_artists(_artist_id, access_token)
        url = get_API_deets['URL']
        headers = get_API_deets['Headers']
        payload = get_API_deets['Payload']
        response = requests.request("GET", url, headers=headers, data=payload)
        unclean_data = response.json()
        pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)
        for item in pure_data['artists']:
            similar_artists_ids.append(item['id'])

    master_lyst.append(similar_artists_ids)
    similar_artists_sa_ids = []
    for _artist_id in similar_artists_ids:
        get_API_deets = API_URIs.get_similar_artists(_artist_id, access_token)
        url = get_API_deets['URL']
        headers = get_API_deets['Headers']
        payload = get_API_deets['Payload']
        response = requests.request("GET", url, headers=headers, data=payload)
        unclean_data = response.json()
        pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)

        for item in pure_data['artists']:
            similar_artists_sa_ids.append(item['id'])
        
        _similar_artist_ids = []
    master_lyst.append(similar_artists_sa_ids)
    for lyst in master_lyst:
        for item in lyst:
            _similar_artist_ids.append(item)
    
    similar_artist_ids = list(set(_similar_artist_ids))
    
    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    song_uris = []
    for i in range(len(similar_artist_ids)):
        if i <= 400:
            get_API_deets = API_URIs.get_artist_top_track(similar_artist_ids[i], access_token)
            url = get_API_deets['URL']
            headers = get_API_deets['Headers']
            payload = get_API_deets['Payload']
            response = requests.request("GET", url, headers=headers, data=payload)
            unclean_data = response.json()
            pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)
            try:
                song_uris.append(pure_data['tracks'][0]['uri'])
            except:
                print(f"apparently no songs for this artist? {pure_data['tracks']}")
            try:
                song_uris.append(pure_data['tracks'][1]['uri'])
                song_uris.append(pure_data['tracks'][2]['uri'])
            except:
                print(f"There only exists {pure_data['tracks']} for artist, therefore, we can't add three songs :(")
        else:
            get_API_deets = API_URIs.get_artist_top_track(similar_artist_ids[i], access_token)
            url = get_API_deets['URL']
            headers = get_API_deets['Headers']
            payload = get_API_deets['Payload']
            response = requests.request("GET", url, headers=headers, data=payload)
            unclean_data = response.json()
            pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)
            try:
                song_uris.append(pure_data['tracks'][0]['uri'])
            except:
                print(f"apparently no songs for this artist? {pure_data['tracks']}")

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    get_API_deets = API_URIs.create_playlist(user_id, access_token, 'Songs Similar to Your Top 20', 'Took artists similar to your top 20, then artists similar to those artists, then added their most popular songs. Enjoy :)')
    url = get_API_deets['URL']
    headers = get_API_deets['Headers']
    payload = get_API_deets['Payload']
    response = requests.request("POST", url, headers=headers, data=payload)
    unclean_data = response.json()
    pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)
    playlist_id = pure_data['id']

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    first_digits = round(len(song_uris), -2)
    for i in range(0, first_digits + 1, 100):
        if i < first_digits:
            e = i + 100
            song_uris_arr = song_uris[i:e]
        else:
            song_uris_arr = song_uris[first_digits:len(song_uris)]
        get_API_deets = API_URIs.put_items_in_playlist(user_id, access_token, playlist_id, song_uris_arr)
        url = get_API_deets['URL']
        headers = get_API_deets['Headers']
        payload = get_API_deets['Payload']
        response = requests.request("POST", url, headers=headers, data=payload)
        unclean_data = response.json()
        pure_data = error_handling(unclean_data, url, headers, payload, user_id, Scopes)
    