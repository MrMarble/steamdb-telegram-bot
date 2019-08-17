import telebot

from . import settings


class Admin:
    def __init__(self):
        self.bot = telebot.TeleBot(token=settings.TELEGRAM_TOKEN, skip_pending=True)

    def log_to_channel(self, message):
        if settings.LOG_CHANNEL:
            self.bot.send_message(chat_id=settings.LOG_CHANNEL, text=message, disable_web_page_preview=True,
                                  disable_notification=True, parse_mode='HTML'
                                  )
