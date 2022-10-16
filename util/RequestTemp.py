import requests
import json
import urllib

class RequestTemp():
    def __init__(self, url, header, payload, method):
        self.url = url
        self.header = header
        self.payload = payload
        self.method = method

    def send(self):
        payload = urllib.parse.urlencode(self.payload)
        if (self.method == "get"):
            res = requests.get(self.url+"?"+payload, headers=self.header)
        elif (self.method == "post"):
            res = requests.post(self.url, headers=self.header, data=payload)
        self.res = res
