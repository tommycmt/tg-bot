import telegram
import configparser
import logging

from util.common import get_bot, is_admin
from util.chinese_convert import s2hk
from util.logging import write_log_msg_to_db

import wikipedia

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_wiki(update):
    wikipedia.set_lang("zh-tw")
    query = " ".join(update.message.text.split(" ")[1:])
    try:
        result = wikipedia.page(query)
        update.message.reply_text(s2hk(result.summary))
    except Exception as e:
        update.message.reply_text("搵唔到喎")
        write_log_msg_to_db(e)
