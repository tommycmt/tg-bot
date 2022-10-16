import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin, get_command

import re, datetime, random
import requests, json

bot = get_bot()
db_conn = get_db_conn()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# /addstock 66 5 2388
# /delstock 5 2388
# /showstock
# /showstock 2388 3988
# /mystock

def handle_stock(update):
    text = update.message.text.lower()
    # spilt the command and stock list
    g = re.match("/(\S+)[\s]*((?:\d+[\s]*)*\d)?", text)
    command = get_command(g.group(1))
    formatted_stock_list = []
    if (g.group(2) is not None):
        stock_list = g.group(2).split()
        formatted_stock_list = [str(int(stock)) for stock in stock_list]
    user_id = update.message.from_user.id
    reply = "咪亂玩"
    if command == "addstock" and formatted_stock_list != []:
        reply = add_stocks(user_id, formatted_stock_list)
    elif command == "delstock" and formatted_stock_list != []:
        reply = del_stocks(user_id, formatted_stock_list)
    elif command == "showstock":
        if text == "/showstock hsi":
          reply = show_HSI()
        else:
          reply = show_HSI() + "\n" + show_stocks(user_id, formatted_stock_list)
    elif command == "mystock":
        reply = show_user_stock_profile(user_id)
    else:
        logger.warning("command: {}".format(command))
        logger.warning("formatted_stock_list: {}".format(formatted_stock_list))
    update.message.reply_text(reply)
    
# add stocks number(s) to user's profile
def add_stocks(user_id, stock_list):
    stock = db_conn.stock
    old_doc = stock.find_one({"userId": user_id})
    old_stockList = []
    if old_doc is not None:
        old_stockList = old_doc["stockList"]
        stock.delete_one(old_doc)
    doc = dict()
    doc["userId"] = user_id
    new_stockList = list(set(old_stockList + stock_list))
    doc["stockList"] = new_stockList
    stock.insert_one(doc)
    return "加左啦，快啲睇下啦"

# delete stocks number(s) to user's profile
def del_stocks(user_id, stock_list):
    
    stock = db_conn.stock
    old_doc = stock.find_one({"userId": user_id})
    old_stockList = []
    if old_doc is not None:
        old_stockList = old_doc["stockList"]
        stock.delete_one(old_doc)
    doc = dict()
    doc["userId"] = user_id
    new_stockList = list(set(old_stockList) - set(stock_list))
    doc["stockList"] = new_stockList
    stock.insert_one(doc)
    return "冇左啦，快啲睇下啦"

# show stocks, if stock_list is empty then show the specfied stocks
# else show those stock stored in user's profile
def show_stocks(user_id, stock_list):
    stock = db_conn.stock
    if stock_list == []:
        doc = stock.find_one({"userId": user_id})
        if doc is None or doc["stockList"] == []:
            return "玩野？你未加野入黎喎"
        stock_list = doc["stockList"]
        result_dict = sync_get_all_stock(stock_list)
    else:
        result_dict = sync_get_all_stock(stock_list)
    reply = ""
    for stock in sorted(result_dict):
        if result_dict[stock][0] == "":
            reply +="{} {}: {}\n".format(str(stock).zfill(4), result_dict[stock][0], result_dict[stock][1])
        else:
            reply += "{} {}: ${}\n".format(str(stock).zfill(4), result_dict[stock][0], result_dict[stock][1])
    return reply
    
def show_HSI():
    name, current_price, today_change = get_stock_price("HSI")
    reply = ""
    reply += "{} {} ({})\n".format(name, current_price, today_change)
    return reply

# show user profile
def show_user_stock_profile(user_id):
    stock = db_conn.stock
    doc = stock.find_one({"userId": user_id})
    if doc is not None:
        if doc["stockList"] != []:
            reply = ""
            for stock in doc["stockList"]:
                reply += "{}\n".format(stock.zfill(4))
            return reply
    return "玩野？你未加野入黎喎"

# get a stock price by the stock number
def get_stock_price(stock_no):
    if stock_no == "HSI":
        url_1 = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
        url_2 = "?formatted=true&lang=HK&region=HK&modules=price&corsDomain=hk.finance.yahoo.com"
        res = requests.get(url_1 + "%5EHSI" + url_2, headers={"accept-language": "zh-TW;q=0.8,zh;q=0.7"})
        stock_info = json.loads(res.content)
        current_price = stock_info["quoteSummary"]["result"][0]["price"]["regularMarketPrice"]["fmt"]
        name = stock_info["quoteSummary"]["result"][0]["price"]["longName"]
        today_change = stock_info["quoteSummary"]["result"][0]["price"]["regularMarketChange"]["fmt"]
        return name, current_price, today_change
    else:
        url_1 = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
        url_2 = ".HK?formatted=true&lang=HK&region=HK&modules=price&corsDomain=hk.finance.yahoo.com"
        res = requests.get(url_1 + stock_no.zfill(4) + url_2, headers={"accept-language": "zh-TW;q=0.8,zh;q=0.7"})
        stock_info = json.loads(res.content)
        current_price = stock_info["quoteSummary"]["result"][0]["price"]["regularMarketPrice"]["fmt"]
        name = stock_info["quoteSummary"]["result"][0]["price"]["longName"]
        return stock_no, name, current_price

# format the result of all stock to a dict
def sync_get_all_stock(stock_list):
    import time
    result_dict = dict()
    for stock in stock_list:
        try:
            stock_no, name, price = get_stock_price(stock)
            result_dict[int(stock_no)] = (name, price)
        except:
            logger.warning("can't find {}".format(stock))
            result_dict[int(stock)] = ("", "唔存左啦")
    logger.info(result_dict)
    return result_dict



