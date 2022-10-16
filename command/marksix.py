import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin

import requests, json

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draw.json"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
           "Accept": "application/json, text/javascript, */*; q=0.01"}


# Get a last mark six result
# return the reply text
def get_last_marksix_result():
    res = requests.get(url, headers=headers)
    content = json.loads(res.content)
    date = content[0]["date"]
    no_list = content[0]["no"].split("+")
    sno = content[0]["sno"]
    text = "上期六合彩 ({})\n".format(date)
    text+= "攪珠結果：{}\n".format(" ".join(no_list))
    text+= "特別號碼：{}".format(sno)
    return text


def handle_marksix(update):
    update.message.reply_text(get_last_marksix_result())

