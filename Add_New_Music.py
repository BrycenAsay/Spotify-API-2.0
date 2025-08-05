from sqlalchemy import create_engine, text
from config import DATABASE, HOST, USER, PASSWORD
from API_Calls import get_user_playlists, get_playlist_tracks, make_user_recommendations_playlist, refresh_access_token
import logging
engine = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

def main():
    pass