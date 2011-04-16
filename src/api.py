"""Some utility functions to access the AgileZen API (v1)."""

import sys
import time
import re
import httplib
import json
import StringIO
import ConfigParser

# AgileZen-related constants, read API key from cfg.
config = ConfigParser.RawConfigParser()
config.read('notify.cfg')
API_KEY = config.get('api', 'key')
API_DOMAIN = 'agilezen.com'
API_PATH_PREFIX = '/api/v1'
API_HEADERS = {
    "X-Zen-ApiKey": API_KEY,
    "Content-Type": "application/json" }
PROJECTS_URL = 'https://agilezen.com/api/v1/projects'


def get_projects():
    """Return a list of all projects."""
    conn = httplib.HTTPSConnection(API_DOMAIN)
    conn.request("GET", PROJECTS_URL, headers=API_HEADERS)
    response = conn.getresponse().read()
    return _parseRresponse(response)

def get_people(project_id, role = None):
    """Return a list of members (dicts) that have the given role in the project.
    If role is None, return all members."""
    path = API_PATH_PREFIX + '/projects/' + str(project_id) + '?with=roles'
    conn = httplib.HTTPSConnection(API_DOMAIN)
    conn.request("GET", path, headers=API_HEADERS)
    response = conn.getresponse().read()
    dict = _parseRresponse(response)
    if role is not None:
        role_dict = _detect(lambda r: r['name'] == role, dict['roles'])
        if (role_dict):
            return role_dict['members']
        else:
            raise APIException('Failed to read members <' + role + '> from API.')
    else:
        result = []
        print dict
        for each in dict['roles']:
            result += each['members']
        return result

def get_story(project_id, story_id):
    """Return the details and comments of a story."""
    path = API_PATH_PREFIX
    path +='/projects/' + str(project_id) + '/stories/' + str(story_id)
    path += '?with=details,comments'
    conn = httplib.HTTPSConnection(API_DOMAIN)
    conn.request("GET", path, headers=API_HEADERS)
    response = conn.getresponse().read()
    return _parseRresponse(response)

def get_active_project_ids():
    """Return a the IDs of all non-archived projects.""" 
    dict = get_projects()
    return map(lambda project: int(project['id']), dict['items'])
    
def lookup_project_id(name):
    """Return the project's ID with the given name.
    If not found raise exception.
    """
    dict = get_projects()
    for project in dict['items']:
        if (project['name'] == name):
            return int(project['id'])
    raise APIException('Unknown project name ' + name)     

def _parseRresponse(response):
    if not response:
        raise APIException('Failed to read data from API.')
    try:
        dict = json.loads(response)
    except:
        raise APIException('Failed to parse data from API.')
    return dict

def _detect(f, seq):
    for item in seq:
        if f(item):
            return item
    return None

class APIException(Exception):
    pass