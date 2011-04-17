# -*- coding: utf-8 -*-

import unittest
from mock import Mock
import json

import sleekxmpp

import message


class TestMessage(unittest.TestCase):
    """Test AZMessage. Uses mocks for API."""

    def setUp(self):
        self.xmpp_msg_1 = _xmpp_msg_1()
        self.story_1 = json.loads(STORY_1_JSON)
        message.api.get_story = Mock(return_value=self.story_1)
        message.api.lookup_project_id = Mock(return_value=99999)
        
        self.xmpp_msg_2 = _xmpp_msg_2()
        self.story_2 = json.loads(STORY_2_JSON)
        message.api.get_story = Mock(return_value=self.story_2)
        message.api.lookup_project_id = Mock(return_value=99999)

    def test_is_agilezen_xmpp_message(self):
        self.assertTrue(
            message.AZMessage.is_agilezen_xmpp_message(self.xmpp_msg_1))
        self.assertTrue(
            message.AZMessage.is_agilezen_xmpp_message(self.xmpp_msg_2))
        self.xmpp_msg_2['from'] = 'foo@gmail.com/CEFF15A8'
        self.assertFalse(
            message.AZMessage.is_agilezen_xmpp_message(self.xmpp_msg_2))
        
    def test_msg_1_data_from_xmpp_message(self):
        msg = message.AZMessage(self.xmpp_msg_1)
        message.api.get_story.assert_called_with(12345, 1)
        
        self.assertEqual(msg.project_id, 12345)
        self.assertEqual(msg.story_id, 1)
        
        # note, new lines are replaced by a dot and space  
        self.assertEqual(msg.title,
            '[TestProject] "New **Story**. Code: '\
            +'`<i>003</i>`" (#1) was created by John Doe')
            
        self.assertTrue(msg.pubdate is not None)
        self.assertEqual(msg.guid,
            'https://agilezen.com/project/12345/story/1#ID_1')
        self.assertEqual(msg.link,
            'https://agilezen.com/project/12345/story/1')
        self.assertEqual(msg.causer, 'John Doe')
    
    def test_msg_1_data_from_api(self):
        msg = message.AZMessage(self.xmpp_msg_1)
        message.api.get_story.assert_called_once_with(12345, 1)
        self.assertFalse(message.api.lookup_project_id.called)
        self.assertEqual(msg.status, 'started')
        self.assertEqual(msg.creator, 'Gob Bluth')
        self.assertEqual(msg.creator_mail, 'Gob@bluth.com')
        self.assertTrue(msg.content is not None)
        self.assertTrue(msg.content_plain is not None)

    def test_msg_2_lookup_project(self):
        msg = message.AZMessage(self.xmpp_msg_2)
        message.api.lookup_project_id.assert_called_once_with('ProjectFoo')
        message.api.get_story.assert_called_once_with(99999, 2)
        self.assertEqual(msg.project_id, 99999)
        self.assertEqual(msg.story_id, 2)
        self.assertTrue(msg.pubdate is not None)
        self.assertEqual(msg.guid,
            'https://agilezen.com/project/99999/story/2#ID_2')
        self.assertEqual(msg.link,
            'https://agilezen.com/project/99999/story/2')
        self.assertEqual(msg.causer, 'Bob Doe')
        
    def test_new_and_ready_to_work(self):
        msg = message.AZMessage(self.xmpp_msg_1)
        self.assertTrue(msg.is_new())
        self.assertTrue(msg.is_moved_to_ready())
        self.assertFalse(msg.is_marked_blocked())
        self.assertFalse(msg.is_marked_deployed())

    def test_ready_to_work_from_backlog(self):
        msg = message.AZMessage(self.xmpp_msg_2)
        self.assertFalse(msg.is_new())
        self.assertTrue(msg.is_moved_to_ready())
        self.assertFalse(msg.is_marked_blocked())
        self.assertFalse(msg.is_marked_deployed())

    def test_invalid_msg_data(self):
        xmpp_msg = sleekxmpp.Message()
        xmpp_msg['html'].set_body('<html><body><p>empty</p></body></html>')
        self.assertRaises(message.MessageCreationException,
            message.AZMessage, xmpp_msg)
        
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
    """This message is special in that it doesn't include an URL from
    which the project ID can be parsed. In this case, the ID is looked
    up through the API.
    """
    msg = sleekxmpp.Message()
    msg['id'] = 'ID_2'
    msg['body'] = '"Add Feature X" (#2) was moved from Backlog to Ready by Foo Bar'
    msg['subject'] = 'Test Subject comment'
    msg['type'] = 'chat'
    msg['from'] = 'notifications@jabber.agilezen.com/Jabber.Net'
    msg['html'].set_body('<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml">Comment by Bob Doe on [ProjectFoo] "Bug X" (#2): Comment Y</body></html>')
    return msg
    

# JSON from dev.agilezen.com/resources/stories.html (slightly adapted)
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

STORY_2_JSON = '{\
  "id": 2,\
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