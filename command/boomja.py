import telegram
import configparser
import logging

from util.common import get_bot, is_admin

import random
import string

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
# Random combination of numbers and alphabets
def boomja_random_word():
    return randomword(random.randint(1,100))
    
def randomword(i):
    if i == 0:
        return ""
    return randomword(i-1) + random.choice(string.ascii_letters)


def handle_boomja(update):
    update.message.reply_text(boomja_random_word())
