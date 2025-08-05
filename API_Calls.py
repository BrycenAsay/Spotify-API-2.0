import pandas as pd
import os
from API_URIs import API_URIs
from OAuth import refresh_access_token
from sqlalchemy import create_engine, text
from Image_Generation import return_rand_img
import random
import logging
import time
from config import DATABASE, HOST, USER, PASSWORD

engine = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

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
        sql = text(f'SELECT playlist_ids FROM "{some_display_name}s_playlists"')
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
    user_playlists_info_dict = {'playlist_names': [], 'playlist_ids': [], 'playlist_owners': [], 'num_of_tracks': []}

    # set up API details and make a call, make sure to check for errors
    pure_data = API_URIs.get_user_playlists(user_id, access_token)

    # parse through the JSON and store desired data into lists
    for item in pure_data['items']:
        user_playlists_info_dict['playlist_names'].append(item['name'])
        user_playlists_info_dict['playlist_ids'].append(item['id'])
        user_playlists_info_dict['num_of_tracks'].append(item['tracks']['total'])
        user_playlists_info_dict['playlist_owners'].append(item['owner']['display_name'])

    # make calls, parse JSON, and store data until there are no more pages to paginate to
    while pure_data['next'] != None:
        url_ov = pure_data['next']
        pure_data = API_URIs.get_user_playlists(user_id, access_token, _url_override=True, _url_offset_val=url_ov)
        for item in pure_data['items']:
            user_playlists_info_dict['playlist_names'].append(item['name'])
            user_playlists_info_dict['playlist_ids'].append(item['id'])
            user_playlists_info_dict['num_of_tracks'].append(item['tracks']['total'])
            user_playlists_info_dict['playlist_owners'].append(item['owner']['display_name'])

    # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
    user_playlists_info_df = pd.DataFrame(user_playlists_info_dict)
    user_playlists_info_df.to_sql(f'{_display_name}s_playlists', engine)

def get_playlist_tracks(_display_name):
    # retreieve user id and proper access_token for user
    Scopes = 'playlist-read-private playlist-read-collaborative'
    user_info = retrieve_user_auth(_display_name, Scopes)
    playlist_ids = retrieve_user_playlist_ids(_display_name)
    print(playlist_ids)
    access_token = user_info[0]

    # set up lists for data we want to store from playlists
    playlist_items_info_dict = {'song_id':[], 'song_name':[], 'added_on':[], 'released_on':[], 'artist':[], 'song_length':[], 
                                'popularity':[], 'is_explicit':[], 'album_or_single':[], 'album_name':[], 
                                'num_of_album_tracks':[], 'track_number':[]}

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    for playlist_id in playlist_ids:
        pure_data = API_URIs.get_playlist_items(playlist_id, access_token)

        # parse through JSON and store desired data into lists
        for item in pure_data['items']:
            playlist_items_info_dict['song_id'].append(item['track']['id'])
            playlist_items_info_dict['song_name'].append(item['track']['name'])
            playlist_items_info_dict['added_on'].append(item['added_at'])
            playlist_items_info_dict['released_on'].append(item['track']['album']['release_date'])
            in_case_multiple_artists = []
            for _artist in item['track']['artists']:
                in_case_multiple_artists.append(_artist['name'])
            playlist_items_info_dict['artist'].append(', '.join(in_case_multiple_artists))
            playlist_items_info_dict['song_length'].append(item['track']['duration_ms'])
            playlist_items_info_dict['popularity'].append(item['track']['popularity'])
            playlist_items_info_dict['is_explicit'].append(item['track']['explicit'])
            playlist_items_info_dict['album_or_single'].append(item['track']['album']['album_type'])
            playlist_items_info_dict['album_name'].append(item['track']['album']['name'])
            playlist_items_info_dict['num_of_album_tracks'].append(item['track']['album']['total_tracks'])
            playlist_items_info_dict['track_number'].append(item['track']['track_number'])
        
        # continue to do the same thing until there are no more pages to paginate through
        while pure_data['next'] != None:
            url = pure_data['next']
            print(url)
            pure_data = API_URIs.get_playlist_items(playlist_id, access_token, _url_override=True, _url_offset_val=url)
            for item in pure_data['items']:
                playlist_items_info_dict['song_id'].append(item['track']['id'])
                playlist_items_info_dict['song_name'].append(item['track']['name'])
                playlist_items_info_dict['added_on'].append(item['added_at'])
                playlist_items_info_dict['released_on'].append(item['track']['album']['release_date'])
                in_case_multiple_artists = []
                for _artist in item['track']['artists']:
                    in_case_multiple_artists.append(_artist['name'])
                playlist_items_info_dict['artist'].append(', '.join(in_case_multiple_artists))
                playlist_items_info_dict['song_length'].append(item['track']['duration_ms'])
                playlist_items_info_dict['popularity'].append(item['track']['popularity'])
                playlist_items_info_dict['is_explicit'].append(item['track']['explicit'])
                playlist_items_info_dict['album_or_single'].append(item['track']['album']['album_type'])
                playlist_items_info_dict['album_name'].append(item['track']['album']['name'])
                playlist_items_info_dict['num_of_album_tracks'].append(item['track']['album']['total_tracks'])
                playlist_items_info_dict['track_number'].append(item['track']['track_number'])
    
    # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
    playlist_items_info_df = pd.DataFrame(playlist_items_info_dict)
    playlist_items_info_df.to_sql(f'{_display_name}s_tracks_wdup', engine)

