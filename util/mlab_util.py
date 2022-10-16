import json
from bson import ObjectId


# JSONEncoder for encoding the return json from pymongo
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

