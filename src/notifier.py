#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the main module of the AgileZen Notifier.

It registers to the XMPP stream and dispatches new messages to the handlers
depending on the given rules. For details see the README.md.
"""

import sys
import logging
import time
import re
import os.path
from optparse import OptionParser
import ConfigParser

import sleekxmpp
from sleekxmpp.stanza import Message
from sleekxmpp.stanza.htmlim import HTMLIM
from sleekxmpp.xmlstream import ET, register_stanza_plugin

from message import AZMessage, MessageCreationException
from rules import create_handlers
import api

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')


class XmppListener(sleekxmpp.ClientXMPP):
    
    def __init__(self, jid, password, handlers):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.handlers = handlers
        
    def start(self, event):
        self.getRoster()
        self.sendPresence()
        
    def message(self, msg):
        if (AZMessage.is_agilezen_xmpp_message(msg)):
            try:
                az_message = AZMessage(msg)
            except (MessageCreationException, api.APIException) as e:
                print e
                return None
            for handler in self.handlers:
                handler.handle(az_message)

def _start_xmpp_listener(debugging=False):
    """Register plugins and create xmpp listener."""
    register_stanza_plugin(Message, HTMLIM)
    config = ConfigParser.RawConfigParser()
    config.read('notify.cfg')
    jid = config.get('xmpp', 'jid')
    password = config.get('xmpp', 'password')
    xmpp = XmppListener(jid, password, create_handlers(debugging))
    if xmpp.connect(('talk.google.com', 5222)):
        xmpp.process(threaded=False)
        print("Done")
    else:
        print("Unable to connect.")

if __name__ == '__main__':
    optp = OptionParser()
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)
    opts, args = optp.parse_args()
    logging.basicConfig(level=opts.loglevel,
        format='%(levelname)-8s %(message)s')
    debugging = opts.loglevel == logging.DEBUG
    _start_xmpp_listener(debugging)