def make_user_recommendations_playlist(_display_name):
    # retreieve user id and proper access_token for user
    Scopes = 'user-top-read'
    user_info = retrieve_user_auth(_display_name, Scopes)
    access_token = user_info[0]
    user_id = user_info[1]

    # set up lists for data we want to store from playlists
    info_dict = {'artist_id':[], 'artist_uri':[], 'artist_name':[], 'artist_genres':[], 'artist_popularity':[]}

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    pure_data = API_URIs.get_top_fifteen_artists(access_token)

    # parse through JSON and store desired data into lists
    for item in pure_data['items']:
        info_dict['artist_id'].append(item['id'])
        info_dict['artist_uri'].append(item['uri'])
        info_dict['artist_name'].append(item['name'])
        info_dict['artist_popularity'].append(item['popularity'])
        in_case_multiple_genres = []
        for _genre in item['genres']:
            in_case_multiple_genres.append(_genre)
        info_dict['artist_genres'].append(', '.join(in_case_multiple_genres))
    
    try:
        # once all calls have been made, we set up the dictionary and utialize pandas to convert dictionary into a SQL table
        info_df = pd.DataFrame(info_dict)
        info_df.to_sql(f'{_display_name}s_top_artists', engine)
    except:
        print('Top fifteen table already exists, moving on')
    
    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    master_lyst = []
    similar_artists_ids = []
    for _artist_id in info_dict['artist_id']:
        pure_data = API_URIs.get_similar_artists(_artist_id, access_token)
        for item in pure_data['artists']:
            similar_artists_ids.append(item['id'])

    master_lyst.append(similar_artists_ids)
    similar_artists_sa_ids = []
    for _artist_id in similar_artists_ids:
        pure_data = API_URIs.get_similar_artists(_artist_id, access_token)
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
            pure_data = API_URIs.get_artist_top_track(similar_artist_ids[i], access_token)
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
            pure_data = API_URIs.get_artist_top_track(similar_artist_ids[i], access_token)
            try:
                song_uris.append(pure_data['tracks'][0]['uri'])
            except:
                print(f"apparently no songs for this artist? {pure_data['tracks']}")

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    pure_data = API_URIs.create_playlist(user_id, access_token, 'Songs Similar to Your Top 20', 'Took artists similar to your top 20, then artists similar to those artists, then added their most popular songs. Enjoy :)')
    playlist_id = pure_data['id']

    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    first_digits = round(len(song_uris), -2)
    for i in range(0, first_digits + 1, 100):
        if i < first_digits:
            e = i + 100
            song_uris_arr = song_uris[i:e]
        else:
            song_uris_arr = song_uris[first_digits:len(song_uris)]
        pure_data = API_URIs.put_items_in_playlist(user_id, access_token, playlist_id, song_uris_arr)

def randomize_playlist_order(_display_name, _playlyst_id):
    # retreieve user id and proper access_token for user
    Scopes = 'playlist-modify-private playlist-modify-public'
    user_info = retrieve_user_auth(_display_name, Scopes)
    access_token = user_info[0]
    user_id = user_info[1]

    # retrieve number of tracks for the playlist from the database
    num_of_tracks = (pd.read_sql(text(f"SELECT num_of_tracks FROM {_display_name}s_playlists WHERE playlist_ids = '{_playlyst_id}'"), con=engine.connect())).to_dict()['num_of_tracks'][0]

    # create a list with every item # randomized for the playlist, then assign every item a position
    pos_items = [i for i in range(num_of_tracks)]
    reass_pos = [i for i in range(num_of_tracks)]
    rand_item_pos_assign = {}
    for i in range(len(pos_items)):
        rand_pos_assign = reass_pos[random.randint(0, len(reass_pos) - 1)]
        rand_item_pos_assign[pos_items[i]] = rand_pos_assign
        reass_pos.pop(reass_pos.index(rand_pos_assign))

    # iterate throught he dict, until each item has been reassigned to it's designated value
    for item in rand_item_pos_assign:
        pure_data = API_URIs.update_playlist_items(user_id, access_token, _playlyst_id, item, rand_item_pos_assign[item])
        print(pure_data)
        time.sleep(.14)

