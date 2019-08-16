import json
import logging
import sqlite3
import time

import requests
import settings
import telebot
from steamdbparser import SteamDbParser
from telebot import types

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN, skip_pending=True)
steamdb = SteamDbParser.parser()
conn = sqlite3.connect('steamdb.db', check_same_thread=False)


def main():
    with open('steamdb.sql', 'r') as file:
        logging.info('Setting up DataBase')
        cursor = conn.cursor()
        for line in file.readlines():
            cursor.execute(line)
        cursor.close()
        conn.commit()
    logging.info('Starting polling')
    bot.polling(True)


def get_id():
    return str(int(time.time()))


@bot.message_handler(commands=['start'])
def message_start(m):
    db_log((m.from_user.id, m.from_user.username, m.from_user.first_name, m.from_user.last_name,
            m.from_user.language_code, m.text, m.chat.id, m.chat.type, m.message_id))
    bot.send_message(m.chat.id, 'Test', True, parse_mode='MARKDOWN')


@bot.message_handler(func=lambda m: True)
def message_handler(m):
    db_log((m.from_user.id, m.from_user.username, m.from_user.first_name, m.from_user.last_name,
            m.from_user.language_code, m.text, m.chat.id, m.chat.type, m.message_id))


@bot.inline_handler(lambda q: len(q.query) <= 2)
def inline_query(query):
    content = types.InputTextMessageContent('@steamdbbot made by @Tinoquete')
    replies = [
        types.InlineQueryResultArticle('1', 'SteamDB.info Bot!', content, description=None),
        types.InlineQueryResultArticle('2', 'Please type a steam username or steamID', content, description=None)
    ]
    bot.answer_inline_query(query.id, replies, cache_time=settings.CACHE_SHORT_QUERY)
    logging.info(
        f'Invalid Query "{query.query}" from  user {query.from_user.id}. Setting cache for {settings.CACHE_SHORT_QUERY} seconds')


# query.query
@bot.inline_handler(lambda q: len(q.query) > 2)
def search_query(query):
    try:
        logging.info(f'User {query.from_user.id} queried "{query.query}".')
        steamID = None
        bad_query = types.InlineQueryResultArticle(get_id(), 'No results!', types.InputTextMessageContent(
            f'Steam username not found: {query.query}'))
        if steamdb.isSteamId(query.query):
            logging.info(f'"{query.query}" is a valid steamID.')
            steamID = query.query
        else:
            logging.info(f'Fetching steamID for "{query.query}".')
            steamID = get_steam_id(query.query)

        if not steamID:
            logging.info(
                f'SteamID not found for "{query.query}". Setting cache for {settings.CACHE_USER_NOT_FOUND} seconds')
            bot.answer_inline_query(query.id, [bad_query], cache_time=settings.CACHE_USER_NOT_FOUND)
            return

        logging.info(f'Fetching profile data for "{steamID}".')
        profile = get_steam_profile(steamID)
        if not profile:
            logging.info(
                f'No Steam Profile found for "{steamID}". Setting cache for {settings.CACHE_USER_NOT_FOUND} seconds')
            bot.answer_inline_query(query.id, [bad_query], cache_time=settings.CACHE_USER_NOT_FOUND)
            return

        register((steamID, query.query))

        button = types.InlineKeyboardButton('Load SteamDB Data', callback_data=steamID)
        markup = types.InlineKeyboardMarkup()
        markup.add(button)
        message = types.InputTextMessageContent(
            f'*{profile["username"]}*\n`{steamID}`\n[Steam Profile]({profile["profile"]})', parse_mode='MARKDOWN')
        reply = types.InlineQueryResultArticle(get_id(), profile['username'], message, description=steamID,
                                               thumb_url=profile['img'], reply_markup=markup)
        bot.answer_inline_query(query.id, [reply], cache_time=settings.CACHE_USER_FOUND)
        logging.info(
            f'Valid Query "{query.query}" from  user {query.from_user.id}. Setting cache for {settings.CACHE_USER_FOUND} seconds')
    except Exception:
        logging.exception(f'Something happened while answering user {query.from_user.id} query "{query.query}"')


