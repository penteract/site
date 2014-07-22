import webapp2,logging

class LowerCaseRedirecter(webapp2.RequestHandler):
    def get(self,path,rest):
        logging.warning("CASE "+path+rest)
        self.redirect(path.lower()+rest,permanent=True)
    def post(self,path,rest):
        logging.error("CASE "+path+rest)
        self.redirect(path.lower()+rest,permanent=True)
        
app = webapp2.WSGIApplication([('([^?]*[A-Z][^?]*)(.*)', LowerCaseRedirecter)])