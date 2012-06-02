import os
import webapp2
import jinja2
from webapp2_extras.routes import RedirectRoute
from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)

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
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("blog/post.html", p = self)

class BlogHome(Handler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render("blog/home.html", posts=posts)

class BlogNewPost(Handler):
    def render_newpost(self,subject="",content="",error=""):
        self.render("blog/newpost.html",subject=subject,content=content,error=error)

    def get(self):
        self.render_newpost()

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()

            self.redirect('/blog/%s/' % str(p.key().id()))
        else:
            error="subject and content, please!"
            self.render_newpost(subject,content,error)

class Post(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("blog/permalink.html", post = post)

app = webapp2.WSGIApplication([RedirectRoute('/blog/', handler=BlogHome, name='blog_home', strict_slash=True),
                               RedirectRoute('/blog/newpost/', handler=BlogNewPost, name='blog_newpost', strict_slash=True),
                               RedirectRoute('/blog/([0-9]+)/', handler=Post, name='blog_post', strict_slash=True)],
                               debug=True)