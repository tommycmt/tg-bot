import telegram
import configparser
import logging

from util.common import get_bot, is_admin

from googletrans import Translator

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_trans(update):
    translator = Translator()
    raw = " ".join(update.message.text.split(" ")[1:])
    text = translator.translate(raw, dest="zh-tw").text
    update.message.reply_text(text)
