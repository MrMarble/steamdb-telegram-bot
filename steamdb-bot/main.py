import logging
import time

import telebot
from telebot import types
from utils import admin
from utils import database
from utils import settings
from utils import steam

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN, skip_pending=True)
steam = steam.Steam()
db = database.DB()
admin = admin.Admin()


def main():
    logging.info('Starting polling')
    bot.polling(True)


def get_id():
    return str(int(time.time()))


@bot.message_handler(commands=['start'])
def message_start(m):
    db.log_message(m)
    msg = ('*SteamDB Bot!*',
           'This is an inline bot that shows the [steamdb.info](http://steamdb.info/calculator) data of a steam profile!',
           'You can get some examples with /help',
           'If you like this bot please leave some [feedback](https://telegram.me/storebot?start=steamdbbot)!',
           '_Made by @Tinoquete_')
    bot.send_message(chat_id=m.chat.id, text='\n'.join(msg), parse_mode='MARKDOWN', disable_web_page_preview=True)


@bot.message_handler(commands=['help'])
def message_help(m):
    db.log_message(m)
    msg = ('*SteamDB Bot!*',
           'To get the data of a steam profile you can use its  *username* (custom  url) or *steamID*',
           '⚠ It *does not* work with display name! those can be used for multiple users!',
           'Example with username:',
           '	`@steamdbbot mrmarblet`',
           'Example with steamID:',
           '	`@steamdbbot 76561198287455504`')
    bot.send_message(chat_id=m.chat.id, text='\n'.join(msg), parse_mode='MARKDOWN', disable_web_page_preview=True)


@bot.message_handler(func=lambda m: True)
def message_handler(m):
    db.log_message(m)


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


@bot.inline_handler(lambda q: len(q.query) > 2)
def search_query(query):
    try:
        logging.info(f'User {query.from_user.id} queried "{query.query}".')
        steamID = None
        bad_query = types.InlineQueryResultArticle(get_id(), 'No results!', types.InputTextMessageContent(
            f'Steam username not found: {query.query}'))
        if steam.is_steam_id(query.query):
            logging.info(f'"{query.query}" is a valid steamID.')
            steamID = query.query
        else:
            logging.info(f'Fetching steamID for "{query.query}".')
            steamID = steam.get_steam_id(query.query)

        if not steamID:
            logging.info(
                f'SteamID not found for "{query.query}". Setting cache for {settings.CACHE_USER_NOT_FOUND} seconds')
            bot.answer_inline_query(query.id, [bad_query], cache_time=settings.CACHE_USER_NOT_FOUND)
            return

        logging.info(f'Fetching profile data for "{steamID}".')
        profile = steam.get_steam_profile(steamID)
        if not profile:
            logging.info(
                f'No Steam Profile found for "{steamID}". Setting cache for {settings.CACHE_USER_NOT_FOUND} seconds')
            bot.answer_inline_query(query.id, [bad_query], cache_time=settings.CACHE_USER_NOT_FOUND)
            return

        db.save_user((steamID, query.query))

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
        admin.log_to_channel(
            f'<b>User:</b> @{query.from_user.username}\n<b>id:</b> {query.from_user.id}\n' +
            f'<b>Language:</b> {query.from_user.language_code}\n<b>SteamID:</b> {steamID}\n' +
            f'<b>Steam Name</b>: {profile["username"]}\n<b>Query:</b> {query.query}')
    except Exception:
        logging.exception(f'Something happened while answering user {query.from_user.id} query "{query.query}"')


@bot.callback_query_handler(lambda c: steam.is_steam_id(c.data))
def loadSteamDB_callback(call):
    logging.info(f'Fetching SteamDB data of "{call.data}" from User {call.from_user.id}')
    bot.answer_callback_query(call.id, f'Fetching Profile of {call.data}. It may take some seconds...',
                              show_alert=False,
                              cache_time=settings.CACHE_USER_FOUND)
    bot.edit_message_text('Loading SteamDB data...', inline_message_id=call.inline_message_id)
    profile = steam.get_steamdb_profile(call.data)
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
           f'*SteamDB:*\t[Link]({profile["url_steamdb"]})')
    bot.edit_message_text('\n'.join(msg), inline_message_id=call.inline_message_id, parse_mode='MARKDOWN')
    admin.log_to_channel(
        f'<b>User:</b> @{call.from_user.username}\n<b>id:</b> {call.from_user.id}\n' +
        f'<b>Language:</b> {call.from_user.language_code}\n<b>SteamID:</b> {call.data}\n' +
        f'<b>Steam Name</b>: {profile["display_name"]}')


if __name__ == "__main__":
    main()
