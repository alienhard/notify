# AgileZen Notify

AgileZen Notify is a daemon that creates custom RSS feeds and sends mails for the AgileZen project management service.

AgileZen is a great tool, but currently it lacks decent notification capabilities (when enabled, you get a mail *for each* single change...).

AgileZen Notify allows your team to define who should get notified of what – either through mail or RSS feeds. Notify is implemented in Python. It listens to the XMPP stream of AgileZen and reads data from their API. It is flexible to be customized and extended.

*AgileZen  is copyright Rally Software Development Corp.*


## Features

Currently implemented are the following outputs:

- Mail (both plain and rich text)
- RSS feeds (atom format)

Through custom rules you can define wich feeds should be created and when to send mails to whom.

Rule examples:

- When new story is created, send a mail to all active members except for the creator
- When a story is marked as being blocked, send a mail to the creator and all active members
- When a story is completed, send a mail to the creator
- For each project create an RSS feed

Mails and RSS feed items not only show the change message (e.g., "Story X was moved from Ready to Working") but they include the **full story details**, including the discussion. The formatting supports markdown. 

The app is implemented to be easily extensible:

- create new rules
- define sets of recipients
- create new handlers

## Installation

Requires Python >= 2.6

1. Clone this project
2. Download and install (SleekXMPP)[https://github.com/fritzy/SleekXMPP]
3. Download and install (Feedgenerator)[http://pypi.python.org/pypi/feedgenerator]
4. Optional: set up a web server to serve the RSS feeds. They are written to the `feeds/` directory.

## Setup

1. Create a [gmail account](https://www.google.com/accounts/NewAccount?service=mail&continue=http://mail.google.com/mail/e-11-1bf426d4034c1f2ca91664311f9516-fa195ed49584db707d3dc9ff47138d8200773a09&type=2) for the Notify bot. It has to be an actual @gmail account, Google Apps for your domain accounts won’t work unless you do [this](http://www.google.com/support/a/bin/answer.py?hl=en&answer=60227).
2. In AgileZen, under settings, go to the Notifications tab. Enable a “Google Talk / XMPP” Channel Type and set the username to yournewaccount@gmail.com. Check “Send me notifications for actions I perform”.
3. Login to your new gmail account and add notifications@jabber.agilezen.com as a contact on google talk
4. Create an AgileZen API key (go to the Developer tab at https://agilezen.com/settings)
4. Configure AgileZen notify.cfg (you need the google account login and the API key you created in the steps above)
5. Start Notify by executing `./run`


## Customization

Check out the creation and of the handler instances and rules in `notifier.py` and adapt them to your needs.


## License 

(The MIT License)

Copyright (c) 2011 Adrian Lienhard adrian@cmsbox.com;

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.