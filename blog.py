import os
from string import letters

import webapp2
import jinja2

import logging
import helpers

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

class BlogHome(BlogHandler):
    def get(self):
        #posts = db.GqlQuery("select * from Post order by created desc limit 10")
        posts = db.GqlQuery("SELECT * "
                            "FROM Post "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY created DESC LIMIT 10",
                            blog_key())
        self.render("blog/home.html", posts=posts)

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
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("blog/permalink.html", post = post)

app = webapp2.WSGIApplication([('/blog/?', BlogHome),
                               ('/blog/([0-9]+)', BlogPermalink),
                               ('/blog/newpost', BlogNewPost),
                               ('/blog/signup', BlogSignup),
                               ('/blog/login', BlogLogin),
                               ('/blog/logout', BlogLogout),
                               ('/blog/welcome', BlogWelcome),
                               ],
                               debug=True)