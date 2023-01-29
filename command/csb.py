import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, is_admin
import re
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

def format_csb_list():
    import re
    text = ""
    csb = db_conn.csb
    csb_list = csb.find({})
    
    day, month, year = csb_list[0]["advertisingDate"].split("/")
    text += "最近刊登日期：{}年{}月{}日\n".format(year, month, day)

    cs = "公務員職位：\n"
    ncsc = "非公務員職位：\n"
    unknown = ""
    
    cs_index = 1
    ncsc_index = 1
    
    for post in csb_list:
        post["post"] = re.sub(r'\[請參閱.*?\]', '', post["post"])
        if post["type"] == "cs":
            cs += "{}. {} {}\n".format(cs_index, post["dept"], post["post"])
            cs_index += 1
        elif post["type"] == "ncsc":
            ncsc += "{}. {} {}\n".format(ncsc_index, post["dept"], post["post"])
            ncsc_index += 1
        else:
            unknown += "{}. {} {}\n".format("未知", post["dept"], post["post"])
    if cs_index > 1:
        text += cs
    if ncsc_index > 1:
        text += ncsc
    return text + unknown

async def handle_csb(update):
    doc = db_conn.system.find_one({"type":"csb"})
    if doc == None:
        year, month, day = update_csb()
    else:
        update_time = doc["updateTime"].replace(tzinfo=pytz.utc).astimezone(tz)
        year = update_time.year
        month = update_time.month
        day = update_time.day

        now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
        #if update_time.day != now.day or (now - update_time).seconds >= 86400:
        year, month, day = update_csb()

    text = ""
    text += format_csb_list()
    text += "資料來源：公務員資訊網\n"
    text += "上次更新日期：{}年{}月{}日\n".format(year, month, day)
    await update.message.reply_text(text)


def compareDate(csb):
    g = re.match("(\d+)\/(\d+)\/(\d+)", csb["advertisingDate"])
    if g == None:
        return 0
    return int(g.group(1)) + int(g.group(2)) * 32 + int(g.group(3)) * 13 * 32

def update_csb():
    err = ""
    csb_list_res = requests.get(url="https://csradar.com/ajax/govjob.php",
                                   headers = {"content-type": "application/x-www-form-urlencoded",
                                              "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
                                              "origin": "https://csradar.com/",
                                              "referer": "https://csradar.com/browse-jobs"})
    csb_list_data = json.loads(csb_list_res.content)
    csb_list = csb_list_data["data"]


    csb_list = sorted(csb_list, key=compareDate)
    latest_date = csb_list[-1]["advertisingDate"]


    filtered_csb_list = []
    
    
    #for post in csb_list[::-1][0:50]:
    for post in csb_list[::-1]:
        if post["advertisingDate"] == latest_date:
            filtered_csb_list.append(post)

    csb = db_conn.csb
    csb.drop()
    csb.insert_many(filtered_csb_list)
    update_time = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
    system = db_conn.system
    system.delete_one({"type": "csb"})
    system.insert_one({"type": "csb", "updateTime": update_time, "err": err})
    update_time_local = update_time.astimezone(tz)
    return update_time_local.year, update_time_local.month, update_time_local.day


    