@bot.callback_query_handler(lambda c: steamdb.isSteamId(c.data))
def loadSteamDB_callback(call):
    logging.info(f'Fetching SteamDB data of "{call.data}" from User {call.from_user.id}')
    bot.answer_callback_query(call.id, f'Fetching Profile of {call.data}. It may take some seconds...',
                              show_alert=False,
                              cache_time=settings.CACHE_USER_FOUND)
    bot.edit_message_text('Loading SteamDB data...', inline_message_id=call.inline_message_id)
    profile = get_steamdb_profile(call.data)
    if not profile:
        bot.edit_message_text(
            f'Something bad happened while fetching the SteamDB Profile of *{call.data}*\nMaybe SteamDB is down',
            inline_message_id=call.inline_message_id, parse_mode='MARKDOWN')
        return
    msg = (f'[{profile["display_name"]}]({profile["url_steam"]})',
           '----------',
           f'*Level:*\t{profile["level"]}',
           f'*Games:*\t{profile["games"]}',
           f'*Played:*\t{profile["games_played"]}',
           '----------',
           f'*Account Value:*\t{profile["price"]}',
           f'*Value with offers:*\t{profile["price_lowest"]}',
           f'*Average Game price:*\t{profile["price_average"]}',
           f'*Price per Hour:*\t{profile["price_hour"]}',
           '----------',
           f'*Hours:*\t{profile["hours"]}',
           f'*Average Hours:*\t{profile["hours_average"]}',
           '----------',
           f'*SteamDB:*\t[Link]({profile["url_stamdb"]})')
    bot.edit_message_text('\n'.join(msg), inline_message_id=call.inline_message_id, parse_mode='MARKDOWN')


def get_steamdb_profile(steamid):
    logging.info(f'Looking up {steamid} in cache')
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM cache where id = ? and date >= ?',
                   (steamid, time.time() - int(settings.CACHE_DB)))
    data = cursor.fetchone()
    if data:
        logging.info(f'Returning cache of {steamid}')
        cursor.close()
        return json.loads(data[0])
    else:
        logging.info(f'Not in cache, fetching.')
        data = steamdb.getSteamDBProfile(steamid)
        if data:
            logging.info(f'Setting cache for {steamid}')
            cursor.execute('INSERT INTO cache values (?,?,?)', (f'steamdb:{steamid}', json.dumps(data), time.time()))
            cursor.close()
            conn.commit()
            return data


def get_steam_id(username):
    steamID = None
    try:
        r = requests.get(
            f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={settings.STEAM_API_TOKEN}&vanityurl={username}',
            timeout=(2, 10))
        if r.status_code == 200:
            data = r.json()['response']
            if data['success'] == 1:
                steamID = data['steamid']
    except Exception:
        logging.exception(f'Something happened while fetching "{username}" steamID')
    finally:
        return steamID


def get_steam_profile(steamID):
    try:
        r = requests.get(
            f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={settings.STEAM_API_TOKEN}&steamids={steamID}',
            timeout=(2, 10))
        if r.status_code == 200:
            data = r.json()['response']['players'][0]
            if data['personaname']:
                return {'username': data['personaname'], 'profile': data['profileurl'], 'img': data['avatarfull']}
        return None
    except Exception:
        logging.exception(f'Something happened while fetching "{steamID}" profile data')
        return None


def db_log(data):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO log values (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)', data)
    cursor.close()
    conn.commit()


def register(user):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM steam where steam_id = ?', (user[0],))
    if cursor.fetchone():
        cursor.execute('UPDATE steam set hits = hits + 1 where steam_id = ?', (user[0],))
    else:
        cursor.execute('INSERT INTO steam values (?,?,CURRENT_TIMESTAMP,1)', user)
    cursor.close()
    conn.commit()


if __name__ == "__main__":
    main()
