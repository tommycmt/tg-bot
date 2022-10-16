import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, is_admin

from bs4 import BeautifulSoup
import requests
import json
import re
import pytz
from datetime import datetime

bot = get_bot()

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
           "Accept": "application/json, text/javascript, */*; q=0.01"}



def scrape_mhwevent(week):
    url = "http://game.capcom.com/world/steam/hk/schedule.html"
    res = requests.get(url)
    bsoup = BeautifulSoup(res.text, "html.parser")
    
    time_period_tags = bsoup.select(".table2 thead tr .term")
    time_period = list(map(lambda t: t.text.replace("NOW", "").strip(), time_period_tags))[int(week)-1]
    
    title_tags = bsoup.select(".t"+ week + " .quest .title")
    content_tags = bsoup.select(".t"+ week + " .quest .txt")
    
    return time_period, title_tags, content_tags

# format the inline keyboard button for callbackk
def format_mhwevent_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="week 1", callback_data="mhwevent1"),
                       telegram.InlineKeyboardButton(text="week 2", callback_data="mhwevent2"),
                       telegram.InlineKeyboardButton(text="week 3", callback_data="mhwevent3")]]
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

def format_mhwevent_message(time_period, title_tags, content_tags):
    text = "Week: <pre>{}</pre>".format(time_period + "\n\n")
    for t, c in zip(title_tags, content_tags):
        text += t.text.strip() + "\n"
        text += c.text.strip() + "\n"
        text += "\n"
    return text

# handle the command
def handle_mhwevent(update):
    time_period, title_tags, content_tags = scrape_mhwevent("1")
    
    text = format_mhwevent_message(time_period, title_tags, content_tags)
    text += "資料來源：Monster Hunter：World：CAPCOM"
    
    reply_markup = format_mhwevent_kb()
    update.message.reply_text(text, reply_markup=reply_markup, parse_mode = "HTML")
    
    
# handle the callback query
def callback_mhwevent(update):
    text = ""
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    # Change pages
    week = data.replace("mhwevent","")
    
    time_period, title_tags, content_tags = scrape_mhwevent(week)
    text = format_mhwevent_message(time_period, title_tags, content_tags)
    reply_markup = format_mhwevent_kb()
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode = "HTML")
    bot.answer_callback_query(callback_query_id=update.callback_query.id)
    
