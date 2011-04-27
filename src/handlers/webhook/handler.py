"""A Webhook handler that notifies another server about events by
sending HTTP requests to some URL.
"""

import os
import urllib
import httplib
import json
from ConfigParser import RawConfigParser


CFG_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'notify.cfg')
CONFIG = RawConfigParser()
CONFIG.read(CFG_PATH)
HOOK_HOST = CONFIG.get('webhook', 'host')
HOOK_PATH = CONFIG.get('webhook', 'path')


class WebhookHandler():
    
    def __init__(self, interested_in, host=HOOK_HOST, path=HOOK_PATH):
        self.interested_in = interested_in
        self.host = host
        self.path = path
        
    def handle(self, message):
        if self.interested_in(message):
            self._send_request(message)
        
    def _send_request(self, message):
        data = {
            'project_id':message.project_id,
            'story_id':message.story_id,
            'text':message.text,
            'status':message.status,
            'tags':message.tags,
            'creator':message.creator,
            'creator_mail':message.creator_mail
        }
        header = {"Content-type": "application/json"}
        params = urllib.urlencode(data)
        conn = httplib.HTTPConnection(self.host, timeout=10)
        conn.request("PUT", self.path, json.dumps(data), header)