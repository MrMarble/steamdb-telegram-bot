import settings
import requests
import sqlite3
import telebot
from steamdbparser import SteamDbParser

bot = telebot.TeleBot(settings.TELEGRAM_TOKEN, skip_pending=True)


def main():
    bot.polling(True)


@bot.message_handler(commands=['start'])
def message_start(m):
    bot.send_message(m.chat.id, 'Test', True, parse_mode='MARKDOWN')


if __name__ == "__main__":
    main()
