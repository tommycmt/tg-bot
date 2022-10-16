import configparser
import logging

import telegram
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackQueryHandler

from util.common import get_bot

import random

bot = get_bot()

def send_shit(update, chat_id, chance):    
    if random.random() < (chance/100):
        bot.send_message(chat_id=chat_id, text="\U0001F4A9")
