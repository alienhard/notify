""" Rules used by notifier.py to figure when to activate a handler and whom
to send mails.
"""

import sys
import time
import re
import httplib

import api

def is_new(msg):
    """See comment in message.py"""
    return msg.is_new()

def is_marked_blocked(msg):
    """See comment in message.py"""
    return msg.is_marked_blocked()

def is_marked_deployed(msg):
    """See comment in message.py"""
    return msg.is_marked_deployed()

def is_moved_to_ready(msg):
    """See comment in message.py"""
    return msg.is_moved_to_ready()

def everyone(msg):
    """Return a list of all mail addresses of all involved people.
    """
    dicts = api.get_people(msg.project)
    return set(map(lambda member: member['email'], dicts))

def active_members_with_creator(msg):
    """Return a set of mail addresses of all active members and the
    message's creator.
    """
    return active_members(msg) | creators(msg)

def active_members_without_creator(msg):
    """Return a set of mail addresses of all active members except for the
    creator of the message.
    """
    return active_members(msg) - creators(msg)

def active_members(msg):
    """Return a list of all mail addresses of people having the role Members.
    """
    dicts = api.get_people(msg.project, 'Members')
    return set(map(lambda member: member['email'], dicts))

def creators(msg):
    """Return a set with the creator's mail address."""
    creator = msg.creator_mail
    return set((creator, ))
