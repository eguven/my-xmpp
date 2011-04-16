#!/usr/bin/env python

from google.appengine.ext import db

class User(db.Model):
  jid = db.StringProperty()
  joined = db.DateTimeProperty(auto_now_add=True)

class Url(db.Model):
  longUrl = db.StringProperty()
  shortUrl = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  creator = db.ReferenceProperty(User)
