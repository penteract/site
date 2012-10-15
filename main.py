# !/usr/bin/env python

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

class MainPage(webapp.RequestHandler):
    """ Renders the main template."""
    def get(self):
        template_values = { 'title':'AJAX Add (via GET)', }
        path = os.path.join(os.path.dirname(__file__), "canvas.html")
        self.response.out.write(template.render(path, template_values))

class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""

    def get(self):
        func = None

        action = self.request.get('action')
        if action=="Add":
            try:
                num1 = int(self.request.get('arg1'))
                num2 = int(self.request.get('arg2'))
            except ValueError:
                self.error(400)#invalid input
                return
            self.response.out.write(str(num1+num2))
        else: self.error(403) # access denied


  
app = webapp.WSGIApplication([
    ('/', MainPage),
    ('/rpc', RPCHandler),
     ], debug=True)
        