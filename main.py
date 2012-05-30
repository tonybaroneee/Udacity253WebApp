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
import re
import os
import blog
import jinja2

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render(self,template,**kw):
         self.write(self.render_str(template,**kw))

    def render_str(self, template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)

class MainHandler(Handler):
    def get(self):
        self.render("home.html")

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

        month = valid_month(self.request.get('month'))
        day = valid_day(self.request.get('day'))
        year = valid_year(self.request.get('year'))

        if not (month and day and year):
            self.write_form("That doesn't look valid to me, friend.",
                            escape_html(user_month), 
                            escape_html(user_day), 
                            escape_html(user_year))
        else:
            self.redirect('/thanks')

class ThanksHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Thanks! That's a totally valid day!")

class Unit2Rot13Handler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(rot13code %{'input': ''})

    def post(self):
        translated_text = escape_html(self.request.get('text').encode('rot13'))
        self.response.out.write(rot13code %{'input': translated_text})

class Unit2SignupHandler(Handler):
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
        
        username_error = check_username(user_username)
        password_error = check_password(user_password)
        verify_error = ''
        if not password_error:
            verify_error = check_verify(user_verify, user_password)
        email_error = check_email(user_email)

        if (username_error or password_error or verify_error or email_error):
            self.write_form(escape_html(user_username), '', '',
                escape_html(user_email), username_error, password_error, verify_error, 
                email_error)
        else:
            self.redirect('/unit2/welcome?username=%s' % escape_html(user_username))

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Welcome, %s!" % self.request.get('username'))


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/birthday', BirthdayHandler),
                               ('/thanks', ThanksHandler),
                               ('/unit2/rot13', Unit2Rot13Handler), 
                               ('/unit2/signup', Unit2SignupHandler),
                               ('/unit2/welcome', WelcomeHandler),
                               ('/blog', blog.MainPage)], 
                               debug=True)

def escape_html(s):
    for (i, o) in (("&", "&amp;"),
                   (">", "&gt;"),
                   ("<", "&lt;"),
                   ('"', "&quote;")):
      s = s.replace(i, o)
    return s

months = ['January', 
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December']

month_abbvs = dict((m[:3].lower(), m) for m in months)

def valid_month(month):
    if month:
        short_month = month[:3].lower()
        return month_abbvs.get(short_month)

def valid_day(day):
    if day and day.isdigit():
        day = int(day)
        if day in range(1,32):
            return day

def valid_year(year):
    if year and year.isdigit():
        year = int(year)
        if year in range(1900,2021):
            return year

def check_username(name):
    error_msg = "That's not a valid username."
    if not (USER_RE.match(name)):
        return error_msg
    else:
        return ''

def check_password(password):
    error_msg = "That's not a valid password."
    if not (PASSWORD_RE.match(password)):
        return error_msg
    else:
        return ''

def check_verify(verify, password):
    error_msg = "Your passwords didn't match."
    if verify == password:
        return ''
    else:
        return error_msg

def check_email(email):
    error_msg = "That's not a valid email."
    if not email:
        return '' # Because it's optional
    else:
        if not (EMAIL_RE.match(email)):
            return error_msg
        else:
            return ''