import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder

from util.common import get_bot, is_admin, get_command

import re

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# handle pin and unpin command
def handle_pin(update):
    chat_id = update.message.chat_id
    if update.message.chat.type != "supergroup":
        update.message.reply_text("呢個group唔係supergroup, 我做唔到喎")
        return
    text = update.message.text
    message_id = update.message.message_id
    user = update.message.from_user
    g = re.match("/(\S+)[\s]*(.*)[\s]*", text)
    command = get_command(g.group(1)).lower()
    pin_message = ""
    if g.group(2) is not None:
        pin_message = g.group(2)
    if not is_admin(chat_id):
        logger.warning("No permission")
        update.message.reply_text("我唔係admin 冇權置頂或者取消置頂喎")
        return
    reply = "咪亂玩"
    if command.startswith("pin") and pin_message != "":
        reply = pin(chat_id, user, pin_message)
    elif command.startswith("unpin"):
        reply = delete_pin(chat_id)
    else:
        logger.warning("command: {}".format(command))
        logger.warning("pin_message: {}".format(pin_message))
    update.message.reply_text(reply)
    
# send the message with user first and last name then pin it
def pin(chat_id, user, pin_message):
    name = ""
    if user.first_name is not None:
        name += user.first_name
    if user.last_name is not None:
        if name != "":
            name += " " + user.last_name
        else:
            name += user.last_name
    message = bot.send_message(chat_id=chat_id, text="{}:\n{}".format(name, pin_message))
    message_id = message.message_id
    try:
        bot.pin_chat_message(chat_id, message_id)
    except telegram.error.BadRequest as e:
        logger.warning(e)
        if e.message == "Not enough rights to pin a message":
            return "我冇權置頂或者取消置頂喎"
        else:
            return "置頂唔到喎"
    return "置頂左啦"

# unpin the pinned message, return unsuccess message if failed to do so
def delete_pin(chat_id):
    try:
        bot.unpin_chat_message(chat_id)
    except telegram.error.BadRequest as e:
        logger.warning(e)
        if e.message == "Not enough rights to pin a message":
            return "我冇權置頂或者取消置頂喎"
        else:
            return "取消唔到喎"
    return "取消左置頂啦"

