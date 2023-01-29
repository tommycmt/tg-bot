import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin

import pytz
from datetime import datetime
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
# If the user drew once in the same day (CST 00:00 reset), reply the old message instead"
def draw_fortune(user_id, date):
    i = random.randrange(1,101)
    fortune = db_conn.fortune
    doc = fortune.find_one({"type": "fortuneHistory", "userId": user_id})
    if doc is not None:
        tz = pytz.timezone("Asia/Hong_Kong")
        if doc["fortuneDate"].replace(tzinfo=pytz.utc).astimezone(tz).day == datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz).day:
            # drew once within one day
            return {"found": True, "chatId": doc["chatId"], "messageId": doc["messageId"], "text" :"你今日求左啦，仲求？"}
        else:
            # delete the old record
            fortune.delete_one(doc)
    doc = fortune.find_one({"fortuneNo": str(i), "type": {"$exists": False}})
    text ="""第{}靈籤：{}
求籤吉凶：{}

算命籤詩：
{}

{}

黃大仙算命解籤詩：
{}

轉載自算命眼""".format(genNumName(doc["fortuneNo"]),
                     doc["fortuneName"],
                     doc["fortuneRank"],
                     doc["fortuneContent"],
                     doc["fortuneDesc"],
                     doc["fortuneMeaning"])
    return {"found": False, "text": text, "fortuneNo": doc["fortuneNo"]}

d = dict()
d = {0: "",
     1: "一",
     2: "二",
     3: "三",
     4: "四",
     5: "五",
     6: "六",
     7: "七",
     8: "八",
     9: "九",
     10: "十",}

# Generate the chinese-like number name
def genNumName(no):
    t = int(no)
    s = ""
    if t <= 10:
        s = d[t]
    elif t == 100:
        s = "一百"
    elif t <= 20:
        t = str(t)
        s = d[10] + d[int(t[1])]
    else:
        t = str(t)
        s = d[int(t[0])] + d[10] + d[int(t[1])]
    return s

# insert the draw history to db
def insert_fortune_history(chat_id, user_id, message_id, date, fortuneNo):
    fortune = db_conn.fortune
    doc = fortune.insert_one({"type": "fortuneHistory", "chatId": chat_id, "userId": user_id, "messageId": message_id, "fortuneDate": date, "fortuneNo": fortuneNo})
    return "OK"


async def handle_fortune(update):
    user_id = update.message.from_user.id
    date = update.message.date
    result = draw_fortune(user_id, date)

    

    # if not found, reply the draw result
    if result["found"] == False:
        # Disabled hidden message function
        #
        #promo_keyboard = telegram.InlineKeyboardButton(text="解", callback_data="fortune" + result["fortuneNo"])
        #custom_keyboard = [[promo_keyboard]]
        #reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
        #
        #message = update.message.reply_text(result["text"], reply_markup=reply_markup)
        message = await update.message.reply_text(result["text"])

        from_tz = message.date.astimezone().tzinfo
        date = message.date.replace(tzinfo=from_tz).astimezone(pytz.utc)
        
        insert_fortune_history(message.chat_id, user_id, message.message_id, date, result["fortuneNo"])
    # if found and drew in same chat group, reply the old drew result
    elif result["found"] == True and result["chatId"] == update.message.chat_id:
        await update.message.reply_text(reply_to_message_id = result["messageId"],
                                            text = result["text"])
    # if found but not in same chat group
    elif result["found"]  == True:
        await update.message.reply_text(result["text"])
