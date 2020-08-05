import json
import os
import sqlite3
import time
from datetime import datetime as dt
from . import settings


class DB:
    def __init__(self):
        self.path = os.path.dirname(os.path.relpath(__file__))
        self.conn = sqlite3.connect(f'{self.path}/../steamdb.db', check_same_thread=False)
        self.setup_database()

    def setup_database(self):
        with open(f'{self.path}/steamdb.sql', 'r') as file:
            cursor = self.conn.cursor()
            for line in file.readlines():
                cursor.execute(line)
            cursor.close()
            self.conn.commit()

    def get_cache(self, cache_key):
        self.clear_expired()
        cursor = self.conn.cursor()
        cursor.execute('SELECT data FROM cache where id = ?',(cache_key,))
        data = cursor.fetchone()
        cursor.close()
        if data:
            return json.loads(data[0])
        return False

    def set_cache(self, cache_key, data):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO cache values (?,?,?)', (cache_key, json.dumps(data), time.time()+ int(settings.CACHE_DB)))
        cursor.close()
        self.conn.commit()
        self.clear_expired()

    def save_user(self, user):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM steam where steam_id = ?', (user[0],))
        if cursor.fetchone():
            cursor.execute('UPDATE steam set hits = hits + 1 where steam_id = ?', (user[0],))
        else:
            cursor.execute('INSERT INTO steam values (?,?,CURRENT_TIMESTAMP,1)', user)
        cursor.close()
        self.conn.commit()

    def log_message(self, m):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO log values (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)',
                       (m.from_user.id, m.from_user.username, m.from_user.first_name, m.from_user.last_name,
                        m.from_user.language_code, m.text, m.chat.id, m.chat.type, m.message_id))
        cursor.close()
        self.conn.commit()
   
    def clear_expired(self):
        cursor = self.conn.cursor()
        cursor.execute(f'DELETE FROM cache WHERE expire < {time.time()}')
        cursor.close()
        self.conn.commit()

    def clear_cache(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM cache')
        cursor.close()
        self.conn.commit()

    def run_query(self, query):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        self.conn.commit()
        if data:
            return json.dumps([dict(ix) for ix in data], indent=4, default=str)

    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT (SELECT count(id) from cache)," +
                       " (SELECT count(id) from cache where expire > ?), " +
                       "(select count(steam_id) from steam)," +
                       "(select steam_id from steam order by hits desc limit 1)," +
                       "(select steam_id from steam order by hits asc, added limit 1)," +
                       "(select count(user_id) from log)," +
                       "(select count(distinct chat_id) from log)," +
                       "(select count(distinct user_id) from log)," +
                       "(select max(expire) from cache)", (time.time(),))
        result = cursor.fetchone()
        cursor.close()
        return {
            'cache_total': result[0],
            'cache_valid': result[1],
            'last_expire':  dt.fromtimestamp(result[8]) if result[8] is not None else '--',
            'steam_total': result[2],
            'stam_most_hits': result[3],
            'steam_lowest_hits': result[4],
            'log_total': result[5],
            'log_unique_chats': result[6],
            'log_unique_users': result[7],
        }
