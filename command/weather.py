import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, is_admin

import requests
import json
import re
import pytz
from datetime import datetime

bot = get_bot()

url = "https://www.hko.gov.hk/wxinfo/json/one_json_uc.xml"


url2_signal = "https://www.hko.gov.hk/wxinfo/json/warnsumc.xml"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
           "Accept": "application/json, text/javascript, */*; q=0.01"}

weekday_dict = {"0": "日",
                "1": "一",
                "2": "二",
                "3": "三",
                "4": "四",
                "5": "五",
                "6": "六",
                "7": "日",}

def get_special_signal():
    res = requests.get(url2_signal, headers=headers)
    g = re.match(".*?({.*});$", res.content.decode('utf-8'))
    content = json.loads(g.group(1))
    signals_desc = ""
    count = 1
    for signal in content:
        if content[signal]["InForce"] == 1:
            if content[signal]["Code"].lower().startswith("tc"):
                signals_desc += "{}. {}\n".format(count, content[signal]["Type"])
            else:
                signals_desc += "{}. {}\n".format(count, ("" if content[signal]["Type"]==None else content[signal]["Type"]) + content[signal]["Name"])
            count = count + 1
            
    return signals_desc
    

# get today weather info
def get_today_weather():
    res = requests.get(url, headers=headers)
    content = json.loads(res.content)
    raw_today = content["hko"]

    current_temp = raw_today["Temperature"]
    raw_current_weather_desc = content["FLW"]["ForecastDesc"]
    clean = re.compile('<.*?>')
    current_weather_desc = re.sub(clean, '', raw_current_weather_desc)

    today_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    today_date = today_date.astimezone(pytz.timezone("Asia/Hong_Kong"))
    
    today = dict()
    today['date'] = datetime.strftime(today_date, "%Y%m%d")
    today['weekday'] = today_date.isoweekday()
    today['temp_max'] = raw_today["HomeMaxTemperature"]
    today['temp_min'] = raw_today["HomeMinTemperature"]
    return current_temp, current_weather_desc, today

# get forecast info with a specified range
def get_forecast_weather(start, end):
    res = requests.get(url, headers=headers)
    content = json.loads(res.content)
    
    forecast_list = list()
    raw_forecast = content["F9D"]["WeatherForecast"]
    for day in raw_forecast[start:end]:
        forecast = dict()
        forecast['date'] = day["ForecastDate"]
        forecast['weekday'] = day["WeekDay"]
        forecast['temp_max'] = day["ForecastMaxtemp"]
        forecast['temp_min'] = day["ForecastMintemp"]
        forecast['weather'] = day["ForecastWeather"]
        forecast_list.append(forecast)
    return forecast_list

# format today weather message
def format_today_weather_message(current_temp, current_weather_desc, today):
    text = ""
    year, month, day = re.match("(\d{4})(\d{2})(\d{2})", today['date']).groups()
    text += "{}月{}日 星期{}\n".format(month, day, weekday_dict[str(today['weekday'])])
    text += get_special_signal()
    text += "現時溫度：{}°C\n".format(current_temp)
    text += "最低溫度：{}°C 最高溫度：{}°C\n".format(today['temp_min'], today['temp_max'])
    text += "{}\n".format(current_weather_desc)
    return text

# format the forecast message
def format_forecast_weather_message(forecast_list):
    text = ""
    for forecast in forecast_list:
        year, month, day = re.match("(\d{4})(\d{2})(\d{2})", forecast['date']).groups()
        text += "{}/{} {} ".format(day, month, weekday_dict[str(forecast['weekday'])])
        text += "{} - {}°C\n".format(forecast['temp_min'], forecast['temp_max'])
        text += "{}\n".format(forecast['weather'])
    return text

# format the inline keyboard button for callbackk
def format_weather_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text=str("天氣概況"), callback_data="weather1"),
                       telegram.InlineKeyboardButton(text=str("天氣預測 1"), callback_data="weather2"),
                       telegram.InlineKeyboardButton(text=str("天氣預測 2"), callback_data="weather3")]]
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

# handle the command
async def handle_weather(update):
    current_temp, current_weather_desc, today = get_today_weather()
    text = format_today_weather_message(current_temp, current_weather_desc, today)
    reply_markup = format_weather_kb()
    await update.message.reply_text(text, reply_markup=reply_markup)
    
    
# handle the callback query
async def callback_weather(update):
    text = ""
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    # Change pages
    page_no = data.replace("weather","")
    if page_no == "1":
        current_temp, current_weather_desc, today = get_today_weather()
        text = format_today_weather_message(current_temp, current_weather_desc, today)
    elif page_no == "2":
        forecast_list = get_forecast_weather(0, 5)
        text = format_forecast_weather_message(forecast_list)
    elif page_no == "3":
        forecast_list = get_forecast_weather(5, 9)
        text = format_forecast_weather_message(forecast_list)
        text += "\n資料來源：香港天文台"
    reply_markup = format_weather_kb()
    await bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
    await bot.answer_callback_query(callback_query_id=update.callback_query.id)
    
