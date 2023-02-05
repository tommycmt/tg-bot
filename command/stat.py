import logging
from util.common import get_bot

import requests
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import csv

langs = ["hkt", "hks", "eng"]
bot = get_bot()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def get_yesterday():
    today = datetime.today()
    yesterday = today - timedelta(days=1)

    yesterday_year = str(yesterday.year).zfill(4)
    yesterday_month = str(yesterday.month).zfill(2)
    yesterday_day = str(yesterday.day).zfill(2)

    return yesterday_year, yesterday_month, yesterday_day

def get_opendata_with_lang(lang):
    result_list = []
    with requests.Session() as s:
        csv_url = f"https://www.immd.gov.hk/opendata/{lang}/transport/immigration_clearance/statistics_on_daily_passenger_traffic.csv"

        download = s.get(csv_url)
        logger.debug(f"CSV url: {csv_url}")

        decoded_content = download.content.decode('utf-8')

        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)

        yesterday_year, yesterday_month, yesterday_day = get_yesterday()
        yesterday_str = "{}-{}-{}".format(yesterday_day, yesterday_month, yesterday_year)
        result_list.extend(row for row in my_list if row[0] == yesterday_str)
    return result_list

def get_latest_stat_table(lang):
    yesterday_year, yesterday_month, yesterday_day = get_yesterday()
    yesterday_str = "{}{}{}".format(yesterday_year, yesterday_month, yesterday_day)
    request_url = f"https://www.immd.gov.hk/{lang}/stat_{yesterday_str}.html"
    logger.debug(f"Request url: {request_url}")

    r = requests.get(request_url)
    if (r.status_code == 404):
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.select(".table-passengerTrafficStat tbody tr")

async def compare_arrival_stat(update, each_control_point_text, opendata_row):
    chat_id = update.message.chat_id
    for index in range(4):
        if (each_control_point_text[index] != opendata_row[index+3]):
            await bot.send_message(chat_id=chat_id, text=f"Error arrival: stat on immd homepage {each_control_point_text}, stat on opendata {opendata_row}")
            return False
    return True

async def compare_departure_stat(update, each_control_point_text, opendata_row):
    chat_id = update.message.chat_id
    for index in range(4,8):
        if (each_control_point_text[index] != opendata_row[index-1]):
            await bot.send_message(chat_id=chat_id, text=f"Error departure: stat on immd homepage {each_control_point_text}, stat on opendata {opendata_row}")
            return False
    return True

async def compare_stat_with_opendata(update, lang):
    chat_id = update.message.chat_id
    stats = get_latest_stat_table(lang)
    opendata = get_opendata_with_lang(lang)

    if (stats == []):
        await bot.send_message(chat_id=chat_id, text=f"Error: {lang} stat page is not ready")
        return

    if (len(opendata) == 0):
        await bot.send_message(chat_id=chat_id, text=f"Error: missing {lang} opendata")
        return
    
    for index in range(len(stats)-1):
        stat = stats[index]
        each_control_point = stat.select(".hRight")
        each_control_point_text = list(map(lambda s: s.text.replace(",", ""), each_control_point))
        logger.debug("Stat page: " + ", ".join(each_control_point_text))
        logger.debug("Arrival opendata: " + ", ".join(opendata[index*2]))
        logger.debug("Departure opendata: " + ", ".join(opendata[index*2+1]))
        if not (await compare_arrival_stat(update, each_control_point_text, opendata[index * 2]) and await compare_departure_stat(update, each_control_point_text, opendata[index * 2 + 1])):
            return
        
    yesterday_year, yesterday_month, yesterday_day = get_yesterday()
    await bot.send_message(chat_id=chat_id, text=f"{yesterday_year}{yesterday_month}{yesterday_day} {lang} stat OK")


async def handle_stat(update): 
    global stat_last_sent
    logger.info("Start checking today stat")
    for lang in langs:
        await compare_stat_with_opendata(update, lang)