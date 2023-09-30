from sqlalchemy import create_engine, text
from config import DATABASE, HOST, USER, PASSWORD
from API_Calls import get_user_playlists, get_playlist_tracks, make_user_recommendations_playlist, refresh_access_token
import logging
engine = create_engine(f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

def create_row(table_name, columns, data):
    columns = ','.join(columns)
    data = ','.join(data)
    query = text(f'INSERT INTO {table_name}({columns}) VALUES ({data});')
    return query

def main():
    make_user_recommendations_playlist('よまま')

if __name__ == "__main__":
    main()