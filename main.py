from sqlalchemy import create_engine, text
from config import DATABASE, HOST, USER, PASSWORD
import API_Calls
import logging
import time
engine = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

def create_row(table_name, columns, data):
    columns = ','.join(columns)
    data = ','.join(data)
    query = text(f'INSERT INTO {table_name}({columns}) VALUES ({data});')
    return query

def main():
    API_Calls.end_music_phobia('よまま')

if __name__ == "__main__":
    main()