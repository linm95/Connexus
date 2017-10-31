#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

# [START main_page]
class LoginPage(webapp2.RequestHandler):

    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/login.html')
        self.response.write(template.render(template_values))
# [END main_page]


# [START guestbook]
class ManagePage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/manage.html')
        self.response.write(template.render(template_values))

# [END guestbook]

# [START createPage]
class CreatePage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/create.html')
        self.response.write(template.render(template_values))

# [END createPage]

# [START viewPage]
class ViewPage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/view.html')
        self.response.write(template.render(template_values))
# [END viewPage]

# [START viewSinglePage]
class ViewSinglePage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/viewSingle.html')
        self.response.write(template.render(template_values))
# [END viewSinglePage]

# [START createPage]
class SearchPage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/search.html')
        self.response.write(template.render(template_values))

# [END searchPage]

# [START trendingPage]
class TrendingPage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/trending.html')
        self.response.write(template.render(template_values))

# [END trendingPage]

# [START socialPage]
class SocialPage(webapp2.RequestHandler):
    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('/html/social.html')
        self.response.write(template.render(template_values))

# [END socialPage]

# [START app]
app = webapp2.WSGIApplication([
    ('/', LoginPage),
    ('/manage', ManagePage),
    ('/create', CreatePage),
    ('/view', ViewPage),
    ('/search', SearchPage),
    ('/trending', TrendingPage),
    ('/social', SocialPage),
    ('/viewSingle', ViewSinglePage)
], debug=True)
# [END app]
