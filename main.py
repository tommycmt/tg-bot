import configparser
import logging

import telegram
from telegram.ext import Updater, Dispatcher, MessageHandler, Filters, CallbackQueryHandler, run_async

from flask import Flask, request
import requests
import datetime

import pymongo

from command.fortune import handle_fortune
from command.boomja import handle_boomja
from command.sgs import handle_sgs
from command.stock import handle_stock
from command.toss import handle_toss
from command.movie import handle_movie, callback_movie
from command.weather import handle_weather, callback_weather
from command.pin import handle_pin
from command.dicegame import handle_dicegame, callback_dicegame
from command.marksix import handle_marksix
from command.blackjack import handle_blackjack, callback_blackjack
from command.csb import handle_csb
from command.youtube import handle_youtube
from command.cards import handle_cards
from command.poker import handle_poker, callback_poker
from command.trans import handle_trans
from command.howdoi import handle_howdoi
from command.mhwevent import handle_mhwevent, callback_mhwevent
from command.ibevent import handle_ibevent, callback_ibevent
from command.itil import handle_itil, callback_itil
from command.log import handle_log

from boomja.shit import send_shit

from util.common import get_bot, get_db_conn
from util.logging import write_log_msg_to_db

import random, os

# Load data from config.ini file
secure_config = configparser.ConfigParser()
secure_config.read('config/secure-config.ini')

config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

if (config['ENV']['PRODUCTION'] == "TRUE"):
    logger.setLevel(logging.WARNING)

# Initial bot by Telegram access token
bot = get_bot()
db_conn = get_db_conn()

# React to command message
def command_handler(bot, update):
    """Command message."""
    logger.info(update)
    new_message = update.message.text.lower()
    try:
        
        if (new_message.startswith("/fortune")):
            handle_fortune(update)
        elif (new_message.startswith("/boomja")):
            handle_boomja(update)
        elif (new_message.startswith("/sgs")):
            handle_sgs(update)
        elif (new_message.startswith(("/addstock", "/delstock", "/showstock", "/mystock"))):
            handle_stock(update)
        elif (new_message.startswith(("/toss"))):
            handle_toss(update)
        elif (new_message.startswith(("/movie"))):
            handle_movie(update)
        elif (new_message.startswith(("/weather"))):
            handle_weather(update)
        elif (new_message.startswith(("/pin", "/unpin"))):
            handle_pin(update)
        elif (new_message.startswith(("/dicegame"))):
            handle_dicegame(update)
        elif (new_message.startswith(("/marksix"))):
            handle_marksix(update)
        elif (new_message.startswith(("/blackjack"))):
            handle_blackjack(update)
        elif (new_message.startswith(("/csb"))):
            handle_csb(update)
        elif (new_message.startswith(("/youtube"))):
            handle_youtube(update)
        elif (new_message.startswith(("/cards"))):
            handle_cards(update)
        elif (new_message.startswith(("/poker"))):
            handle_poker(update)
        elif (new_message.startswith(("/trans"))):
            handle_trans(update)
        elif (new_message.startswith(("/howdoi"))):
            handle_howdoi(update)
        elif (new_message.startswith(("/mhwevent"))):
            handle_mhwevent(update)
        elif (new_message.startswith(("/ibevent"))):
            handle_ibevent(update)
        elif (new_message.startswith(("/itil"))):
            handle_itil(update)
        elif (new_message.startswith(("/log"))):
            handle_log(update)
          
    except Exception as e:
        logger.exception(e)
        logger.warning(update)
        write_log_msg_to_db(e)
        update.message.reply_text("你個野壞左呀")

# React to plain text message
def boomja_handler(bot, update):
    logger.info(update)
    try:
        new_message = update.message.text.lower()
        chat_id = update.message.chat_id
        if (new_message in ["rip", "mgl"]):
            if (random.random() > 0.6):
                bot.send_message(chat_id=chat_id, text=random.choice(["rip", "mgl", ":O"]))
            send_shit(update, chat_id, 30)
        elif (new_message.startswith(("me le", "mele"))):
            if (random.random() > 0.5):
                bot.send_message(chat_id=chat_id, text=random.choice(["no u fun", "me leeeee"]))
                send_shit(update, chat_id, 30)
        elif (new_message == "98"):
            bot.send_message(chat_id=chat_id, text="98")
            send_shit(update, chat_id, 85)
        else:
            send_shit(update, chat_id, 15)

        if (new_message.startswith("cheat:")):
            m = new_message.replace("cheat:","")
            bot.send_message(chat_id="-1001312488810", text=m)
    except Exception as e:
        logger.exception(e)
        write_log_msg_to_db(e)


# React the callback function
def callback_handler(bot, update):
    logger.info(update)
    try:
      if update.callback_query.data.startswith("movie"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_movie(bot, update, db_conn)
              callback_movie(update)
          except AttributeError as e:
              logger.warning(e)
              callback_movie(update)
      elif update.callback_query.data.startswith("weather"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_weather(update)
          except AttributeError as e:
              logger.warning(e)
              callback_weather(update)
      elif update.callback_query.data.startswith("dice"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_dicegame(update)
          except AttributeError as e:
              logger.warning(e)
              callback_dicegame(update)
      elif update.callback_query.data.startswith("blackjack"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_blackjack(update)
          except AttributeError as e:
              logger.warning(e)
              callback_blackjack(update)
      elif update.callback_query.data.startswith("poker"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_poker(update)
          except AttributeError as e:
              logger.warning(e)
              callback_poker(update)
      elif update.callback_query.data.startswith("mhwevent"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_mhwevent(update)
          except AttributeError as e:
              logger.warning(e)
              callback_mhwevent(update)
      elif update.callback_query.data.startswith("ibevent"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_ibevent(update)
          except AttributeError as e:
              logger.warning(e)
              callback_ibevent(update)
      elif update.callback_query.data.startswith("itil"):
          callback_user_id = update.callback_query.from_user.id
          try: 
              #message_user_id = update.callback_query.message.reply_to_message.from_user.id
              #if callback_user_id == message_user_id:
              #    callback_weather(bot, update)
              callback_itil(update)
          except AttributeError as e:
              logger.warning(e)
              callback_itil(update)
    except telegram.error.TimedOut as timeout:
        logger.warning("timeout")
        write_log_msg_to_db(timeout)
    except telegram.error.BadRequest as e:
        write_log_msg_to_db(e)
        if str(e) == 'Message is not modified':
            logger.warning("Message is not modified")
        else:
            raise # re-raise BadRequest because string not recognized
    except Exception as ee:
        write_log_msg_to_db(ee)


        
# New a dispatcher for bot

# Add handlers for handling message.

if __name__ == '__main__':
    updater = Updater(bot=bot, workers=4)
    updater.dispatcher.add_handler(MessageHandler((Filters.command), command_handler))
    updater.dispatcher.add_handler(MessageHandler((Filters.text), boomja_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    updater.start_webhook(listen="0.0.0.0", port=int(80)
    updater.idle()
