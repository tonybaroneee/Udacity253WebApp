import os
import webapp2
import jinja2
from webapp2_extras.routes import RedirectRoute
from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

    def render_str(self, template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)

    def render(self,template,**kw):
         self.write(self.render_str(template,**kw))

class BlogHome(Handler):

    def render_front(self,title="",art="",error=""):
        self.render("front.html",title=title,art=art,error=error)

    def get(self):
        self.render_front()

    def post(self):
        title=self.request.get("title")
        art=self.request.get("art")

        if title and art:
            self.write("thanks!")
        else:
            error="we need both title and art"
            self.render_front(title,art,error)

app = webapp2.WSGIApplication([RedirectRoute('/blog/', handler=BlogHome, name='bloghome', strict_slash=True)],
                               debug=True)