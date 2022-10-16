import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_db_conn

from opencc import OpenCC

def s2hk(s):
  cc = OpenCC('s2hk')  
  to_convert = s
  converted = cc.convert(to_convert)
  return converted