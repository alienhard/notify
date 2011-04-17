"""Agilezen message with additional information obtained through the API.
Creates plain text and HTML representations of a message.

Note, regexes make assumptions about the text structure of AgileZen messages!
Future changes have to be reflected here (at least until AgileZen supports
WebHooks...).

This code further assumes, that active members of a project have a role
named 'Members' (this is the default).
"""

import time
import re
import StringIO
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
    """Agilezen message with additional information obtained through the API.
    Creates plain text and HTML representations of a message.
    """

    @staticmethod
    def is_agilezen_xmpp_message(xmpp_msg):
        """Check whether xmpp message is of interesest.""" 
        chat_message = xmpp_msg['type'] == 'chat'
        from_agilezen = 'jabber.agilezen.com' == xmpp_msg['from'].server
        return chat_message and from_agilezen
        
    def __init__(self, xmpp_msg):
        self.title = re.sub('([\n\r]+)', '. ', xmpp_msg['body'])
        self.pubdate = datetime.utcnow()
        self.project_id = None
        self.story_id = None
        self.categories = []
        self.status = None
        self.creator = None
        self.creator_mail = None
        self.content = None
        self.content_plain = None

        source = tostring(xmpp_msg['html']['body'])
        self._load_project_and_story(source)
        self.link = 'https://agilezen.com' \
            + '/project/' + str(self.project_id) \
            + '/story/' + str(self.story_id)
        self.guid = self.link + '#' + xmpp_msg['id']
        match = re.search(CAUSER_RE, source)
        if match:
            self.causer = match.group(1)
        self._load_additional_data()


    def _load_project_and_story(self, source):
        """Try to extract and set the project and story IDs.
        
        AgileZen messages for comments do not have URLs...  :(
        In this case, resort to parsing project name and looking up its ID
        via the API.
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
          
    def _load_additional_data(self):
        """Create html and text representations and load status,
        creator, and creator_mail from the API."""
        story = api.get_story(self.project_id, self.story_id)
        self.content = self._create_html_content_from(story)
        self.content_plain = self._create_plain_content_from(story)
        try:
            self.status = story['status']
            self.creator = story['creator']['name']
            self.creator_mail = story['creator']['email']
        except KeyError:
            raise MessageCreationException(
                'Failed to read status or creator from API.')

    def _create_html_content_from(self, story):
        """Return an html representation of this story."""
        html = StringIO.StringIO()    
        html.write('<html><body>')
        html.write('<a href="' + self.link + '">Story details</a><br />')
        html.write('<b>' + markdown(story['text']) + '</b>')
        if story['details']:
            html.write(markdown(story['details']))
        html.write('<hr />')
        html.write('Phase: ' + story['phase']['name'] + '<br />')
        html.write('Status: ' + story['status'] + '<br />')
        if 'blockedReason' in story.keys():
            html.write('<span style="color:red">Block reason: '
                + story['blockedReason'] + '</span><br />')
        html.write('Creator: ' + story['creator']['name'] + '<br />')
        if 'owner' in story.keys():
            html.write('Owner: ' + story['owner']['name'] + '<br />')
        if 'deadline' in story.keys():
            html.write('Deadline: '
                + re.sub('T00:00:00', '', story['deadline']) + '<br />')
        if story['comments']:
            html.write('<hr /><br />')
        for comment in story['comments']:
            html.write(' <i>' + comment['author']['name'] + '</i> said (')
            html.write(_convert_gmt(comment['createTime']) + '):')
            comment = re.sub('(\n)', '<br />', comment['text'])
            html.write('<p>' + markdown(comment) + '</p>')
            html.write("<br />")        
        html.write('</body></html>')
        content = html.getvalue()
        html.close()
        return content
    
    def _create_plain_content_from(self, story):
        """Return a plain text representation of this story."""
        text = StringIO.StringIO()
        text.write(self.link + '\n\n')
        text.write(story['text'] + '\n\n')
        if story['details']:
            text.write(story['details'] + '\n\n')
        text.write('---------------------------\n\n')
        text.write('Phase: ' + story['phase']['name'] + '\n')
        text.write('Status: ' + story['status'] + '\n')
        if 'blockedReason' in story.keys():
            text.write('* Block reason: '
                + story['blockedReason'] + '\n')
        text.write('Creator: ' + story['creator']['name'] + '\n')
        if 'owner' in story.keys():
            text.write('Owner: ' + story['owner']['name'] + '\n')
        if 'deadline' in story.keys():
            text.write('Deadline: '
                + re.sub('T00:00:00', '', story['deadline']) + '\n')  
        if story['comments']:
            text.write('\n---------------------------\n\n')
        for comment in story['comments']:
            text.write(comment['author']['name'] + ' said (')
            text.write(_convert_gmt(comment['createTime']) + '):\n')
            text.write(comment['text'])
            text.write("\n\n")
        content = text.getvalue()
        text.close()
        return content
        
    def is_new(self):
        """Returns true if the message was triggered when creating a story.
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
        return "<AZMessage '" + self.title + "' [" + self.guid + "]>"


class MessageCreationException(Exception):
    """Exception raised when message instance cannot be created."""
    pass


def _convert_gmt(string):
    """Convert the argument, a timestamp in GMT, to a timestamp
    string in the local time zone. Format as %d.%m.%Y %H:%M."""
    try:
        utc = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return 'n/a'
    local = time.localtime(time.mktime(utc.timetuple()) - time.altzone)
    return time.strftime("%d.%m.%Y %H:%M", local)

        