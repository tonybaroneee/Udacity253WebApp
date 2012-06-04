from string import letters
import re
import hashlib
import hmac
import random

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

# Secret key for hmac algo
secretKey = "1234567890"

#### FUNCTIONS ####

# Secure hashing functions for cookie generation and parsing
def make_secure_val(val):
    return "%s|%s" %(val, hmac.new(secretKey, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

# Secure password storage
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

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
