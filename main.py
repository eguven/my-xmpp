#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.api import xmpp, urlfetch # probably should have used urllib instead
from django.utils import simplejson as json
from models import User, Url
import logging
import urllib

_DEBUG = True
LOGIN = 'FILL-IN' # bitly username
API_KEY = 'FILL-IN' # bitly user api key
JMP_URL = 'http://api.bitly.com/v3/shorten?login=%s&apiKey=%s&domain=j.mp&format=json&longUrl=' % (LOGIN, API_KEY) # shorten request

class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('main.html',{})) # static html really

class SubscribeHandler(webapp.RequestHandler):
  '''Get user JID, add to datastore if it doesn't exist'''
  def post(self):
    j = self.request.get('from').split('/')[0]
    if not User.gql('WHERE jid = :1', j).get():
      User(jid=j).put()

class ChatHandler(webapp.RequestHandler):
  '''Responsd to chat message with a shortened URL'''
  def post(self):
    j = self.request.get('from').split('/')[0]
    u = User.gql('WHERE jid = :1', j).get()
    if not u:
      u = User(jid=j)
      u.put()
    message = xmpp.Message(self.request.POST)
    
    r = query_bitly(message.body.strip().split(' ')[0], u)
    message.reply('\n'+r) # replied
    return

class UpHandler(webapp.RequestHandler):
    def get(self):
        return 42

def query_bitly(longUrl, user):
  l = urllib.quote(longUrl,'')
  if (longUrl[:7].lower() != 'http://' and urllib.unquote(longUrl)[:7].lower() != 'http://' and
      longUrl[:8].lower() != 'https://' and urllib.unquote(longUrl)[:8].lower() != 'https://'):
    l = urllib.quote('http://'+longUrl,'')

  result = urlfetch.fetch(JMP_URL+l)
  logging.debug('posted to bit.ly: %s' % l)
  if result.status_code != 200:
    return 'Sorry! Query failed.'
  j = json.JSONDecoder()
  data = j.decode(result.content)
  if data.get('status_code') == 403:
    logging.warning('RATE LIMIT EXCEEDED')
    return 'Sorry! Experiencing rate limits from bit.ly'
  if data.get('status_code') != 200:
    logging.error(result.content)
    return 'Sorry! bit.ly did not accept the query. Make sure that your message only contains a URL.'    
  url = Url(longUrl=data.get('data').get('long_url'), shortUrl=data.get('data').get('url'), creator=user)
  url.put()
  return data.get('data').get('url')

def main():
    application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', ChatHandler),
                                          ('/_ah/xmpp/subscription/subscribe/', SubscribeHandler),
                                          ('/up', UpHandler),
                                          ('/', MainHandler)],
                                         debug=_DEBUG)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
