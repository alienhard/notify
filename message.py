"""Agilezen message with additional information obtained through the API.
Creates plain text and HTML representations of a message.

Note, regexes make assumptions about the text structure of AgileZen messages!
Future changes have to be reflected here (at least until AgileZen supports
WebHooks...).

This code further assumes, that active members of a project have a role
named 'Members' (this is the default).
"""

import sys
import time
import re
import httplib
import json
import StringIO
import ConfigParser
from datetime import datetime

from sleekxmpp.xmlstream.tostring import tostring
from markdown2 import markdown

import api

# Regexes 
PROJECT_STORY_RE = 'https://agilezen.com/project/(\d*)/story/(\d*)'
ALT_PROJECT_STORY_RE = '\[(\w*)\].*\(\#(\d*)\)'
NEW_STORY_RE = '\) was created by '
MARKED_BLOCKED_RE = '\) was blocked by '
MARKED_DEPLOYED_RE = '\) was moved from .*? to Deployed'
MOVED_TO_READY_RE = 'was moved from .*? to Ready'
CAUSER_RE = '\sby\s([A-Z]\w+\s[A-Z]\w+)'


class AZMessage():
    
    @staticmethod
    def is_agilezen_xmpp_message(xmpp_msg):
        """Check whether xmpp message is of interesest.""" 
        chat_message = xmpp_msg['type'] == 'chat'
        from_agilezen = 'jabber.agilezen.com' == xmpp_msg['from'].server
        return chat_message and from_agilezen
        
    def __init__(self, xmpp_msg):
        body_element = xmpp_msg['html']['body']
        source = tostring(body_element)
        
        self._initialize_urls_from(source)
        self._fetch_additional_data()
        
        match = re.search(CAUSER_RE, source)
        if match:
            self.causer = match.group(1)
        
        self.title = re.sub('([\n\r]+)', '. ', xmpp_msg['body'])
        self.pubdate = datetime.utcnow()
        self.id = xmpp_msg['id']
        self.categories = []
     
    def _initialize_urls_from(self, source):
        """Try to extract and set the project and story IDs.
        
        AgileZen comment messages do not have URLs...  :(
        In this case, resort to parsing project name and looking up its ID
        via the API.
        
        Also note that, AgileZen's URLs for web and API access are inconsistent.
        """
        match = re.search(PROJECT_STORY_RE, source)
        if match:
            self.project_id = int(match.group(1))
            self.story_id = int(match.group(2))
        else:
            match = re.search(ALT_PROJECT_STORY_RE, source, flags=re.DOTALL)
            if match:
                self.project_id = api.lookup_project_id(match.group(1))
                self.story_id = int(match.group(2))
            else:
                raise MessageCreationException(
                    'Could not parse project/story number from: ' + source)
        self.link = 'https://agilezen.com' \
            + '/project/' + str(self.project_id) \
            + '/story/' + str(self.story_id)
          
    def _fetch_additional_data(self):
        dict = api.get_story(self.project_id, self.story_id)
        self.content = self._create_html_content_from(dict)
        self.content_plain = self._create_plain_content_from(dict)
        try:
            self.status = dict['status']
            self.creator = dict['creator']['name']
            self.creator_mail = dict['creator']['email']
        except KeyError:
            raise MessageCreationException(
                'Failed to read status or creator from API.')

    def _create_html_content_from(self, dict):
        html = StringIO.StringIO()    
        html.write('<html><body>')
        html.write('<a href="' + self.link + '">Story details</a><br />')
        html.write('<b>' + markdown(dict['text']) + '</b>')
        if dict['details']:
            html.write(markdown(dict['details']))
        html.write('<hr />')
        html.write('Phase: ' + dict['phase']['name'] + '<br />')
        html.write('Status: ' + dict['status'] + '<br />')
        if 'blockedReason' in dict.keys():
            html.write('<span style="color:red">Block reason: '
                + dict['blockedReason'] + '</span><br />')
        html.write('Creator: ' + dict['creator']['name'] + '<br />')
        if 'owner' in dict.keys():
            html.write('Owner: ' + dict['owner']['name'] + '<br />')
        if 'deadline' in dict.keys():
            html.write('Deadline: '
                + re.sub('T00:00:00', '', dict['deadline']) + '<br />')
        if dict['comments']:
            html.write('<hr /><br />')
        for comment in dict['comments']:
            html.write(' <i>' + comment['author']['name'] + '</i> said (')
            html.write(self._convert_gmt(comment['createTime']) + '):')
            comment = re.sub('(\n)', '<br />', comment['text'])
            html.write('<p>' + markdown(comment) + '</p>')
            html.write("<br />")        
        html.write('</body></html>')
        content = html.getvalue()
        html.close()
        return content
    
    def _create_plain_content_from(self, dict):
        text = StringIO.StringIO()
        text.write(self.link + '\n\n')
        text.write(dict['text'] + '\n\n')
        if dict['details']:
            text.write(dict['details'] + '\n\n')
        text.write('---------------------------\n\n')
        text.write('Phase: ' + dict['phase']['name'] + '\n')
        text.write('Status: ' + dict['status'] + '\n')
        if ('blockedReason' in dict.keys()):
            text.write('* Block reason: '
                + dict['blockedReason'] + '\n')
        text.write('Creator: ' + dict['creator']['name'] + '\n')
        if 'owner' in dict.keys():
            text.write('Owner: ' + dict['owner']['name'] + '\n')
        if 'deadline' in dict.keys():
            text.write('Deadline: '
                + re.sub('T00:00:00', '', dict['deadline']) + '\n')  
        if dict['comments']:
            text.write('\n---------------------------\n\n')
        for comment in dict['comments']:
            text.write(comment['author']['name'] + ' said (')
            text.write(self._convert_gmt(comment['createTime']) + '):\n')
            text.write(comment['text'])
            text.write("\n\n")
        content = text.getvalue()
        text.close()
        return content
        
    def _convert_gmt(self, string):
        try:
            utc = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return 'n/a'
        local = time.localtime(time.mktime(utc.timetuple()) - time.altzone)
        return time.strftime("%d.%m.%Y %H:%M", local)
            
    def is_new(self):
        """Returns true if the message was triggered when creating a new story.
        """
        return re.search(NEW_STORY_RE, self.title) is not None
    
    def is_moved_to_ready(self):
        """Returns true if the current story is moved into the ready queue."""
        moved_ready = re.search(MOVED_TO_READY_RE, self.title) is not None
        new_and_started = self.is_new() and self.status == 'started'
        return moved_ready or new_and_started
        
    def is_marked_blocked(self):
        """Returns true if the message was triggered when blocking the story.
        """    
        return re.search(MARKED_BLOCKED_RE, self.title) is not None
    
    def is_marked_deployed(self):
        """Returns true if the message was triggered when moving story
        to deployed.
        """
        return re.search(MARKED_DEPLOYED_RE, self.title) is not None

    def __str__(self):
        return "<AZMessage '" + self.title + "' [" + self.id + "]>"


class MessageCreationException(Exception):
    pass
        