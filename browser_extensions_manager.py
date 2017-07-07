from google.appengine.ext import db, webapp
from google.appengine.api import mail, users
from datetime import datetime

import urllib
import re

from constants \
 import EXTENSION_GALLERY, AUTHOR_EMAIL, \
 BUG_DATABASE_NO_REPLY_EMAIL, ORIGIN

from util import render_template

class ExtensionsDatabase(db.Model):
 name = db.StringProperty(multiline=False)
 eid = db.StringProperty(multiline=False)
 changelog = db.TextProperty()
   
class TechnicalSupportDatabase(db.Model):
  author = db.StringProperty(multiline=False)
  email = db.StringProperty(multiline=False)
  content = db.TextProperty()
  dateAdded = db.DateTimeProperty(indexed=True)
  bugKey = db.StringProperty(multiline=False,indexed=True)

class IssueDatabase(db.Model):
  author = db.StringProperty(multiline=False)
  email = db.StringProperty(multiline=False)
  title = db.StringProperty(multiline=False)
  dateAdded = db.DateTimeProperty()
  content = db.TextProperty()
  extension = db.StringProperty(multiline=False)
  emails = db.StringProperty(multiline=True)

class CreateBug(webapp.RequestHandler):
  def get(self):
   extension = self.request.get('extension')
   author_from_cookie = self.request.cookies.get("author")
   email_from_cookie = self.request.cookies.get("email")
   emailme_from_cookie = self.request.cookies.get("emailme")
   theresponse = "<a href='/bugs?extension=" + urllib.quote(extension) + "'>Return to the list of issues</a><br/>"
   theresponse += "<form action='/bug-process' method='post'><h1>Create a new issue</h1>"
   theresponse += "<input type='hidden' name='extension' value='" + extension + "' size='50'/>"
   theresponse += "<input type='hidden' name='action' value='new' size='50'/>"
   theresponse += "Author <input type='text' name='author' size='50' value='"
   if author_from_cookie != None:
    theresponse += author_from_cookie.replace("'","&quot;")
   theresponse += "'/><br/>"
   theresponse += "E-Mail (only visible to the developer) <input type='text' size='50' name='email' value='"
   if email_from_cookie != None:
    theresponse += email_from_cookie.replace("'","&quot;")
   theresponse += "'><br/>"
   theresponse += "<input type='checkbox' name='emailme'"
   if emailme_from_cookie == None or emailme_from_cookie == "true":
    theresponse += " checked='true'"
   theresponse += " id='emails'><label for='emails'>E-Mail me whenever a new comment is added.</label><br/>"
   theresponse += "Summary <input type='text' name='title' size='55'/><br/>"
   theresponse += "<textarea name='content' cols='50' rows='20'>Google Chrome version (about:version) - \n</textarea><br/>"
   theresponse += "<input type='submit'></form>"
   template_values = {"title": "Create An Issue",
                      "content": theresponse}
   self.response.out.write(render_template(template_values))

class BugProcess(webapp.RequestHandler):
  def post(self):
   action = self.request.get('action')
   extension = self.request.get('extension')
   author = self.request.get('author')
   email = self.request.get('email')
   if not len(email) > 5 or not email.find('@') > 0:
    email = ""
   emailmeforcookie = emailme = self.request.get('emailme')
   if emailme == "on":
    emailmeforcookie = "true"
   self.response.headers.add_header(
       'Set-Cookie', 
       'author=%s; expires=Fri, 31-Dec-2027 23:59:59 GMT' \
         % author.encode())
   self.response.headers.add_header(
       'Set-Cookie', 
       'emailme=%s; expires=Fri, 31-Dec-2027 23:59:59 GMT' \
         % str(emailmeforcookie).lower())
   self.response.headers.add_header(
       'Set-Cookie', 
       'email=%s; expires=Fri, 31-Dec-2027 23:59:59 GMT' \
         % email.encode())
   if action == "new":
    if len(author) == 0 or author == "":
     author = "(Unknown Reporter)"
    dbIssues = IssueDatabase()
    dbIssues.author = author
    dbIssues.email = email
    dbIssues.title = self.request.get('title')
    dbIssues.content = self.request.get("content")
    dbIssues.extension = extension
    dbIssues.dateAdded = datetime.today();
    if emailme == "on":
     dbIssues.emails = email
    dbIssues.put()
    newBugKey = "%s" % dbIssues.key()
    mail.send_mail(BUG_DATABASE_NO_REPLY_EMAIL,
                   AUTHOR_EMAIL,
                   "A New Bug Was Filed",
                   ORIGIN + "/view-bug?extension=" + urllib.quote(extension) + "&key=" + newBugKey)
    self.redirect('/bugs?extension=' + extension)
   if action == "comment":
    if len(author) == 0 or author == "":
     author = "(Unknown Commenter)"
    bugKey = self.request.get('bugKey')
    dbIssueComments = TechnicalSupportDatabase()
    dbIssueComments.bugKey = bugKey
    dbIssueComments.author = author
    dbIssueComments.email = email
    dbIssueComments.content = self.request.get("content")
    dbIssueComments.dateAdded = datetime.today();
    dbIssues = IssueDatabase()
    issue = dbIssues.get(db.Key(bugKey))
    emails = ""
    if (issue):
     emails = "," + re.sub(email + "[,]*","",issue.emails)
     issue.emails = re.sub(email + "[,]*","",issue.emails) + "," + email
     issue.put()
    mail.send_mail(BUG_DATABASE_NO_REPLY_EMAIL, AUTHOR_EMAIL + emails,"A New Comment Was Added", ORIGIN + "/view-bug?extension=" + urllib.quote(extension) + "&key=" + bugKey)
    dbIssueComments.put()
    self.redirect("/view-bug?extension=" + extension + "&key=" + bugKey + "&emails=" + emails)

