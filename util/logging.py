import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_db_conn

import re
from datetime import datetime
import pytz
import traceback

db_conn = get_db_conn()
tz = pytz.timezone("Asia/Hong_Kong")

def write_log_msg_to_db(e):
    update_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    update_time_local = update_time.astimezone(tz)
    
    system = db_conn.system
    system.delete_one({"type": "log"})
    system.insert_one({"type": "log", "updateTime": update_time_local, "msg":  str(traceback.format_exc()), "e": str(e)})
