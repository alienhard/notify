"""A handler that sends mails."""

import sys
import re
import smtplib
import ConfigParser
import os.path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# load config
config = ConfigParser.RawConfigParser()
config.read(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'notify.cfg'))    
SENDER_MAIL = config.get('mail', 'sender')
SMPT_SERVER = config.get('mail', 'smtp_server')


class MailHandler():
    
    def __init__(self, interested_in, getrecipients):
        self.interested_in = interested_in
        self.getrecipients = getrecipients
        
    def handle(self, message):
        if (not self.interested_in(message)):
            return None
        recipients = self.getrecipients(message)
        if len(recipients) == 0:
            return None
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.title
        msg['From'] = SENDER_MAIL
        part1 = MIMEText(message.content_plain.encode('utf-8'), 'plain')
        part2 = MIMEText(message.content.encode('utf-8'), 'html')
        msg.attach(part1)
        msg.attach(part2)
        s = smtplib.SMTP(SMPT_SERVER)
        s.sendmail(SENDER_MAIL, recipients, msg.as_string())
        s.close()
        