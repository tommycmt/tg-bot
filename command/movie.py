import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin

import json, requests
import pytz
import math
from datetime import datetime

tz = pytz.timezone("Asia/Hong_Kong")
bot = get_bot()
db_conn = get_db_conn()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the a page of movies (6 movies) from db
def get_movie_list(page_no):
    movie = db_conn.movie
    movie_list = movie.find({"id": {"$gte": (page_no-1) * 6 + 1, "$lte": page_no * 6}}, {"id": 1, "chiName": 1, "name": 1, "openDate": 1}).sort("id", pymongo.ASCENDING)
    return movie_list

# Get the detail information of a specific movie from db
def get_movie(movie_id):
    movie = db_conn.movie
    movie_data = movie.find_one({"id":movie_id}, {"id": 1, "chiName": 1, "name": 1, "openDate": 1, "chiInfoDict": 1, "infoDict": 1, "chiSynopsis":1, "synopsis":1, "dbTrailerUrl": 1})
    return movie_data

# Get the total page of movies by count the size of db and divided by 6
def get_max_page():
    movie = db_conn.movie
    max_page = math.ceil(movie.count() / 6)
    return max_page


# format the movie list message
def format_movie_list(movie_list):
    text = ""
    for movie in movie_list:
        movie_id = movie["id"]
        if "chiName" in movie:
            movie_name = movie["chiName"]
        else:
            movie_name = movie["name"]
        if "openDate" in movie:
            movie_open_date = datetime.strptime(movie["openDate"], "%a %d %b %Y %H:%M:%S")
            movie_open_date_year = str(movie_open_date.year)
            movie_open_data_month = str(movie_open_date.month)
            movie_open_date_day = str(movie_open_date.day)
            text += "{}. {} {}年{}月{}日\n".format(movie_id, movie_name, movie_open_date_year, movie_open_data_month, movie_open_date_day)
        else:
            text += "{}. {}\n".format(movie_id, movie_name)
    return text


# format the detail information message of a specific movie
def format_movie_detail(movie):
    text = ""
    movie_id = movie["id"]
    if "chiName" in movie:
        movie_name = movie["chiName"]
    else:
        movie_name = movie["name"]
    text += "{}. {}\n\n".format(movie_id, movie_name)
    if "openDate" in movie:
        movie_open_date = datetime.strptime(movie["openDate"], "%a %d %b %Y %H:%M:%S")
        movie_open_date_year = str(movie_open_date.year)
        movie_open_data_month = str(movie_open_date.month)
        movie_open_date_day = str(movie_open_date.day) 
        text += "上映日期： {}年{}月{}日\n".format(movie_open_date_year, movie_open_data_month, movie_open_date_day)
    if "chiInfoDict" in movie:
        if "演員" in movie["chiInfoDict"]:
            text += "演員： {}\n".format(movie["chiInfoDict"]["演員"])
        if "語言" in movie["chiInfoDict"]:
            text += "語言： {}\n".format(movie["chiInfoDict"]["語言"])
        if "級別" in movie["chiInfoDict"]:
            text += "級別： {}\n".format(movie["chiInfoDict"]["級別"])
        if "導演" in movie["chiInfoDict"]:
            text += "導演： {}\n".format(movie["chiInfoDict"]["導演"])
        if "片長" in movie["chiInfoDict"]:
            text += "片長： {}\n".format(movie["chiInfoDict"]["片長"])
        if "類型" in movie["chiInfoDict"]:
            text += "類型： {}\n".format(movie["chiInfoDict"]["類型"])
    else:
        if "Cast" in movie["infoDict"]:
            text += "演員： {}\n".format(movie["infoDict"]["Cast"])
        if "Language" in movie["infoDict"]:
            text += "語言： {}\n".format(movie["infoDict"]["Language"])
        if "Category" in movie["infoDict"]:
            text += "級別： {}\n".format(movie["infoDict"]["Category"])
        if "Director" in movie["infoDict"]:
            text += "導演： {}\n".format(movie["infoDict"]["Director"])
        if "Duration" in movie["infoDict"]:
            text += "片長： {}\n".format(movie["infoDict"]["Duration"])
        if "Genre" in movie["infoDict"]:            
            text += "類型： {}\n".format(movie["infoDict"]["Genre"])
    text += "\n"
    if "chiSynopsis" in movie:
        text += "故事簡介：\n{}\n\n".format(movie["chiSynopsis"])
    elif "synopsis" in movie:
        text += "故事簡介：\n{}\n\n".format(movie["synopsis"])
    if "dbTrailerUrl" in movie:
        text += "預告片：\n{}\n".format(movie["dbTrailerUrl"].replace(",","\n\n"))
    return text

