import os
from string import letters

import webapp2
import jinja2
import json

import logging
import helpers

from datetime import datetime, timedelta
from google.appengine.api import memcache
from google.appengine.ext import db
from webapp2_extras.routes import RedirectRoute

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template,**params):
        return render_str(template, **params)

    def render(self,template,**kw):
         self.write(self.render_str(template,**kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    def set_secure_cookie(self, name, val):
        cookie_val = helpers.make_secure_val(val)
        self.response.set_cookie('user_id', cookie_val, path='/')

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and helpers.check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.set_cookie('user_id', '', path='/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name = ', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = helpers.make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and helpers.valid_pw(name, pw, u.pw_hash):
            return u

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        return render_str("blog/post.html", p = self)

    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt)}
        return d

class BlogHome(BlogHandler):
    def get(self):
        posts, age = get_posts()
        if self.format == 'html':
            self.render("blog/home.html", posts=posts, age=age_str(age))
        else:
            return self.render_json([p.as_dict() for p in posts])

#
# Signup Handler for handling user signup validation module 
#
class SignupHandler(BlogHandler):
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
        self.user_username = self.request.get('username')
        self.user_password = self.request.get('password')
        self.user_verify = self.request.get('verify')
        self.user_email = self.request.get('email')
        
        username_error = helpers.check_username(self.user_username)
        password_error = helpers.check_password(self.user_password)
        verify_error = ''
        if not password_error:
            verify_error = helpers.check_verify(self.user_verify, self.user_password)
        email_error = helpers.check_email(self.user_email)

        if (username_error or password_error or verify_error or email_error):
            self.write_form(self.user_username, '', '',
                self.user_email, username_error, password_error, verify_error, 
                email_error)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Unit2Signup(SignupHandler):
    def done(self):
        self.redirect('/welcome?username=%s' % user_username)

class BlogSignup(SignupHandler):
    def done(self):
        # check that user doesn't exist
        u = User.by_name(self.user_username)
        if u:
            msg = 'That user already exists.'
            self.render('blog/signup.html', username_error = msg)
        else:
            u = User.register(self.user_username, self.user_password, self.user_email)
            u.put()

            self.login(u)
            self.redirect('/blog/welcome')

class BlogLogin(BlogHandler):
    def get(self):
        self.render('/blog/login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog/welcome')
        else:
            msg = 'Invalid login'
            self.render('blog/login-form.html', error = msg)

class BlogLogout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog/signup')

#
# Welcome Handler for handling acceptable registration 
#
class BlogWelcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('/blog/welcome.html', username = self.user.name)
        else:
            self.redirect('/blog/signup')


class BlogNewPost(BlogHandler):
    def get(self):
        self.render("blog/newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()

            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error="subject and content, please!"
            self.render("blog/newpost.html",subject=subject,content=content,error=error)

class BlogPermalink(BlogHandler):
    def get(self, post_id):
        post_key = 'POST_' + post_id

        post, age = age_get(post_key)
        if not post:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            age_set(post_key, post)
            age = 0

        if not post:
            self.error(404)
            return
        if self.format == 'html':
            self.render("blog/permalink.html", post=post, age = age_str(age))
        else:
            self.render_json(post.as_dict())

class BlogCacheFlush(BlogHandler):
    def get(self):
        memcache.flush_all()
        self.redirect("/blog")

def age_set(key, val):
    save_time = datetime.utcnow()
    memcache.set(key, (val, save_time))

def age_get(key):
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow() - save_time).total_seconds()
    else:
        val, age = None, 0

    return val, age

def add_post(ip, post):
    post.put()
    get_posts(update = True)
    return str(post.key().id())

def get_posts(update = False):
    q = Post.all().order('-created').fetch(limit = 10)
    mc_key = 'BLOGS'

    posts, age = age_get(mc_key)
    if update or posts is None:
        posts = list(q)
        age_set(mc_key, posts)

    return posts, age

def age_str(age):
    s = 'queried %s seconds ago'
    age = int(age)
    if age == 1:
        s = s.replace('seconds', 'second')
    return s % age


app = webapp2.WSGIApplication([('/blog/?(?:\.json)?', BlogHome),
                               ('/blog/([0-9]+)(?:\.json)?', BlogPermalink),
                               ('/blog/newpost', BlogNewPost),
                               ('/blog/signup', BlogSignup),
                               ('/blog/login', BlogLogin),
                               ('/blog/logout', BlogLogout),
                               ('/blog/welcome', BlogWelcome),
                               ('/blog/flush', BlogCacheFlush),
                               ],
                               debug=True)