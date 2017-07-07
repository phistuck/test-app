from google.appengine.ext import db, webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

import cgi
import wsgiref.handlers
import string

from constants import IS_PRODUCTION, PATH

from flair_extender import FlairList
from messenger import SendPresenceNotification, MessageReceiver
from browser_extensions_manager import CreateBug, BugProcess, \
 DeleteBugOrComment, ViewBug, AddExtension, \
 EditExtensionChangelog, ViewExtensionChangelog, \
 ExtensionDatabasesViewing, BugDatabaseViewing

class GuestbookDatabase(db.Model):
  author = db.UserProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

class UsersDatabase(db.Model):
  author = db.UserProperty()
  gender = db.StringProperty(multiline=True)
  joined = db.DateTimeProperty(auto_now_add=True)
  lastlogin = db.DateTimeProperty()
  calendartoken = db.StringProperty()
  docstoken = db.StringProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    theresponse = ""
    user = users.get_current_user()
    if user:
      theresponse += "Hello, %s. (<a href='/signout'>Sign out</a>)<br/>" % user.nickname()
      dbU = db.GqlQuery("SELECT * FROM UsersDatabase WHERE author = :author", author=user)
      results = dbU.fetch(1)
      if len(results)==0:
       theresponse +="You are not a registered user of this website, even though you already signed up for a Google account, you still need an account in this website.<br/>You can sign up for free right <a href='signup'>here</a>.<br/><br/>"
      else:
       result = results[0]
    else:
      theresponse += """
       Seems like you are not logged in at all, totally anonymous, so weird.
       Who are you?<br/>
       You may <a href='login'>log in</a> using your Google account first.<br/>
       <font size='1+'>(<b>Tip</b> - if you already have an account in this website,
       you will not have to login twice).</font><br/><br/>"""
    theresponse += """
     Strangely enough, anyone may sign our guestbook.<br/>
     Even more strange - only contents by users with a Google account will even be saved.<br/>
     <form action="/crazy" method="post">
      <div><textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type="submit" value="Sign Guestbook"></div>
     </form><br/><br/><br/>We are standard now, yo! Do you prefer <a href="/quirks">quirks</a>?"""

    template_values = {"content": theresponse}
    self.response.out.write(unicode(template.render(PATH, template_values)))

class SigningUp(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
     theresponse = """
      All we need to know about you to make it is this - <br/>
      <form method="post" action="thankyou">E-Mail - """
     theresponse += user.email()
     theresponse += """<br/>
      Gender - <input name="gender" type="radio" value="0"> Female 
      <input name="gender" type="radio" value="1"> Male<br/>
      <input value="Sign up" type="submit"/></form>"""
     template_values = {"title": "Signing Up",
                        "content": theresponse}
     self.response.out.write(unicode(template.render(PATH, template_values)))

class SignedUpThankYou(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
     dbU = UsersDatabase();
     dbU.author = users.get_current_user()
     dbU.gender = self.request.get('gender')
     dbU.put()
    theresponse = """
     Thank you for taking the time to sign up.
     You can now move on to doing nothing in the <a href="/">main page</a>."""
    template_values = {"title": "Thank You For Signing Up",
                       "content": theresponse}
    self.response.out.write(unicode(template.render(PATH, template_values)))
    
class Guestbook(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
     dbGb = GuestbookDatabase();
     dbGb.author = users.get_current_user()
     dbGb.content = self.request.get("content")
     dbGb.put()
    theresponse = ''
    theresponse += 'You wrote:<pre>'
    theresponse += cgi.escape(self.request.get("content"))
    theresponse += '</pre>'
    if user:
      theresponse += '<br/>Your content was saved. To view it, along with other contents, please click <a href="/view">here</a>.'
    else:
      theresponse +='<br/>Your content was not saved, since you do not have a user or not logged in. To log in, click <a href="/login">here</a>. To view past contents, click <a href="/view">here</a>.'
    template_values = {"title": "Guestbook Submission Confirmation",
                       "content": theresponse}
    self.response.out.write(unicode(template.render(PATH, template_values)))

class SignInAgain(webapp.RequestHandler):
  def get(self):
   self.redirect(users.create_logout_url("/login"))

class Logout(webapp.RequestHandler):
  def get(self):
   self.redirect(users.create_logout_url("/"))

class LoginNow(webapp.RequestHandler):
  def get(self):
   self.redirect(users.create_login_url("/"))

class DeleteContent(webapp.RequestHandler):
  def get(self):
   dbGb = GuestbookDatabase()
   result = dbGb.get(db.Key(self.request.get('key')))
   result.delete()
   self.redirect("/view")
   
class GuestbookViewing(webapp.RequestHandler):
  def get(self):
   dbGb = GuestbookDatabase.all()
   results = dbGb.fetch(10,1)
   if len(results)>0:
    theresponse = ""
    for result in results:
     theresponse += "Name - " + result.author.nickname() + "<br/>"
     theresponse += "Content - " + result.content + "<br/>"
     if users.is_current_user_admin():
      theresponse += "<a href='/delete?key=%s'>Delete content</a>" % result.key()
     theresponse += "<hr/>"
    template_values = {"title": "View Guestbook",
                       "content": theresponse}
    self.response.out.write(unicode(template.render(PATH, template_values)))

   else:
     self.redirect("/")

class Quirks(webapp.RequestHandler):
 def get(self):
  self.response.out.write('<html><head><title>Quirks mode</title></head><body></body></html>')



routes = \
         [
          ('/', MainPage),
          ('/quirks', Quirks),
          ('/crazy', Guestbook),
          ('/signout', Logout),
          ('/login', LoginNow),
          ('/view', GuestbookViewing),
          ('/delete', DeleteContent),
          ('/signup', SigningUp),
          ('/thankyou', SignedUpThankYou),
          ('/signinagain', SignInAgain),
          ('/bugs', BugDatabaseViewing),
          ('/create-bug', CreateBug),
          ('/bug-process', BugProcess),
          ('/view-bug', ViewBug),
          ('/delete-bug-or-comment', DeleteBugOrComment),
          ('/add-extension', AddExtension),
          ('/extension-bugs', ExtensionDatabasesViewing),
          ('/complete-changelog', ViewExtensionChangelog),
          ('/edit-changelog', EditExtensionChangelog),
          ('/send', SendPresenceNotification),
          ('/_ah/xmpp/message/chat/', MessageReceiver),
          ('/flair-list', FlairList)
         ]
application = webapp.WSGIApplication(routes, debug=not IS_PRODUCTION)