class DeleteBugOrComment(webapp.RequestHandler):
  def get(self):
   extension = self.request.get('extension')
   if users.is_current_user_admin():
    action = self.request.get('action')
    key = self.request.get('key')
    if (action == "comment"):
     bugKey = self.request.get('bugKey')
     dbIssueComments = TechnicalSupportDatabase()
     result = dbIssueComments.get(db.Key(key))
     result.delete()
     self.redirect("/view-bug?extension=" + extension + "&key=" + bugKey)
    if (action == "bug"):
     dbIssues = IssueDatabase()
     result = dbIssues.get(db.Key(key))
     result.delete()
     dbIssueComments = db.GqlQuery("SELECT * FROM TechnicalSupportDatabase " +
                                   "WHERE bugKey = '" + key + "'")
     results = dbIssueComments.fetch(500)
     for result in results:
      result.delete()
     self.redirect("/bugs?extension=" + urllib.quote(extension))
    else:
     self.redirect("/bugs?extension=" + urllib.quote(extension))
   

class ViewBug(webapp.RequestHandler):
  def get(self):
   dbIssues = IssueDatabase()
   bugKey = self.request.get('key')
   extension = self.request.get('extension')
   author_from_cookie = self.request.cookies.get("author")
   email_from_cookie = self.request.cookies.get("email")
   emailme_from_cookie = self.request.cookies.get("emailme")
   theresponse = "<a href='/bugs?extension=" + urllib.quote(extension) + "'>Return to the list</a>"
   result = dbIssues.get(db.Key(bugKey))
   if result:
    if users.is_current_user_admin() and len(result.email) > 5 and result.email.find('@') > 0:
     issue_author = "<a href='mailto:" + result.email + "'>" + result.author + "</a>"
    else:
     issue_author = result.author
    theresponse += "<h1>" + result.title + "</h1>By " + issue_author + ", regarding " + result.extension + "<br/>"
    theresponse += "<pre>" + result.content + "</pre>"
   else:
    theresponse += "<h4>This issue does not exist (anymore?).</h4>"
   dbIssueComments = TechnicalSupportDatabase()
   dbIssueComments = db.GqlQuery("SELECT * FROM TechnicalSupportDatabase " +
                                  "WHERE bugKey = '" + bugKey + "' ORDER BY dateAdded")
   comments = dbIssueComments.fetch(1000)
   if len(comments) > 0:
    theresponse += "<h2>Comments</h2>"
    for comment in comments:
     if users.is_current_user_admin() and len(comment.email) > 5 and comment.email.find('@') > 0:
      theresponse += "<a href='mailto:" + comment.email + "'>" + comment.author + "</a>"
     else:
      theresponse += comment.author
     theresponse += " (" + str(comment.dateAdded) + ") -<br/>"
     theresponse += "<pre>" + comment.content + "</pre><br/>"
     commentKey = "%s" % comment.key()
     if users.is_current_user_admin():
      theresponse += "<a href='/delete-bug-or-comment?extension=" + urllib.quote(extension) + "&action=comment&key=" + commentKey + "&bugKey=" + bugKey + "'>Delete</a><hr/>"
   if result:
    theresponse += "<form action='/bug-process' method='post'><h2>Add comments</h2>"
    theresponse += "<input type='hidden' name='extension' value='" + extension + "' size='50'/>"
    theresponse += "<input type='hidden' name='bugKey' value='" + bugKey + "' size='50'/>"
    theresponse += "<input type='hidden' name='action' value='comment' size='50'/>"
    theresponse += "Author <input type='text' name='author' size='50' value='"
    if author_from_cookie != None:
     theresponse += author_from_cookie.replace("'","&quot;")
    theresponse += "'/><br/>"
    theresponse += "E-Mail (only visible to the developer) <input type='text' size='50' name='email' value='"
    if email_from_cookie != None:
     theresponse += email_from_cookie.replace("'","&quot;")
    theresponse += "'><br/>"
    theresponse += "<input type='checkbox' name='emailme'"
    if emailme_from_cookie == None or emailme_from_cookie == "true":
     theresponse += " checked='true'"
    theresponse += " id='emails'><label for='emails'>E-Mail me whenever a new comment is added.</label><br/>"
    theresponse += "<textarea name='content' cols='50' rows='10'></textarea><br/>"
    theresponse += "<input type='submit'></form>"
   template_values = {"title": "View Issue",
                      "content": theresponse}
   self.response.out.write(render_template(template_values))
   
