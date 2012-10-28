# !/usr/bin/env python

import os
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from django.utils import simplejson
from google.appengine.ext import db
import jinja2

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class show(Exception):
    def __init__(self,s):
        self.s=s
    def __str__(self):
        return repr(self.s)

class GameData(db.Model):
    turn=db.StringProperty()#"O" or "X"
    winner=db.StringProperty()#"","O" or "X"
    board=db.StringProperty()#" ","O" or "X" 64 times
  
def game_key(gameNum):
    """Constructs a Datastore key for a Start entity with a given id."""
    return db.Key.from_path('GameData',gameNum)
    
class MainPage(webapp.RequestHandler):
    """ Renders the main template."""
    def get(self):
        gmNum=self.request.get('gameID')
        if gmNum=="":
            gmNum="5"
        template_values = {'gameID':gmNum}
        
        template = jinja_environment.get_template('canvas.html')
        self.response.out.write(template.render(template_values))

class AjaxHandler(webapp.RequestHandler):
    """handles turns sent and polls for new data"""
    def get(self):
        #lastUpdate = self.request.get('lastUpdate')
        gameID = game_key(self.request.get('gameID'))
        gm=GameData.get(gameID)
        self.response.out.write(simplejson.dumps({"board":gm.board}))

    def post(self):
        pos = self.request.get('pos')
        x,y,z=(int(c) for c in pos)
        player = self.request.get('player')
        gameID = game_key(self.request.get('gameID'))
        gm=GameData.get(gameID)
        game=Game(gm)
        pos=16*z+4*y+x
        gm.board=gm.board[:pos]+player+gm.board[pos+1:]
        gm.put()
        
class NewGame(webapp.RequestHandler):
    """ produces an id for a new game"""
    def post(self):
        gameID = game_key(self.request.get('gameID'))
        gm=GameData(key=gameID)
        gm.turn="X"
        gm.board=" "*64
        gm.winner=""
        gm.put()
        
class Clear(webapp.RequestHandler):
    """clear all game data"""
    def get(self):
        db.delete(Game.all(keys_only=True).run())

class Game():
    def __init__(self,gmData):
        bd=gmData.board
        l=[]
        for z in range(4):
            l.append([])
            for y in range(4):
                l[-1].append(bd[z*16+y*4:z*16+y*4+4])
        self.board=l
        self.turn=gmData.turn
        self.won=not not gmData.winner
        
    def linesThrough(self,x,y,z):
        bd=self.board
        lines=[[],[],[]]
        for n in range(4):
            lines[0].append(bd[n][y][z])
            lines[1].append(bd[x][n][z])
            lines[2].append(bd[x][y][n])
        xp=abs(x-1.5)
        yp=abs(y-1.5)
        zp=abs(z-1.5)
        if xp==yp:
            lines.append([])
            for n in range(4):
                lines[-1].append(bd[n][n if y==x else 3-n][z])
        if xp==zp:
            lines.append([])
            for n in range(4):
                lines[-1].append(bd[n][y][n if z==x else 3-n])
        if yp==zp:
            lines.append([])
            for n in range(4):
                lines[-1].append(bd[x][n][n if y==z else 3-n])
        if xp==yp and xp==zp:
            lines.append([])
            for n in range(4):
                lines[-1].append(bd[n][n if y==x else 3-n][n if x==z else 3-n])
        return lines

app = webapp.WSGIApplication([
    ('/post', AjaxHandler),
    ('/get', AjaxHandler),
    ('/clr', NewGame),
    #('/clrall', Clear),
    ('/', MainPage),
     ], debug=True)
        