"""A handler that writes messages to an RSS feed on disk.

It caches a certain number of recent messages to persist them over restarts.
"""

import os
import pickle
from ConfigParser import RawConfigParser

from feedgenerator import Atom1Feed

# read config
CFG_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'notify.cfg')
CONFIG = RawConfigParser()
CONFIG.read(CFG_PATH)
FEED_BASE_URL = CONFIG.get('feed', 'base_url')
FEED_DESCRIPTION = CONFIG.get('feed', 'description')
AUTHOR_NAME = CONFIG.get('feed', 'author_name')
AUTHOR_EMAIL = CONFIG.get('feed', 'author_email')
MESSAGE_CACHE_SIZE = CONFIG.getint('feed', 'message_cache_size')

FEED_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'feeds')


class FeedHandler():
    
    def __init__(self, title, filename, interested_in):
        self.title = title
        self.filename = filename
        self.interested_in = interested_in
        self._load_messages()
        self._generate_feed()
        
    def handle(self, message):
        if self.interested_in(message):
            self._remember(message)
            self._generate_feed()
        
    def _generate_feed(self):
        generator = self._create_generator()
        for each in self.messages:
            try:
                author_name = each.causer
            except AttributeError:
                author_name = AUTHOR_NAME
            generator.add(
                title = each.title,
                link = each.link,
                description = each.content,
                pubdate = each.pubdate,
                unique_id = each.guid,
                categories = each.categories,
                author_name = author_name,
                author_email = AUTHOR_EMAIL)
        path = os.path.abspath(
            os.path.join(FEED_PATH, self.filename + '.xml'))
        file = open(path, 'w')
        generator.write_string_to_file(file)
        file.close()

    def _create_generator(self):
        return FeedGenerator(
            self.title, FEED_BASE_URL + self.filename, FEED_DESCRIPTION)

    # cache MESSAGE_CACHE_SIZE number of messages
    def _remember(self, message):
        self.messages.insert(0, message)
        self.messages = self.messages[:MESSAGE_CACHE_SIZE]
        self._save_messages()
    
    # persist the messsages as a pickle file
    def _save_messages(self):
        if len(self.messages) > 0:
            file = open(self._backup_pickle_path(), 'wb')
            pickle.dump(self.messages, file)
            file.close()
            
    # try to load messages from file system
    # note, it's possible that these files don't exist 
    def _load_messages(self):
        try:
            file = open(self._backup_pickle_path(), 'rb')
            self.messages = pickle.load(file)
            file.close()
        except IOError as e:
            self.messages = []

    def _backup_pickle_path(self):
        return os.path.abspath(os.path.join(
            FEED_PATH, self.filename + '.pkl'))


class FeedGenerator():
    """A class that wraps the feedgenerator (creates an Atom feed)."""
    
    def __init__(self, title, link, description):
        self.feed = Atom1Feed(
            title = title,
            link = link,
            description = description,
            language=u"en",
        )

    def add(self, **event):
        """Add an item to the feed."""
        self.feed.add_item(**event)

    def write_string_to_file(self, file):
        """Export the feed to a file."""
        file.write(self.feed.writeString('utf-8'))