class AddExtension(webapp.RequestHandler):
 def get(self):
  dbExtensions = ExtensionsDatabase()
  dbExtensions.name = self.request.get("name")
  dbExtensions.eid = self.request.get("eid")
  dbExtensions.changelog = "0.1 - Initial release."
  dbExtensions.put()
  self.redirect("/extension-bugs")

class EditExtensionChangelog(webapp.RequestHandler):
 def post(self):
  extension = self.request.get("extension")
  dbExtensions = ExtensionsDatabase.gql("WHERE name = '" + extension + "'")
  for result in dbExtensions.fetch(1):
   result.changelog = self.request.get("changelog")
   result.put()
  self.redirect("/extension-bugs")
  
class ViewExtensionChangelog(webapp.RequestHandler):
 def get(self):
  extension = self.request.get("extension")
  query = db.GqlQuery("SELECT * FROM ExtensionsDatabase WHERE name = '" + extension + "'")
  theresponse = "<a href='/extension-bugs'>Return to the extension list</a>"
  for result in query.fetch(1):
   theresponse += "<h1>" + extension + " Changelog</h1>"
   if users.is_current_user_admin():
    theresponse += "<form method='post' action='/edit-changelog'>"
    theresponse += "<input type='hidden' name='extension' value='" + extension + "'/>"
    theresponse += "<textarea name='changelog' rows='10' cols='60'>"
   else:
    theresponse += "<pre style='width: 400px'>"
   theresponse += result.changelog
   if users.is_current_user_admin():
    theresponse += "</textarea><br/>"
    theresponse += "<input type='submit' value='Save Changelog'/>"
    theresponse += "</form>"
   else:
    theresponse += "</pre>"
  template_values = {"title": extension + " Changelog",
                     "content": theresponse}
  self.response.out.write(render_template(template_values))

class ExtensionDatabasesViewing(webapp.RequestHandler):
  def get(self):
   extensions = ExtensionsDatabase.all()
   theresponse = "<h1>Extensions Bug Database</h1>"
   for extensionResult in extensions:
    extension = extensionResult.name
    extension_link = EXTENSION_GALLERY + extensionResult.eid
    dbIssues = db.GqlQuery("SELECT * FROM IssueDatabase WHERE extension = '" + extension + "'")
    results = dbIssues.fetch(1000)
    extensionsBugs = len(results)
    theresponse += "<a href='/bugs?extension=" + urllib.quote(extension) + "'>" + extension + "</a> (" + str(extensionsBugs) + ") (<a href='" + extension_link + "'>link</a>) (<a href='/complete-changelog?extension=" + extension + "'>Complete Changelog</a>)<br/>"
   if users.is_current_user_admin():
    theresponse += "<br/><br/><form action='/add-extension'>Name - <input type='text' name='name' size='60'/><br/>"
    theresponse += "ID - <input type='text' name='eid' size='60'/><br/>"
    theresponse += "<input type='submit' value='Add Extension'/>"
    theresponse += "</form>"
   template_values = {"title": "Extensions Bug Database",
                      "content": theresponse}
   self.response.out.write(render_template(template_values))

class BugDatabaseViewing(webapp.RequestHandler):
  def get(self):
   extension = self.request.get('extension')
   dbIssues = db.GqlQuery("SELECT * FROM IssueDatabase WHERE extension = '" + extension + "'")
   results = dbIssues.fetch(100)
   theresponse = "<a href='/extension-bugs'>Return to the extension list</a> <a href='/create-bug?extension=" + urllib.quote(extension) + "'>Create a new issue</a><br/>"
   theresponse += "<h1>Issues for <font color='red'>" + extension + "</font></h1>"
   if len(results) > 0:
    theresponse += "<table>"
    theresponse += "<tr><th align='left'>Reporter</th><th align='left'>Summary</th><th></th></tr>"
    for result in results:
     theresponse += "<tr>"
     key = "%s" % result.key()
     if users.is_current_user_admin() and len(result.email) > 5 and result.email.find('@') > 0:
       theresponse += "<td><a href='mailto:" + result.email + "'>" + result.author + "</a></td>"
     else:
       theresponse += "<td>" + result.author + "</td>"
     theresponse +="<td><a href='/view-bug?extension=" + urllib.quote(extension) + "&key=" + key + "'>" + result.title + "</a></td>"
     if users.is_current_user_admin():
      theresponse += "<td>(<a href='/delete-bug-or-comment?extension=" + urllib.quote(extension) + "&action=bug&key=" + key + "'>delete</a>)</td>"
     theresponse += "</tr>"
    theresponse += "</table>"
   else:
    theresponse += "No issues (yet?)."
   template_values = {"title": extension + " Issues",
                      "content": theresponse}
   self.response.out.write(render_template(template_values))