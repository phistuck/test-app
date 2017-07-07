from google.appengine.ext import db, webapp
from google.appengine.api import mail, xmpp, urlfetch
from datetime import datetime, timedelta

import os
import urllib
import re

from constants \
 import AUTHOR_EMAIL, NO_REPLY_EMAIL, IS_PRODUCTION, \
 LEGACY_MESSENGER_URL, MESSENGER_DEFAULTS

class InstantMessagingDatabase(db.Model):
 sender = db.StringProperty(multiline=False)
 recipient = db.StringProperty(multiline=False)
 message = db.TextProperty()
 message_date = db.DateTimeProperty()
   
class InstantMessagingManagerDatabase(db.Model):
 uid = db.StringProperty(multiline=False)
 real = db.DateTimeProperty()

nicknames_by_email = {}
emails_by_nickname = {}
default_recipient_by_email = {}

def fill_name_objects(email, name, default_recipient_nickname):
 nicknames_by_email[email] = name
 default_recipient_by_email[email] = default_recipient_nickname
 emails_by_nickname[name] = email
 
def get_nickname(email):
 if email in nicknames_by_email:
  return nicknames_by_email[email]
 return email

def get_email(name):
 if name in emails_by_nickname:
  return emails_by_nickname[name]
 return name

def get_default_recipient(email):
 if email in default_recipient_by_email:
  return default_recipient_by_email[email]
 return email

real_replies = {}
message_bank = {}

for x in MESSENGER_DEFAULTS:
 fill_name_objects(x[0], x[1], x[2])


def update_real_user_state(email, real_minutes):
  user_row = InstantMessagingManagerDatabase.gql("WHERE uid = :uid", uid=email).fetch(1000)
  if len(user_row) == 1:
   User = db.get(user_row[0].key())
   User.real = datetime.today() + timedelta(minutes=real_minutes)
   db.put(User)
  else:
   add_user(email, real_minutes)
     
def add_user(email, real_minutes):
  User = InstantMessagingManagerDatabase(uid=email, real = datetime.today() + timedelta(minutes=real_minutes))
  User.put()

def can_converse(email):
 user_row = InstantMessagingManagerDatabase.gql("WHERE uid = :uid", uid=email).fetch(1000)
 if len(user_row) == 1:
  return (user_row[0].uid == email and user_row[0].real > datetime.today())
 else:
  add_user(email, -1)
 return False

def hour_delta():
 if datetime.today() < datetime(day=1,month=4,year=2011,hour=0,minute=0,second=0) or \
    (datetime.today() > datetime(day=1,month=10,year=2011,hour=23,minute=0,second=0) and \
     datetime.today() < datetime(day=30,month=3,year=2012,hour=0,minute=0,second=0)) or \
    (datetime.today() > datetime(day=22,month=9,year=2012,hour=23,minute=0,second=0) and \
     datetime.today() < datetime(day=29,month=3,year=2013,hour=0,minute=0,second=0)) or \
    (datetime.today() > datetime(day=7,month=9,year=2013,hour=23,minute=0,second=0) and \
     datetime.today() < datetime(day=28,month=3,year=2014,hour=0,minute=0,second=0)) or \
    (datetime.today() > datetime(day=27,month=9,year=2014,hour=23,minute=0,second=0) and \
     datetime.today() < datetime(day=27,month=3,year=2015,hour=0,minute=0,second=0)):
  return 2
 else:
  return 3

def get_messages(nickname):
 current_day = (datetime.today() + timedelta(hours=hour_delta())).date()
 messages = ""
 message_list = InstantMessagingDatabase.gql("WHERE recipient = :recipient ORDER BY message_date", recipient=nickname).fetch(1000)
 for message in message_list:
  additional = ""
  if message.message_date.date() != current_day:
   additional = "%Y-%m-%d "
  messages += "\n" + message.sender + " (" + (message.message_date + timedelta(hours=hour_delta())).strftime(additional + "%H:%M:%S") + ") - " + message.message
 if (messages != ""):
  messages = "\nRecently received messages - \n" + messages
  db.delete(message_list)
 return messages

def add_message(recipient, sender, message_text):
 message = InstantMessagingDatabase(sender=sender, recipient=recipient, message=message_text, message_date=datetime.today())
 message.put()
 
class SendPresenceNotification(webapp.RequestHandler):
 def post(self):
  sender = self.request.get("sender")
  recipient = self.request.get("recipient")
  message = self.request.get("message")
  notify = self.request.get("notify") == "1"
  xmpp.send_invite(recipient)
  if can_converse(recipient) and len(message) > 0:
   xmpp.send_message(recipient, message)
  else:
   if notify:
    xmpp.send_message(recipient, "This is an automated message. Do not reply.")
   if len(message) > 0:
    add_message(get_nickname(recipient), get_nickname(sender), message)
  if notify:
   mail.send_mail(NO_REPLY_EMAIL,
                  recipient,
                  "Automated Message - Do Not Reply",
                  "This is an automated message. Do not reply.")
  if not IS_PRODUCTION:
   self.response.out.write(unicode(message + get_messages(get_nickname(recipient))))
   
class MessageReceiver(webapp.RequestHandler):
 def post(self):
  message = xmpp.Message(self.request.POST);
  sender = re.sub("/.*$", "", message.sender)
  message_reply = ""
  indeed_send = True
  message_from = get_nickname(sender)
  message_to = get_default_recipient(sender)
  start_conversing = False
  if ("@" in message_from):
   indeed_send = False
  if (message.body.startswith("SAW") or message.body.startswith("PAW") or message.body.startswith("--stop")):
   update_real_user_state(sender, -1)
   indeed_send = False
  if message.body.startswith("--real"):
   start_conversing = True
   real_for_minutes = re.sub("\D", "", message.body)
   indeed_send = False
   if len(real_for_minutes) == 0:
    real_for_minutes = 5
   update_real_user_state(get_email(message_from), int(real_for_minutes))
  if indeed_send:
   payload_string = "xmpp=1&from=" + message_from + "&to=" + message_to + "&message=" + urllib.quote(message.body.encode("utf-8"))
   if IS_PRODUCTION:
    urlfetch.fetch(LEGACY_MESSENGER_URL,
                   payload=payload_string,
                   method=urlfetch.POST,
                   headers={"Content-Type": "application/x-www-form-urlencoded"},
                   allow_truncated=False,
                   follow_redirects=False,
                   deadline=None)
  if start_conversing:
   message_reply = "Starting the real conversation mode." + get_messages(get_nickname(sender))
  else:
   if can_converse(get_email(message_from)):
    if indeed_send:
     message_reply = "_Sent._"
    else:
     message_reply = "Understood."
   else:
    message_reply = "\n\n\n\n\n\n\n\n\n\n\n\n\n\nPlease, do not reply."
  if not message_reply == "":
   message.reply(message_reply)
  if not IS_PRODUCTION:
   self.response.out.write(unicode(message_reply));