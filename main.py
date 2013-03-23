# !/usr/bin/env python

import os
import datetime

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.api import channel,users
from django.utils import simplejson
import jinja2
from time import clock
from datetime import datetime
from random import randrange

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


#error handling
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
        return "excpected: "+repr(self.excpected)+"\nbut recieved"+repr(self.input)
        
def check(a,b,msg):
    """raises an error if inputs are not equal"""
    if a!=b:raise InvalidInput(a,b,msg)



class GameData(db.Model):
    turn=db.StringProperty()#"O" or "X"
    winpos=db.StringProperty()#"" or "xyz"
    board=db.StringProperty()#" ","O" or "X" 64 times
    timeCreated = db.DateTimeProperty(auto_now_add=True)
    playerX=db.UserProperty()
    playerO=db.UserProperty()
    timeLimit=db.IntegerProperty()
    lastTurn=db.DateTimeProperty()
    started=db.BooleanProperty()
  
def game_key(gameNum):
    """Constructs a Datastore key for a GameData entity with a given id."""
    if all([c in "1234567890" for c in gameNum]):
        return db.Key.from_path('GameData',gameNum)
    else: return gameNum

class PlayerData(db.Model):
    account=db.UserProperty()
    token=db.StringProperty()
    username=db.StringProperty()
    score=db.IntegerProperty()
    lastOnline =db.DateTimeProperty()
    online=db.BooleanProperty()#if False, definitely not online
    dateJoined = db.DateTimeProperty(auto_now_add=True)
    
def getPlayer(nickname):
    return PlayerData.get(db.Key.from_path('PlayerData',str(hash(nickname))))
    
@db.transactional
def playerName(nickname,em=False):
    p=getPlayer(nickname)
    if not p:return None
    ret=p.username
    if em:ret="<em>"+ret+"</em>"
    return ret
    
@db.transactional
def getCurrentPlayer():
    """gets the Entity for the player currently logged in and redirects them if necessary"""
    user = users.get_current_user()
    if not user:
        return None
    pl=getPlayer(user.nickname())
    if not pl:
        return None
    pl.lastOnline=datetime.now()
    pl.online=True
    pl.put()
    return pl

    
class WelcomePage(webapp.RequestHandler):
    """for users who have not logged in yet"""
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect("/user")
        else:
            template_values = {"user":None,
                               "loginurl":users.create_login_url(self.request.uri)}
            template = jinja_environment.get_template('welcome.html')
            self.response.out.write(template.render(template_values))
        
class UserPage(webapp.RequestHandler):
    """shows a user's homepage where they can continue games and start new ones"""
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/")
            return None
        pl=getPlayer(user.nickname())
        if pl==None:#create a new user
            pl=PlayerData(key_name=str(hash(user.nickname())))
            pl.account=user
            pl.score=1000
            pl.token=channel.create_channel(user.nickname())
            pl.username="usert"
        pl.lastonline=datetime.now()
        pl.online=True
        pl.put()
        players=db.GqlQuery("SELECT * "
                        "FROM PlayerData "
                        "WHERE online = TRUE "
                        "ORDER BY lastOnline DESC LIMIT 10")
        players=[{"id":hash(p.account.nickname()),"name":p.username,"score":p.score} for p in players]
        
        gamesX=db.GqlQuery("SELECT playerO, turn FROM GameData WHERE playerX = :1",pl.account)
                        
        games=[{"id":game.key().id_or_name(),
                "O":playerName(game.playerO.nickname(),game.turn=="O"),
                "X":playerName(pl.account.nickname(),game.turn=="X")}
               for game in gamesX]
            
        gamesO=db.GqlQuery("SELECT playerX, turn FROM GameData WHERE playerO = :1",pl.account)
       
        games+=[{"id":game.key().id_or_name(),
                "O":playerName(pl.account.nickname(),game.turn=="O"),
                "X":playerName(game.playerX.nickname(),game.turn=="X")}
               for game in gamesO]
        
        template_values = {"name":pl.username,
                           "score":pl.score,
                           "logouturl":users.create_logout_url(self.request.uri),
                           "chtoken":pl.token,
                           "players":players,
                           "games":games}
        template = jinja_environment.get_template('user.html')
        self.response.out.write(template.render(template_values))

class ChangeName(webapp.RequestHandler):
    """changes a user's name"""
    @db.transactional
    def post(self):
        pl=getCurrentPlayer()
        if not pl: return None
        newName=self.request.get("name")
        if len(newName)>20:
            return None
        pl.username=self.request.get("name")
        pl.put()

class ChannelCreator(webapp.RequestHandler):
    """creates a new token when the old one runs out - susceptible to abuse"""
    @db.transactional
    def post(self):
        pl=getCurrentPlayer()
        if not pl: return None
        pl.token=channel.create_channel(pl.account.nickname())
        pl.put()
        self.response.out.write(pl.token)



