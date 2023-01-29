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

# Draw one from db and return a formatted text.
def draw_question():
    i = random.randrange(1,101)
    ITIL = db_conn.ITIL
    n = ITIL.estimated_document_count()
    doc = ITIL.find()[random.randrange(n)]
   
    text = "{}:{}\n".format(doc["questionNo"], doc["questionProblem"])
    for i in range(len(doc["questionOptions"])):
        text += chr(65+i) + ") " + doc["questionOptions"][i] + "\n"
    text += "Credit to Francis Yip"
    reply_markup = format_itil_kb(doc["questionNo"])
    
    return text, reply_markup


def format_itil_kb(questionNo):
    custom_keyboard = [[telegram.InlineKeyboardButton(text=str("Show Answer"), callback_data="itil" + questionNo)],
                       [telegram.InlineKeyboardButton(text=str("Change Question"), callback_data="itilchange")]]
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

async def handle_itil(update):
    text, reply_markup = draw_question()
    await update.message.reply_text(text, reply_markup=reply_markup)

async def callback_itil(update):
    data = update.callback_query.data
    if data == "itilchange":
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
        text, reply_markup = draw_question()
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
        return
    q_no = data.replace("itil","")
    ITIL = db_conn.ITIL
    doc = ITIL.find_one({"questionNo": q_no})
    text = doc["questionAns"]
    await bot.answer_callback_query(callback_query_id=update.callback_query.id, text=text, show_alert=True)
    return
