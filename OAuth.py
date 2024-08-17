from API_URIs import API_URIs
from sqlalchemy import create_engine, text
import logging
from config import DATABASE, HOST, USER, PASSWORD

engine = create_engine(f'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}')

def error_handling(message, USER_ID=None, SCOPES=None):
    if 'error' in message:
        try:
            if message['error']['message'] == 'The access token expired':
                fix_this = input("Looks like the access token expired. Would you like to refresh this? (Y/N): ")
                while fix_this != 'Y' or fix_this != 'N':
                    print("ERROR! Please provide only either Y (for yes) or N (for no) as input!")
                    fix_this = input("Looks like the access token expired. Would you like to refresh this? (Y/N): ")
                if fix_this == "Y":
                    print("Alright, we will go ahead and refresh the token, this will kill the terminal and you will have to re-run the program. Hopefully it works this time! :)")
                    refresh_access_token(USER_ID, SCOPES)
                    quit()
                else:
                    quit()
            print(f"There was a {message['error']['status']} error boiii :P --> \"{message['error']['message']}!\"")
        except:
            print(f"There was an error boiii :P --> \"{message['error']}\"")
        quit()

def create_row(table_name, columns, data):
    columns = ','.join(columns)
    data = ','.join(data)
    query = text(f'INSERT INTO {table_name}({columns}) VALUES ({data});')
    return query

def update_row(table_name, columns, data, thing_1, value_1, thing_2, value_2):
    update_statements = []
    for i in range(len(columns)):
        query = text(f"UPDATE {table_name} SET {columns[i]} = '{data[i]}' WHERE {thing_1} = '{value_1}' AND {thing_2} = '{value_2}'")
        update_statements.append(query)
    return update_statements

def refresh_access_token(_user_id, _scopes):
    with engine.connect() as conn:
        sql = text(f"SELECT refresh_token FROM user_info WHERE user_id = '{_user_id}' AND scope = '{_scopes}'")
        try:
            yes = conn.execute(sql)
            conn.commit()
            for row in yes:
                refresh_token = row[0]
        except Exception as e:
            logging.error('did not work: ', e)
            conn.rollback()
        pure_authorization_data = API_URIs.refresh_access_token(refresh_token)
        error_handling(pure_authorization_data)
        COLUMNS = ['access_token']
        DATA = [pure_authorization_data['access_token']]
        sql = update_row('user_info', COLUMNS, DATA, 'user_id', _user_id, 'scope', _scopes)
        sql = sql[0]
        try:
            conn.execute(sql)
            conn.commit()
        except Exception as e:
            logging.error('did not work: ', e)
            conn.rollback()
        conn.close()

def main():
    # authorize person in order to get personal details within the required scopes
    scopes = input('Enter scopes to authorize the user under: ')
    print(f'visit this URL: {API_URIs.get_code(_scopes=scopes)}')

    # second step, passing the code in and using the correct API call so that we can get the access token
    code = input('Paste code (from URL) here: ')
    pure_authorization_data = API_URIs.get_access_token(code)
    error_handling(pure_authorization_data)

    # getting more info on the person so we actually know who is who
    pure_personal_data = API_URIs.get_personal_information(pure_authorization_data['access_token'])
    error_handling(pure_personal_data)

    # check to see if user already in database
    user_id_exists = False
    same_scope = False
    with engine.connect() as conn:
        sql = text('SELECT user_id, scope FROM user_info')
        try:
            yes = conn.execute(sql)
            conn.commit()
            for row in yes:
                if pure_personal_data['id'] == row[0]:
                    user_id_exists = True
                if pure_authorization_data['scope'] == row[1]:
                    same_scope = True
        except Exception as e:
            logging.error('did not work: ', e)
            conn.rollback()
        conn.close()

    # we then put data into the database for future use (if not already in database)
    if user_id_exists == False or same_scope == False:
        COLUMNS = ['display_name', 'user_id', 'uri', 'access_token', 'refresh_token', 'scope']
        DATA = []
        for COL in COLUMNS:
            if COL == "user_id":
                COL = "id"
            if COL in pure_authorization_data:
                DATA.append("'" + pure_authorization_data[COL] + "'")
            else:
                DATA.append("'" + pure_personal_data[COL] + "'")
        with engine.connect() as conn:
            sql = create_row('user_info', COLUMNS, DATA)
            print(sql)
            try:
                conn.execute(sql)
                conn.commit()
            except Exception as e:
                logging.error('did not work: ', e)
                conn.rollback()
            conn.close()
    else:
        COLUMNS = ['access_token', 'refresh_token']
        DATA = []
        for COL in COLUMNS:
            DATA.append("'" + pure_authorization_data[COL] + "'")
        with engine.connect() as conn:
            sql = update_row('user_info', COLUMNS, DATA, 'user_id', pure_personal_data['id'], 'scope', pure_authorization_data['scope'])
            for sql_statement in sql:
                try:
                    conn.execute(sql_statement)
                    conn.commit()
                except Exception as e:
                    logging.error('did not work: ', e)
                    conn.rollback()
            conn.close()


if __name__ == '__main__':
    main()