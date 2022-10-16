import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin

import pytz
from datetime import datetime

bot = get_bot()
db_conn = get_db_conn()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
# Random combination of numbers and alphabets

def handle_log(update):
    system = db_conn.system
    doc = system.find_one({"type": "log"})
    text = ""
    text += "{}\n".format(doc["msg"])
    text += "{}\n".format(doc["updateTime"])
    update.message.reply_text(text)