# format the inline keyboard button for callbackk
def format_movie_kb(page_no, max_page):
    custom_keyboard = [[telegram.InlineKeyboardButton(text=str(i), callback_data="movie" + str(i)) for i in range((page_no-1) * 6 + 1, (page_no-1) * 6 + 4)],
                       [telegram.InlineKeyboardButton(text=str(i), callback_data="movie" + str(i)) for i in range((page_no-1) * 6 + 4, (page_no)   * 6 + 1)],
                       [telegram.InlineKeyboardButton(text="<-", callback_data="moviepage" + str(page_no - 1)),
                        telegram.InlineKeyboardButton(text=str(page_no) + "/" + str(max_page), callback_data="moviepage"+ str(page_no)),
                        telegram.InlineKeyboardButton(text="->", callback_data="moviepage" + str(page_no + 1))]]
    
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

# handle the movie command
def handle_movie(update):
    page_no = 1
    movie_list = get_movie_list(page_no)
    max_page = get_max_page()
    
    doc = db_conn.system.find_one({"type":"movie"})
    year = doc["updateTime"].year
    month = doc["updateTime"].month
    day = doc["updateTime"].day

    if doc["updateTime"].replace(tzinfo=pytz.utc).astimezone(tz).day != datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz).day:
        year, month, day = update_movie()
    
    text = "資料來源：hkmovie6\n"
    text += "上次更新日期：{}年{}月{}日\n".format(year, month, day)
    
    text += format_movie_list(movie_list)
    reply_markup = format_movie_kb(page_no, max_page)
    update.message.reply_text(text, reply_markup=reply_markup)

# handle the callback query
def callback_movie(update):
    max_page = get_max_page()
    text = ""
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    
    if data.startswith("moviepage"):
        # Change pages
        page_no = int(data.replace("moviepage",""))
        if page_no < 1 or page_no > max_page:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="盡啦", show_alert=True)
            return
        else:
            movie_list = get_movie_list(page_no)
            text = format_movie_list(movie_list)
            reply_markup = format_movie_kb(page_no, max_page)
    else:
        # view a movie detail
        movie_id = int(data.replace("movie",""))
        movie_data = get_movie(movie_id)
        if movie_data == None:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="搵唔到喎", show_alert=True)
            return
        text = format_movie_detail(movie_data)
        reply_markup = format_movie_kb(math.ceil(movie_id / 6), max_page)
    bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, disable_web_page_preview=True)
    bot.answer_callback_query(callback_query_id=update.callback_query.id)

def update_movie():
    err = ""
    movie_list_res = requests.post(url="https://hkmovie6.com/api/movies/lists",
                                   data="type=showing",
                                   headers = {"content-type": "application/x-www-form-urlencoded",
                                              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
                                              "origin": "https://hkmovie6.com",
                                              "referer": "https://hkmovie6.com/showing"})
    movie_list_data = json.loads(movie_list_res.content)
    movie_list = movie_list_data["data"]
    #movie_list.sort(key=lambda d: datetime.strptime(d["openDate"], "%a %d %b %Y %H:%M:%S").timestamp())
    movie_list.sort(key=lambda m: m["interestingness"] if "interestingness" in m else 0, reverse=True)
    new_id = 1
    for movie in movie_list:
        movie["id"] = new_id
        new_id += 1

    movie = db_conn.movie
    movie.drop()
    movie.insert_many(movie_list)
    update_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    system = db_conn.system
    system.delete_one({"type": "movie"})
    system.insert_one({"type": "movie", "updateTime": update_time, "err": err})
    update_time_local = update_time.astimezone(tz)
    return update_time_local.year, update_time_local.month, update_time_local.day


    
