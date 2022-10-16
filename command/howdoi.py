import telegram
import configparser
import logging

from util.common import get_bot, is_admin

from howdoi import howdoi

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_howdoi(update):
    query = update.message.text.split(" ")[1:]
    parser = howdoi.get_parser()
    args = vars(parser.parse_args(query))
    text = howdoi.howdoi(args)
    update.message.reply_text(text)
