# -*- coding: utf-8 -*-

import unittest
from mock import Mock
import json

import sleekxmpp

from .. import message


class TestMessage(unittest.TestCase):
    """Test creation of AZMessage instances. Uses mocks for API."""

    def setUp(self):
        self.xmpp_msg = _xmpp_msg_1()
        self.story_1 = json.loads(STORY_1_JSON)
        message.api.get_story = Mock(return_value=self.story_1)
        
    def test_data_from_xmpp_message(self):
        msg = message.AZMessage(self.xmpp_msg)
        message.api.get_story.assert_called_with(12345, 1)
        
        self.assertEqual(msg.project_id, 12345)
        self.assertEqual(msg.story_id, 1)
        self.assertEqual(msg.causer, 'John Doe')
        
        # note, new lines are replaced by a dot and space  
        self.assertEqual(msg.title,
            '[TestProject] "New **Story**. Code: '\
            +'`<i>003</i>`" (#1) was created by John Doe')
        
        self.assertTrue(msg.pubdate is not None)
        self.assertEqual(msg.id, 'ID_1')
        self.assertEqual(msg.link,
            'https://agilezen.com/project/12345/story/1')
    
    def test_data_from_api(self):
        msg = message.AZMessage(self.xmpp_msg)
        message.api.get_story.assert_called_with(12345, 1)
        self.assertEqual(msg.status, 'started')
        self.assertEqual(msg.creator, 'Gob Bluth')
        self.assertEqual(msg.creator_mail, 'Gob@bluth.com')
        self.assertTrue(msg.content is not None)
        self.assertTrue(msg.content_plain is not None)


def _xmpp_msg_1():
    msg = sleekxmpp.Message()
    msg['id'] = 'ID_1'
    msg['body'] = '[TestProject] "New **Story**\n\nCode: `<i>003</i>`" (#1) was created by John Doe'
    msg['subject'] = 'Test Subject umlaut Ä'
    msg['type'] = 'chat'
    msg['from'] = 'notifications@jabber.agilezen.com/Jabber.Net'
    msg['html'].set_body('<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml">[<a href="https://agilezen.com/project/12345">TestProject</a>] <em>&quot;New Story with umlaut Ä&quot;</em> (<a href="https://agilezen.com/project/12345/story/1">#1</a>) was moved from <strong>Done</strong> to <strong>Tested</strong> by John Doe</body></html>')
    return msg


def _xmpp_msg_2():
    msg = sleekxmpp.Message()
    msg['id'] = 'ID_2'
    msg['body'] = '"Add Feature X" (#20) was moved from Backlog to Ready by Foo Bar'
    msg['subject'] = 'Test Subject comment'
    msg['type'] = 'chat'
    msg['from'] = 'notifications@jabber.agilezen.com/Jabber.Net'
    msg['html'].set_body('<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml">Comment by John Doe on [Sandbox] "Bug X" (#12): Comment Y</body></html>')
    return msg
    

# Example JSON data from http://dev.agilezen.com/resources/stories.html 
STORY_1_JSON = '{\
  "id": 1,\
  "text": "Build Spec house",\
  "details": "Only have 2 weeks to build a spec house.",\
  "size": "5",\
  "color": "teal",\
  "priority": "9",\
  "deadline": "2011-02-24T00:00:00",\
  "status": "started",\
  "project": {\
    "id": 12345,\
    "name": "Sudden Valley"\
  },\
  "phase": {\
    "id": 3,\
    "name": "Working"\
  },\
  "creator": {\
    "id": 1,\
    "name": "Gob Bluth",\
    "userName": "gob",\
    "email": "Gob@bluth.com"\
  },\
  "owner": {\
    "id": 1,\
    "name": "Gob Bluth",\
    "userName": "gob",\
    "email": "Gob@bluth.com"\
  },\
  "comments": [\
    {\
      "id": 1,\
      "text": "No way we can build it in 2 weeks.",\
      "createTime": "2011-02-17T20:01:01",\
      "author": {\
        "id": 1,\
        "name": "Gob Bluth",\
        "userName": "gob",\
        "email": "Gob@bluth.com"\
      }\
    }\
  ]\
}'