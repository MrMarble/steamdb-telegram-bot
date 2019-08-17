import json
import sqlite3
import time

from . import settings


class DB:
    def __init__(self):
        self.conn = sqlite3.connect('steamdb.db', check_same_thread=False)

    def setup_database(self):
        with open('steamdb.sql', 'r') as file:
            cursor = self.conn.cursor()
            for line in file.readlines():
                cursor.execute(line)
            cursor.close()
            self.conn.commit()

    def get_cache(self, cache_key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT data FROM cache where id = ? and date >= ?',
                       (cache_key, time.time() - int(settings.CACHE_DB)))
        data = cursor.fetchone()
        cursor.close()
        if data:
            return json.loads(data[0])
        return False

    def set_cache(self, cache_key, data):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO cache values (?,?,CURRENT_TIMESTAMP)', (cache_key, json.dumps(data)))
        cursor.close()
        self.conn.commit()

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

    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT (SELECT count(id) from cache)," +
                       " (SELECT count(id) from cache where julianday(date) > julianday(current_timestamp - ?)), " +
                       "(select count(steam_id) from steam)," +
                       "(select steam_id from steam order by hits desc limit 1)," +
                       "(select steam_id from steam order by hits asc, added limit 1)," +
                       "(select count(user_id) from log)," +
                       "(select count(distinct chat_id) from log)," +
                       "(select count(distinct user_id) from log);", (settings.CACHE_DB,))
        result = cursor.fetchone()
        cursor.close()
        return {
            'cache_total': result[0],
            'cache_valid': result[1],
            'steam_total': result[2],
            'stam_most_hits': result[3],
            'steam_lowest_hits': result[4],
            'log_total': result[5],
            'log_unique_chats': result[6],
            'log_unique_users': result[7],
        }