def end_music_phobia(_display_name, _playlist_id='7mc6eQFiPnXBPwq1zWsk02'):
    # retreieve user id and proper access_token for user
    Scopes = 'ugc-image-upload playlist-modify-private playlist-modify-public'
    user_info = retrieve_user_auth(_display_name, Scopes)
    access_token = user_info[0]
    user_id = user_info[1]

    # set playlist image
    API_URIs.update_playlist_image(access_token, _playlist_id, return_rand_img())

    # define function to initialize dictonary with all individual song attributes and randomized values
    def song_attr_random():
        song_attrs_dict = {}
        keys = ['t_pop']
        for key in keys:
            if key not in ['t_pop', 't_temp']:
                song_attrs_dict[key] = random.randint(0, 100) / 100
            elif key == 't_pop':
                song_attrs_dict[key] = random.randint(0, 100)
            elif key == 't_temp':
                song_attrs_dict[key] = random.randint(50, 190)
        return song_attrs_dict

    # initialize a list with all possible genre parm options Spotify will allow
    poss_genres = API_URIs.get_avaliable_genre_seeds(access_token)['genres']

    # get music recommendations to add, append results to list
    song_uris = []
    song_genres = []
    genre_groups = []
    print(f'Image init completed. So far, 0/{len(genre_groups)} recommendations recieved! :/')
    for i in range(0, len(poss_genres), 5):
        if (i + 5) < len(poss_genres):
            genre_groups.append(poss_genres[i:i+ 5])
        elif (i + 5) > len(poss_genres):
            genre_groups.append(poss_genres[i:(i + (len(poss_genres) % 5))])
    for genre_group in genre_groups:
        time.sleep(0.5)
        try:
            something = API_URIs.get_recomendations_genre(access_token, song_attr_random(), 50, genre_group)
            print(something)
            input()
            input()
            # song_uris.append(track['uri'])
        except:
            pass
        done_so_far = genre_groups.index(genre_group) + 1

        # update access token so it does not expire
        refresh_access_token('9g0sn24ze4wyf0gpldyfxmy96', 'ugc-image-upload playlist-modify-private playlist-modify-public')
        user_info = retrieve_user_auth(_display_name, Scopes)
        access_token = user_info[0]

        os.system('cls')

        if done_so_far <= 10:
            print(f"WOW, ALMOST THERE!!!... Jk only {done_so_far}/{len(genre_groups)} loaded :'(")
        elif done_so_far <= 30:
            print(f"Losing patience already, I see??? WOMP WOMP. Only {done_so_far}/{len(genre_groups)} loaded :'(")
        elif done_so_far <= 50:
            print(f"Slow and steady, as they say... {done_so_far}/{len(genre_groups)} loaded :(")
        elif done_so_far <= 67:
            print(f"Far along, but not far enough mannnnn, {done_so_far}/{len(genre_groups)} loaded :/")
        elif done_so_far <= 68:
            print(f"Almost there... {done_so_far}/{len(genre_groups)} loaded :/")
        elif done_so_far == 69:
            print(f"HAHAHAHAHAHAHAHAHHAHAHAH FUNNY NUMBER!!! {done_so_far}/{len(genre_groups)} loaded :DDDDD")
        elif done_so_far <= 99:
            print(f"Pretty sure you stopped monitoring this by now... {done_so_far}/{len(genre_groups)} loaded :/")
        elif done_so_far <= 100:
            print(f"Hitting triple digits now! Reaching the home stretch! {done_so_far}/{len(genre_groups)} loaded :)")
        elif done_so_far <= 110:
            print(f"Please don't hit the rate limit... please don't throw an error... {done_so_far}/{len(genre_groups)} loaded :)")
        elif done_so_far <= len(poss_genres) - 4:
            print(f"PLEASE DON'T HIT THE RATE LIMIT... PLEASE DON'T THROW AN ERROR... I'M FUCKING BEGGING YOU MANNNNNN- {done_so_far}/{len(genre_groups)} loaded :)")
        elif done_so_far <= len(poss_genres) - 1:
            print(f"ONLY ONE MORE LEFT PLEASE BY THE POWER OF THE HOLY SPAGHETTI MONSTER PLEASE LET THIS WORK... {done_so_far}/{len(genre_groups)} loaded :)")
        elif done_so_far <= len(poss_genres):
            print(f"It. Is. Finished. My. Work. Is. Done. {done_so_far}/{len(genre_groups)} loaded :D :D :D :D :D :D :D :D :D :D :D :D (PLEASE LET THE ACTUAL ADDING-THE-SONGS-TO-THE-PLAYLIST SHIT WORK)")
    
    # set up API details and make a call, make sure to check for errors (in the case of playlists, loop until you run out of playlist ids)
    first_digits = round(len(song_uris), -2)
    for i in range(0, first_digits + 1, 100):
        if i < first_digits:
            e = i + 100
            song_uris_arr = song_uris[i:e]
        else:
            song_uris_arr = song_uris[first_digits:len(song_uris)]
        API_URIs.put_items_in_playlist(user_id, access_token, _playlist_id, song_uris_arr)