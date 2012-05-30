import string
import re

#### VARS ####

# Regular expressions for valid username/password/email
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

# Array of all month names
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
# 3-letter abbreviations for all months
month_abbvs = dict((m[:3].lower(), m) for m in months)


#### FUNCTIONS ####

# Validate date components
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

# Validate signup components
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
