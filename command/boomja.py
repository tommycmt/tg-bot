import telegram
import configparser
import logging

from util.common import get_bot, is_admin, get_openai, get_command

import random
import string
import re
import openai

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
# Random combination of numbers and alphabets
def chat_ai(question):
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=f"Human: {question} \n AI:",
    temperature=0.9,
    max_tokens=999,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.6,
    stop=[" Human:", " AI:"]
    )

    res = response['choices'][0]['text']
    if res.startswith("？") or res.startswith("?"):
        res = res[1:]
    return res.strip()

def reply_handler(update):
    text = update.message.text
    g = re.match("/(\S+)[\s]*(.*)[\s]*", text)
    question = ""
    if g.group(2) is not None:
        question = g.group(2)
        res = chat_ai(question)
    return res


async def handle_boomja(update):
    await update.message.reply_text(reply_handler(update))
