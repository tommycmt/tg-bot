import telegram
import configparser
import logging

from util.common import get_bot, is_admin

import random

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_quit(update):
    qa =   [("Q: 點解走", "A: 因為我覺得GT Scheme 唔係好啱我，都係想focus係development到。 好似GT project 咁要做好多額外既工作，大家又唔係好想做。"),
            ("Q: 唔使你做GT Project", "A: 唔好做壞規矩，GT project 原意好，可能只係我唔適合。"),
            ("Q: 加你人工", "A: 如果俾同事同朋友知道左就好難做"),
            ("Q: 係唔係已經搵到工", "A: 未，暫時想抖下。我之前in過，佢地要時間考慮，但一直都冇打黎叫我番。")]


    text = random.choice(qa)
    update.message.reply_text(text[0] + "\n" + text[1])
