import telegram
import configparser
import logging, os

from util.common import get_bot, is_admin, get_command

import random

bot = get_bot()

def handle_toss(update):
    message_list = update.message.text.split()
    message_list[0] = get_command(message_list[0])
    if message_list[0] == "toss":
        if len(message_list) > 1:
            text = random.choice(message_list[1:])
        update.message.reply_text(text)
