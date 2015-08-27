# !/usr/bin/env python

from tools import *

#import datetime

from google.appengine.ext import db
from google.appengine.api import channel,users
from google.appengine.api.users import User
import jinja2

    
@db.transactional
def getPlayer(user,put=True):
    if user.email().startswith("p "):
        return None
    if user.email().startswith("a "):
        return None
    assert " " not in user.email()#warning, may not count some valid addresses
    kname=str(hash_(user.nickname()))
    pl=Player.get_by_key_name(kname)
    if not pl:
        pl=Player(key_name=kname,
            account=user,
            score=1000,
            token=channel.create_channel(user.email()),
            playername="New_User")
        if put:pl.put()
    return pl
        

@db.transactional
def getCurrentPlayer(put=True):
    u=users.get_current_user()
    if u:
        pl=getPlayer(u,put=False)
        pl.lastOnline=datetime.now()
        if put:pl.put()
        return pl

def getCurrentUser(pnum,put=True):
    u=users.get_current_user()
    if u:
        pl=getPlayer(u,put=False)
        pl.lastOnline=datetime.now()
        if put:pl.put()
        return u
    else:
        assert pnum
        return User("p "+pnum)
        
    
class Player(db.Model):
    """Stores information about players"""
    account=db.UserProperty()
    token=db.StringProperty()
    playername=db.StringProperty()
    score=db.IntegerProperty()
    lastOnline=db.DateTimeProperty(auto_now_add=True)#if they haven't done anything for 2 minutes, assume they are offline
    dateJoined=db.DateTimeProperty(auto_now_add=True)


    def changeName(self,newName,put=True):
        if len(newName)<20 and all(c in "qwertyuiopasdfghjklzxcvbnm" for c in newName):
            self.playername=newName
            if put:self.put()
            return True
        
    def getName(self,em=False):
        ret=self.username
        if em:ret="<em>"+ret+"</em>"
        return ret
        
    def send(self,message):
        if not isinstance(message,str):message=sjd(message)
        channel.send_message(self.account.email(),message)

##class Clear(webapp.RequestHandler):
##    """clear all game data"""
##    def get(self):
##        db.delete(PlayerData.all(keys_only=True).run())

        
