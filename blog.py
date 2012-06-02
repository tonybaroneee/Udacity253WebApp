import os
from string import letters

import webapp2
import jinja2
import logging
from google.appengine.ext import db
from webapp2_extras.routes import RedirectRoute

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template,**params):
        return render_str(template, **params)

    def render(self,template,**kw):
         self.write(self.render_str(template,**kw))

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        return render_str("blog/post.html", p = self)

class BlogHome(Handler):
    def get(self):
        #posts = db.GqlQuery("select * from Post order by created desc limit 10")
        posts = db.GqlQuery("SELECT * "
                            "FROM Post "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY created DESC LIMIT 10",
                            blog_key())
        self.render("blog/home.html", posts=posts)

class BlogNewPost(Handler):
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

class BlogPermalink(Handler):
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
                               ],
                               debug=True)