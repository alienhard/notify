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


# useful for debugging        
def _send_test_messages(listener):
    msg = sleekxmpp.Message()
    msg['id'] = 'ID_1'
    msg['body'] = '[TestProject] "New **Story**;\n\nCode: `<i>003</i>`" (#18) was created by John Doe Ä'
    msg['subject'] = 'Test Subject umlaut Ä'
    msg['type'] = 'chat'
    msg['from'] = 'notifications@jabber.agilezen.com/Jabber.Net'
    msg['html'].set_body('<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml">[<a href="https://agilezen.com/project/18765">TestProject</a>] <em>&quot;New Story with umlaut Ä&quot;</em> (<a href="https://agilezen.com/project/18765/story/17">#17</a>) was moved from <strong>Done</strong> to <strong>Tested</strong> by John Doe</body></html>')
    listener.message(msg)
    
    msg = sleekxmpp.Message()
    msg['id'] = 'ID_2'
    msg['body'] = '"Add Feature X" (#20) was moved from Backlog to Ready by Foo Bar'
    msg['subject'] = 'Test Subject comment'
    msg['type'] = 'chat'
    msg['from'] = 'notifications@jabber.agilezen.com/Jabber.Net'
    msg['html'].set_body('<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml">Comment by John Doe on [Sandbox] "Bug X" (#12): Comment Y</body></html>')
    listener.message(msg)

    
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
    optp.add_option('-s', '--simulation', dest="simulation",
                    help='enable simulation', action="store_const", const=True)
    opts, args = optp.parse_args()
    
    # Setup logging
    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')
    
    # Register plugins and create xmpp listener
    register_stanza_plugin(Message, HTMLIM)
    config = ConfigParser.RawConfigParser()
    config.read('notify.cfg')
    jid = config.get('xmpp', 'jid')
    password = config.get('xmpp', 'password')
    debugging = opts.loglevel == logging.DEBUG
    xmpp = XmppListener(jid, password, create_handlers(debugging))
    
    if opts.simulation:
        print '\n\nEntering simulation. Sending fake messages...\n\n'
        _send_test_messages(xmpp)
    else:
        if xmpp.connect(('talk.google.com', 5222)):
            xmpp.process(threaded=False)
            print("Done")
        else:
            print("Unable to connect.")
            
