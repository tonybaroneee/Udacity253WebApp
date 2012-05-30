#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
#
import webapp2
import string
import os
import jinja2
import helpers

# Declare Jinja directory and environment
template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

#
# Superclass Handler that provides helper methods for shorthand response writes
# and Jinja template writes.
#
class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render(self,template,**kw):
         self.write(self.render_str(template,**kw))

    def render_str(self, template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)

#
# Homepage Handler for displaying links to various modules 
#
class MainHandler(Handler):
    def get(self):
        self.render("home.html")

#
# Birthday Handler for handling date validation module 
#
class BirthdayHandler(Handler):
    def write_form(self, error="", month="", day="", year=""):
        self.render("birthday.html", error=error,
                                     month=month,
                                     day=day,
                                     year=year)

    def get(self):
        self.write_form()

    def post(self):
        user_month = self.request.get('month')
        user_day = self.request.get('day')
        user_year = self.request.get('year')

        month = helpers.valid_month(self.request.get('month'))
        day = helpers.valid_day(self.request.get('day'))
        year = helpers.valid_year(self.request.get('year'))

        if not (month and day and year):
            self.write_form("That doesn't look valid to me, friend.",
                            user_month, 
                            user_day, 
                            user_year)
        else:
            self.redirect('/thanks')

#
# Thanks Handler for handling acceptable inputted date from date validation module 
#
class ThanksHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Thanks! That's a totally valid day!")

#
# Rot13 Handler for handling Rot13 encoding/decoding for a block of text
#
class Rot13Handler(Handler):
    def write_form(self, input=""):
        self.render("rot13.html", input=input)

    def get(self):
        self.write_form()

    def post(self):
        translated_text = self.request.get('text').encode('rot13')
        self.write_form(translated_text)

#
# Signup Handler for handling user signup validation module 
#
class SignupHandler(Handler):
    def write_form(self, username="", password="", verify="", email="",
                   username_error="", password_error="", verify_error="", 
                   email_error=""):
        self.render("signup.html", username=username, 
                                   password=password, 
                                   verify=verify, 
                                   email=email, 
                                   username_error=username_error, 
                                   password_error=password_error, 
                                   verify_error=verify_error, 
                                   email_error=email_error)

    def get(self):
        self.write_form()

    def post(self):
        user_username = self.request.get('username')
        user_password = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')
        
        username_error = helpers.check_username(user_username)
        password_error = helpers.check_password(user_password)
        verify_error = ''
        if not password_error:
            verify_error = helpers.check_verify(user_verify, user_password)
        email_error = helpers.check_email(user_email)

        if (username_error or password_error or verify_error or email_error):
            self.write_form(user_username, '', '',
                user_email, username_error, password_error, verify_error, 
                email_error)
        else:
            self.redirect('/welcome?username=%s' % user_username)

#
# Welcome Handler for handling acceptable user signup credentials 
#
class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Welcome, %s!" % self.request.get('username'))

#
# URL routes to specific handlers 
#
app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/birthday', BirthdayHandler),
                               ('/thanks', ThanksHandler),
                               ('/rot13', Rot13Handler), 
                               ('/signup', SignupHandler),
                               ('/welcome', WelcomeHandler)], 
                               debug=True)