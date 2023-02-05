import configparser
import logging


import telegram, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, MessageHandler, filters, CallbackContext, Updater

from flask import Flask, request
import requests
import datetime

import pymongo

from command.fortune import handle_fortune
from command.boomja import handle_boomja
from command.sgs import handle_sgs
from command.toss import handle_toss
from command.weather import handle_weather, callback_weather
from command.dicegame import handle_dicegame, callback_dicegame
from command.marksix import handle_marksix
from command.blackjack import handle_blackjack, callback_blackjack
from command.csb import handle_csb
from command.cards import handle_cards
from command.poker import handle_poker, callback_poker
from command.itil import handle_itil, callback_itil
from command.stat import handle_stat
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
async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command message."""
    logger.info(update)
    new_message = update.message.text.lower()
    try:
        if (new_message.startswith("/fortune")):
            await handle_fortune(update)
        elif (new_message.startswith("/boomja")):
            await handle_boomja(update)
        elif (new_message.startswith("/sgs")):
            await handle_sgs(update)
        elif (new_message.startswith(("/toss"))):
            await handle_toss(update)
        elif (new_message.startswith(("/weather"))):
            await handle_weather(update)
        elif (new_message.startswith(("/dicegame"))):
            await handle_dicegame(update)
        elif (new_message.startswith(("/marksix"))):
            await handle_marksix(update)
        elif (new_message.startswith(("/blackjack"))):
            await handle_blackjack(update)
        elif (new_message.startswith(("/csb"))):
            await handle_csb(update)
        elif (new_message.startswith(("/cards"))):
            await handle_cards(update)
        elif (new_message.startswith(("/poker"))):
            await handle_poker(update)
        elif (new_message.startswith(("/itil"))):
            await handle_itil(update)
        elif (new_message.startswith(("/stat"))):
            await handle_stat(update)
        elif (new_message.startswith(("/log"))):
            await handle_log(update)
    except Exception as e:
        logger.exception(e)
        logger.warning(update)
        write_log_msg_to_db(e)
        await update.message.reply_text("你個野壞左呀")

# React to plain text message
async def boomja_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(update)
    try:
        new_message = update.message.text.lower()
        chat_id = update.message.chat_id
        if (new_message in ["rip", "mgl"]):
            if (random.random() > 0.6):
                await bot.send_message(chat_id=chat_id, text=random.choice(["rip", "mgl", ":O"]))
                await send_shit(update, chat_id, 30)
        elif (new_message.startswith(("me le", "mele"))):
            if (random.random() > 0.5):
                await bot.send_message(chat_id=chat_id, text=random.choice(["no u fun", "me leeeee"]))
                await send_shit(update, chat_id, 30)
        elif (new_message == "98"):
            await bot.send_message(chat_id=chat_id, text="98")
            await send_shit(update, chat_id, 85)
        else:
            await send_shit(update, chat_id, 15)
    except Exception as e:
        logger.exception(e)
        write_log_msg_to_db(e)


# React the callback function
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(update)
    try:
      if update.callback_query.data.startswith("weather"):
          try: 
              await callback_weather(update)
          except AttributeError as e:
              logger.warning(e)
      elif update.callback_query.data.startswith("dice"):
          try: 
              await callback_dicegame(update)
          except AttributeError as e:
              logger.warning(e)
      elif update.callback_query.data.startswith("blackjack"):
          try: 
              await callback_blackjack(update)
          except AttributeError as e:
              logger.warning(e)
      elif update.callback_query.data.startswith("poker"):
          try: 
              await callback_poker(update)
          except AttributeError as e:
              logger.warning(e)
      elif update.callback_query.data.startswith("itil"):
          try: 
              await callback_itil(update)
          except AttributeError as e:
              logger.warning(e)
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


def main():
    application = ApplicationBuilder().bot(bot).build()
    
    application.add_handler(MessageHandler((filters.COMMAND), callback=command_handler))
    application.add_handler(MessageHandler((filters.TEXT), callback=boomja_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    #application.run_polling()

    application.run_webhook(
    listen='0.0.0.0',
    cert='cert/webhook_cert.pem',
    key='cert/webhook_pkey.key',
    port=8443,
    webhook_url='https://keymantommy.asuscomm.com:8443/',
    secret_token=secure_config['TELEGRAM']['SECRET_TOKEN'])

    print(application.bot.getWebhookInfo().to_dict())

if __name__ == '__main__':
    main()
    


    