class NewGame(webapp.RequestHandler):
    """handles a request by one player to start a game with another"""
    
    def get(self):
        """returns a page where the user can select options for the game they want to start"""
        pl=getCurrentPlayer()
        if not pl:
            self.redirect("/")
            return None
        opponent=self.request.get("player")
        op=PlayerData.get(db.Key.from_path('PlayerData',opponent))
        if not op:
            self.redirect("/user?opponentnotfound=true")
            return None
        if not op.online:
            self.redirect("/user?opponentnotonline=true")
            return None
        template_values = {"name":pl.username,
                           "chtoken":pl.token,
                           "opponent":{"name":op.username,
                                       "id":hash(op.account.nickname()),
                                       "score":op.score}
                           }
        template = jinja_environment.get_template('offer.html')
        self.response.out.write(template.render(template_values))
        
        
    @db.transactional(xg=True)
    def post(self):
        """notifies the other player to see if they want to start the game (and to check if they are online)"""
        pl=getCurrentPlayer()
        if not pl:
            return None
        opponent=self.request.get("opponent")
        #check the opponent
        op=PlayerData.get(db.Key.from_path('PlayerData',opponent))
        if (not op) or not op.online:
            self.response.out.write("not online")
            return None
        
        #create the game Entity
        time=int(self.request.get("time"))
        assert time in range(6)
        times=[60,120,300,600,24*3600,7*24*3600]
        seconds=times[time]
        gm=True
        while gm:
            gmNum=str(randrange(100000000))
            gm=GameData.get(game_key(gmNum))
        gm=GameData(key_name=gmNum)
        gm.turn="X"
        gm.board=" "*64
        gm.winpos=""
        gm.started=False
        gm.playerO=pl.account
        gm.playerX=op.account
        gm.timeLimit=seconds
        gm.put()
        
        #tell the opponent
        op.online=False
        op.put()
        message={"request":"NewGame",
                 "player":pl.username+" ("+str(pl.score)+")",
                 "time":time,
                 "gameID":gmNum}
        channel.send_message(op.account.nickname(),simplejson.dumps(message))
        self.response.out.write(gmNum)
        
        
class Response(webapp.RequestHandler):
    """handles the response to a game request"""
    
    @db.transactional(xg=True)#check if xg necessary
    def post(self):
        pl=getCurrentPlayer()
        if not pl:return None
        gmNum=self.request.get("gameID")
        gm=GameData.get(game_key(gmNum))
        if not gm or gm.started:
            self.response.out.write("no")
            return None
        check(pl.account,gm.playerX,"player replying to a game which they are not part of")
        answer=self.request.get("answer")
        message={"request":"reply","answer":answer}
        if answer=="yes":
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
            gm.started=True
            gm.lastTurn=datetime.now()
            gm.put()
        if answer=="no":
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
            db.delete(gm)
    
    def get(self):
        """for players checking the opponent is online"""
        gmNum=self.request.get("gameID")
        gm=GameData.get(game_key(gmNum))
        if not gm:
            self.response.out.write("no")
            return None
        opName=gm.playerX.nickname()
        op=getPlayer(opName)
        if not op or not op.online:
            self.response.out.write("no")
        else:
            self.response.out.write("yes")
        

class GamePage(webapp.RequestHandler):
    def get(self):
        """ Shows a page on which a game can be played"""
        #make sure that the user is logged in
        pl = getCurrentPlayer()
        if not pl:
            self.redirect("/")
            return None
        gmNum=self.request.get('gameID')
        gameID = game_key(gmNum)
        gm=GameData.get(gameID)
        if not gm:
            self.redirect("/")
            return None
        
        #show the page
        template_values = {"gameID":gmNum,
                           "board":gm.board,
                           "chtoken":pl.token}
        pageType=self.request.get('pageType')
        file=""
        if pageType=="" or pageType=="table":
            file='tablegame.html'
        #if pageType=="canvas":
        #    file='canvasgame.html'
        #if pageType=="threeD":
        #    file='3Dgame.html'
        if file: self.response.out.write(jinja_environment.get_template(file).render(template_values))
    
    @db.transactional(xg=True)
    def post(self):
        
        pl = getCurrentPlayer()
        if not pl:
            return None
        gmNum=self.request.get('gameID')
        gameID = game_key(gmNum)
        gm=GameData.get(gameID)
        if not gm:
            return None
        game=Game(gm)
            
        pos = self.request.get('pos')
        if not pos:
            self.response.out.write("error")
            return None
        x,y,z=(int(c) for c in pos)
        pos=16*z+4*y+x
        try: game.go(pl,x,y,z)
        except InvalidInput as e:
            self.response.out.write(e.msg)
            return None
        game.sync(gm)
        gm.put()
        for player in [gm.playerX,gm.playerO]:
            channel.send_message(player.nickname(),simplejson.dumps(game.getData()))
        self.response.out.write("none")


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
        self.players={"O":gmData.playerO,"X":gmData.playerX}
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
        d={"request":"gameUpdate"}
        d["board"]="".join(["".join(["".join(y) for y in z]) for z in self.board])
        d["wonlines"]=self.wonlines
        return d
        
    def go(self,player,x,y,z):
        check(self.winpos,"","game's over")
        check(player.account,self.players[self.turn],"it is not your turn")
        check(self.board[z][y][x]," ","you must go in an empty cell")
        self.board[z][y][x]=self.turn
        for line in self.linesThrough(x,y,z):
            if all([p==self.turn for p in line[0]]):
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
        

class ClearGames(webapp.RequestHandler):
    """clear all game data"""
    def post(self):
        games=db.GqlQuery("SELECT __key__ "
                        "FROM GameData "
                        "WHERE started = False ")
        db.delete(games)
        games=db.GqlQuery("SELECT __key__ "
                        "FROM GameData "
                        "WHERE winpos > '' ")
        db.delete(games)

class Clear(webapp.RequestHandler):
    """clear all game data"""
    def get(self):
        db.delete(PlayerData.all(keys_only=True).run())

        
app = webapp.WSGIApplication([
    ('/', WelcomePage),
    ('/user', UserPage),
    ('/changeName', ChangeName),
    ('/newChannel', ChannelCreator),
    ('/newGame', NewGame),
    ('/respond', Response),
    ('/checkRequest', Response),
    ('/game', GamePage),
    ('/makeMove', GamePage),
    ('/clr', ClearGames),
    #('/clrall', Clear),
     ], debug=True)
        