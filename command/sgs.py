import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin

import random

bot = get_bot()
db_conn = get_db_conn()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Get a random SGS quote from DB
# return as a string
def getHeroQuote():    
    SGSQuote = db_conn.SGSQuote
    n = SGSQuote.count()
    i = random.randrange(0, n+1)
    doc = SGSQuote.find_one({"id": str(i)})
    # Disabled message, show hero name also
    # text ="({})：{}".format(doc["heroName"], doc["heroQuote"])
    text ="{}".format(doc["heroQuote"])
    return text


def handle_sgs(update):
    update.message.reply_text(getHeroQuote())

