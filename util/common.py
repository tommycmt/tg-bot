import telegram
import configparser
import logging

import pymongo
import dns
from util.mlab_util import JSONEncoder
from telegram.request import HTTPXRequest
import openai

import re

# Load data from config.ini file
secure_config = configparser.ConfigParser()
secure_config.read('config/secure-config.ini')

config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

request = HTTPXRequest(connection_pool_size=68, connect_timeout=5, read_timeout=5)

bot = telegram.Bot(token=(secure_config['TELEGRAM']['ACCESS_TOKEN']),request=request)
#mlab_client = pymongo.MongoClient(secure_config['MLAB']['URL'], retryWrites=False)
mlab_client = pymongo.MongoClient(secure_config['MONGO']['URL'])
db_conn = mlab_client['boomja-bot']
openai.api_key = secure_config['OPENAI']['key']

def get_openai():
    return openai

def get_bot():
    return bot

def get_db_conn():
    return db_conn

async def is_admin(chat_id):
    bot_user_id = bot.id
    chat_members = (await bot.getChatAdministrators(chat_id))
    for member in chat_members:
        if member.user.id == bot_user_id:
            return True
    return False

def get_command(text):
    text = text.lower()
    pattern = "/*(\w*)(@" + bot.name.lower()+")?"
    g = re.match(pattern, text)
    if g is not None:
        return g.group(1).lower()
    return text

def get_user_name(user):
    name = ""
    if user.first_name is not None:
        name += user.first_name
    if user.last_name is not None:
        if name != "":
            name += " " + user.last_name
        else:
            name += user.last_name
    return name
