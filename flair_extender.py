from google.appengine.ext import webapp

from constants import HOST_NAME

class FlairList(webapp.RequestHandler):
 def get(self):
  self.response.headers["Access-Control-Allow-Origin"] = "*"
  self.response.headers["Access-Control-Allow-Methods"] = "GET"
  self.response.headers["Access-Control-Max-Age"] = "1728000"
  self.response.out.write(unicode( \
"""{
 "list":
  [
   "//%s/flairs/chat.png",
   "//%s/flairs/birthday.png",
   "//%s/flairs/classic-fat-smile.png",
   "//%s/flairs/fat-smile.png"
  ]
}""" % (HOST_NAME, HOST_NAME, HOST_NAME, HOST_NAME)))