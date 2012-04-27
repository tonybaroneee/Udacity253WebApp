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

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

form = '''
<form method="post">
    What is your birthday?
    <br>

    <label> Month
        <input type="text" name="month" value="%(month)s">
    </label>
    
    <label> Day
        <input type="text" name="day" value="%(day)s">
    </label>
    
    <label> Year
        <input type="text" name="year" value="%(year)s">
    </label>
    <div style="color: red">%(error)s</div>
    <br>
    <br>
    <input type="submit">
</form>
'''

rot13code = '''
<!DOCTYPE html>
<html>
  <head>
    <title>Unit 2 Rot 13</title>
  </head>

  <body>
    <h2>Enter some text to ROT13:</h2>
    <form method="post">
      <textarea name="text" style="height: 100px; width: 400px;">%(input)s</textarea>
      <br>
      <input type="submit">
    </form>
  </body>

</html>
'''

signupcode = '''
<!DOCTYPE html>
<html>
  <head>
    <title>Sign Up</title>
    <style type="text/css">
      .label {text-align: right}
      .error {color: red}
    </style>

  </head>

  <body>
    <h2>Signup</h2>
    <form method="post">
      <table>
        <tr>
          <td class="label">
            Username
          </td>
          <td>
            <input type="text" name="username" value="%(username)s">
          </td>
          <td class="error">
            %(username_error)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input type="password" name="password" value="%(password)s">
          </td>
          <td class="error">
            %(password_error)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input type="password" name="verify" value="%(verify)s">
          </td>
          <td class="error">
            %(verify_error)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input type="text" name="email" value="%(email)s">
          </td>
          <td class="error">
            %(email_error)s
          </td>
        </tr>
      </table>

      <input type="submit">
    </form>
  </body>

</html>
'''

class MainHandler(webapp2.RequestHandler):
    def write_form(self, error="", month="", day="", year=""):
        self.response.out.write(form %{"error": error,
                                        "month": escape_html(month),
                                        "day": escape_html(day),
                                        "year": escape_html(year)})

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
                            user_month, user_day, user_year)
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

class Unit2SignupHandler(webapp2.RequestHandler):
    def write_form(self, username="", password="", verify="", email="",
                   username_error="", password_error="", verify_error="", 
                   email_error=""):
        self.response.out.write(signupcode %{'username': username,
                                            'password': password,
                                            'verify': verify,
                                            'email': email,
                                            'username_error': username_error,
                                            'password_error': password_error,
                                            'verify_error': verify_error,
                                            'email_error': email_error})

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
                               ('/thanks', ThanksHandler),
                               ('/unit2/rot13', Unit2Rot13Handler), 
                               ('/unit2/signup', Unit2SignupHandler),
                               ('/unit2/welcome', WelcomeHandler)], 
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