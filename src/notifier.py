#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the main module of the AgileZen Notifier.

It registers to the XMPP stream and dispatches new messages to the handlers
depending on the given rules. For details see the README.md.
"""

import sys
import logging
from optparse import OptionParser
import ConfigParser
import os.path

import sleekxmpp
from sleekxmpp.stanza import Message
from sleekxmpp.stanza.htmlim import HTMLIM
from sleekxmpp.xmlstream import register_stanza_plugin

from message import AZMessage, MessageCreationException
from rules import create_handlers
import api

# To ensure that Unicode is handled properly throughout SleekXMPP for
# Python < 3, set the default encoding to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')


class XmppListener(sleekxmpp.ClientXMPP):
    """The custom XMPP listener class that forwards each incoming message
    to our handlers.
    """
    
    def __init__(self, jid, password, handlers):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.handlers = handlers
        
    def start(self, _):
        """Starting up..."""
        self.getRoster()
        self.sendPresence()
        
    def message(self, msg):
        """Check whether that's a message we are interested in, and if yes
        create an AgileZen message (AZMessage) instance and pass it to 
        each handler.
        """
        if (AZMessage.is_agilezen_xmpp_message(msg)):
            try:
                az_message = AZMessage(msg)
            except (MessageCreationException, api.APIException) as ex:
                print ex
                return None
            for handler in self.handlers:
                handler.handle(az_message)

def _start_xmpp_listener():
    """Register plugins and create xmpp listener."""
    register_stanza_plugin(Message, HTMLIM)
    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', 'notify.cfg'))
    jid = config.get('xmpp', 'jid')
    password = config.get('xmpp', 'password')
    xmpp = XmppListener(jid, password, create_handlers())
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0004') # Data Forms
    xmpp.registerPlugin('xep_0060') # PubSub
    xmpp.registerPlugin('xep_0199') # XMPP Ping
    if xmpp.connect(('talk.google.com', 5222)):
        xmpp.process(threaded=False)
        print("Done")
    else:
        print("Unable to connect.")

def _parse_options():
    """Parse command line options."""
    parser = OptionParser()
    parser.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    parser.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    parser.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)
    options, _ = parser.parse_args()
    logging.basicConfig(level=options.loglevel,
        format='%(levelname)-8s %(message)s')
    
if __name__ == '__main__':
    _parse_options()
    _start_xmpp_listener()
