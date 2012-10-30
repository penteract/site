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

class InvalidInput(Exception):
    def __init__(self,input,excpected,msg):
        self.input=input
        self.excpected=excpected
        self.msg=msg
    def __str__(self):
        return "excpected: "+self.excpected+"\nbut recieved"+repr(self.input)
        
def check(a,b,msg):
    """raises an error if inputs are not equal"""
    if a!=b:raise InvalidInput(a,b,msg)

class GameData(db.Model):
    turn=db.StringProperty()#"O" or "X"
    winpos=db.StringProperty()#"" or "xyz"
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
        gameID = game_key(gmNum)
        gm=GameData.get(gameID)
        #if someone else creates a game with the same key at this point it will be overwritten, but that shouldn't matter because they would both be identical
        if gm==None:
            gm=GameData(key_name=gmNum)
            gm.turn="X"
            gm.board=" "*64
            gm.winpos=""
            gm.put()
        #doesn't always show the board, may be a problem with caching
        template_values = {'gameID':gmNum,"board":gm.board}
        
        template = jinja_environment.get_template('canvas.html')
        self.response.out.write(template.render(template_values))

class AjaxHandler(webapp.RequestHandler):
    """handles turns sent and polls for new data"""
    def get(self):
        gameID = game_key(self.request.get('gameID'))
        gm=GameData.get(gameID)
        game=Game(gm)
        self.response.out.write(simplejson.dumps(game.getData()))

    def post(self):
        pos = self.request.get('pos')
        x,y,z=(int(c) for c in pos)
        player = self.request.get('player')
        gameID = game_key(self.request.get('gameID'))
        gm=GameData.get(gameID)
        game=Game(gm)
        pos=16*z+4*y+x
        try: game.go(player,x,y,z)
        except InvalidInput as e:
            self.response.out.write(simplejson.dumps({"error":e.msg}))
            return None
        game.sync(gm)
        gm.put()
        data={"error":"none"}
        self.response.out.write(simplejson.dumps(data))
        
class NewGame(webapp.RequestHandler):
    """ produces an id for a new game"""
    def post(self):
        gameID = game_key(self.request.get('gameID'))
        gm=GameData(key=gameID)
        gm.turn="X"
        gm.board=" "*64
        gm.winpos=""
        gm.put()
        
class Clear(webapp.RequestHandler):
    """clear all game data"""
    def get(self):
        db.delete(GameData.all(keys_only=True).run())

class Game():
    def __init__(self,gmData):
        bd=gmData.board
        l=[]
        for z in range(4):
            l.append([])
            for y in range(4):
                l[-1].append([])
                for x in range(4):
                    l[-1][-1].append(bd[z*16+y*4+x])
        self.board=l
        self.turn=gmData.turn
        self.winpos=gmData.winpos
        self.wonlines=[]
        if gmData.winpos:
            x,y,z=(int(n) for n in self.winpos)
            c=self.board[z][y][x]
            for line in self.linesThrough(x,y,z):
                if all([p==c for p in line[0]]):
                    self.wonlines.append(line[1])
        
            
        
    def getData(self):
        d={}
        d["board"]="".join(["".join(["".join(y) for y in z]) for z in self.board])
        d["wonlines"]=self.wonlines
        return d
        
    def go(self,player,x,y,z):
        check(self.wonlines,[],"game's over")
        check(player,self.turn,"it is not your turn")
        check(self.board[z][y][x]," ","you must go in an empty cell")
        self.board[z][y][x]=player
        for line in self.linesThrough(x,y,z):
            if all([p==player for p in line[0]]):
                self.wonlines.append(line[1])
        if self.wonlines: self.winpos=str(x)+str(y)+str(z)
        self.turn={"X":"O","O":"X"}[self.turn]
        
        
    def sync(self,gameData):
        gameData.board=self.getData()["board"]
        gameData.turn=self.turn
        gameData.winpos=self.winpos
    
    def linesThrough(self,x,y,z):
        """returns a list of the lines through a point in the form [(["X","O","O","O"],[[0,2,3],[1,2,3],[2,2,3],[3,2,3]]),(["O"...],[...]),...]"""
        bd=self.board
        lines=[([],[]),([],[]),([],[])]
        for n in range(4):
            lines[0][0].append(bd[n][y][x])
            lines[1][0].append(bd[z][n][x])
            lines[2][0].append(bd[z][y][n])
            lines[0][1].append([x,y,n])
            lines[1][1].append([x,n,z])
            lines[2][1].append([n,y,z])
        xp=abs(x-1.5)
        yp=abs(y-1.5)
        zp=abs(z-1.5)
        if zp==yp:
            lines.append(([],[]))
            for n in range(4):
                lines[-1][0].append(bd[n][n if y==z else 3-n][x])
                lines[-1][1].append([x,n if y==z else 3-n,n])
        if zp==xp:
            lines.append(([],[]))
            for n in range(4):
                lines[-1][0].append(bd[n][y][n if x==z else 3-n])
                lines[-1][1].append([n if x==z else 3-n,y,n])
        if yp==xp:
            lines.append(([],[]))
            for n in range(4):
                lines[-1][0].append(bd[z][n][n if y==x else 3-n])
                lines[-1][1].append([n if y==x else 3-n,n,z])
        if zp==yp and zp==xp:
            lines.append(([],[]))
            for n in range(4):
                lines[-1][0].append(bd[n][n if y==z else 3-n][n if z==x else 3-n])
                lines[-1][1].append([n if z==x else 3-n,n if y==z else 3-n,n])
        return lines

app = webapp.WSGIApplication([
    ('/post', AjaxHandler),
    ('/get', AjaxHandler),
    ('/clr', NewGame),
    #('/clrall', Clear),
    ('/', MainPage),
     ], debug=True)
        