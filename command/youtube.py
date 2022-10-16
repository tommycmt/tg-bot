import telegram
import configparser
import logging

from util.common import get_bot, is_admin

import pytube
import requests

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
           "Accept": "application/json, text/javascript, */*; q=0.01"}

def test_dl_link(url):
    r = requests.get(url, headers=headers)
    if (r.status_code == requests.codes.ok):
        return url
    else:
        logger.info(r.status_code)
        return "轉唔到喎"

def handle_youtube(update):
    url = update.message.text.split()
    link = url[1]
    yt = pytube.YouTube(link)
    converted_url = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().url
    response = test_dl_link(converted_url)
    update.message.reply_text(response)
