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


#@db.transactional
#def win(game,winner,timeup=False):
    #"""informs players that the game is over and updates their scores"""
    #pls={"X":getPlayer(game.playerX.nickname()),
         #"O":getPlayer(game.playerO.nickname())}
    #msg={"request":"gameover", "won":True,
         #"reason":"timeup" if timeup else "line",
         #"gameID":game.key().name()}
    #if game.turn=="ai":
        #msg["won"]=(winner=="ai")
        #channel.send_message(pls["O"].account.nickname(),sjd(msg))
        #return None
    #loser=other[winner]
    #dScore=int(pls[loser].score/10)
    #pls[winner].score+=dScore
    #pls[loser].score-=dScore
    #channel.send_message(pls[winner].send(msg))
    #msg["won"]=False
    #channel.send_message(pls[loser].account.nickname(),sjd(msg))
    #for pl in pls:pls[pl].put()

##webpages

#class ChannelCreator():
    #"""creates a new token when the old one runs out - susceptible to abuse"""
    #@db.transactional
    #def post(self):
        #pl=getCurrentPlayer()
        #if not pl: return None
        #pl.token=channel.create_channel(pl.account.nickname())
        #pl.put()
        #self.response.out.write(pl.token)



#class NewGame():
    #"""handles a request by one player to start a game with another"""
    
    #def get(self):
        #"""shows a page where the user can select options for the game they want to start"""
        #pl=getCurrentPlayer()
        #if not pl:
            #self.redirect("/")
            #return None
        #opponent=self.request.get("player")
        #op=PlayerData.get(db.Key.from_path('PlayerData',opponent))
        #if not op:
            #self.redirect("/user?opponentnotfound=true")
            #return None
        #if not op.online:
            #self.redirect("/user?opponentnotonline=true")
            #return None
        #template_values = {"name":pl.username,
                           #"chtoken":pl.token,
                           #"opponent":{"name":op.username,
                                       #"id":hash(op.account.nickname()),
                                       #"score":op.score}
                           #}
        #template = jinja_environment.get_template('offer.html')
        #self.response.out.write(template.render(template_values))
        
        
    #@db.transactional(xg=True)
    #def post(self):
        #"""notifies the other player to see if they want to start the game (and to check if they are online)"""
        #pl=getCurrentPlayer()
        #if not pl:
            #return None
        #opponent=self.request.get("opponent")
        ##check the opponent
        #op=PlayerData.get(db.Key.from_path('PlayerData',opponent))
        #if (not op) or not op.online:
            #self.response.out.write("not online")
            #return None
        
        ##create the game Entity
        #time=int(self.request.get("time"))
        #assert time in range(6)
        #times=[60,120,300,600,24*3600,7*24*3600]
        #seconds=times[time]
        #gm=True
        #while gm:
            #gmNum=str(randrange(100000000))
            #gm=GameData.get(game_key(gmNum))
        #gm=GameData(key_name=gmNum)
        #gm.turn="X"
        #gm.board=" "*64
        #gm.winpos=""
        #gm.started=False
        #gm.playerO=pl.account
        #gm.playerX=op.account
        #gm.timeLimit=seconds
        #gm.put()
        
        ##tell the opponent
        #op.online=False
        #op.put()
        #message={"request":"NewGame",
                 #"player":pl.username+" ("+str(pl.score)+")",
                 #"time":time,
                 #"gameID":gmNum}
        #channel.send_message(op.account.nickname(),simplejson.dumps(message))
        #self.response.out.write(gmNum)
        

#class AIGame():
    #"""handles a request to start a game with the AI"""
    
    #def get(self):
        #"""returns a page where the user can select options for the game they want to start"""
        #pl=getCurrentPlayer()
        #if not pl:
            #self.redirect("/")
            #return None
        #template_values = {"chtoken":pl.token}
        #template = jinja_environment.get_template('aioffer.html')
        #self.response.out.write(template.render(template_values))
        
        
    #@db.transactional(xg=True)
    #def post(self):
        #"""starts a game against the AI"""
        #pl=getCurrentPlayer()
        #if not pl:
            #return None
        ##create the game Entity
        #difficulty=int(self.request.get("difficulty"))
        #assert difficulty in range(3)
        #gm=True
        #while gm:
            #gmNum=str(randrange(100000000))
            #gm=GameData.get(game_key(gmNum))
        #gm=GameData(key_name=gmNum)
        #gm.turn="ai"
        #gm.board=" "*64
        #gm.winpos=""
        #gm.started=True
        #gm.playerO=pl.account
        #gm.playerX=pl.account#saves trouble but may cause problems
        #gm.timeLimit=difficulty
        #gm.put()
        #self.response.out.write(gmNum)
        
        
#class Response():
    #"""handles the response to a game request"""
    
    #@db.transactional(xg=True)
    #def post(self):
        #pl=getCurrentPlayer()
        #if not pl:return None
        #gmNum=self.request.get("gameID")
        #gm=GameData.get(game_key(gmNum))
        #if not gm or gm.started:
            #self.response.out.write("no")
            #return None
        #check(pl.account,gm.playerX,"player replying to a game which they are not part of")
        #answer=self.request.get("answer")
        #message={"request":"reply","answer":answer}
        #if answer=="yes":
            #gm.started=True
            #gm.lastTurn=datetime.now()
            #gm.put()
            #channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
        #if answer=="no":
            #channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
            #db.delete(gm)

#class CheckRequest(): 
    #"""tells a player if the opponent is online"""
    #def get(self):
        #gmNum=self.request.get("gameID")
        #gm=GameData.get(game_key(gmNum))
        #if not gm:
            #self.response.out.write("no")
            #return None
        #opName=gm.playerX.nickname()
        #op=getPlayer(opName)
        #if not op or not op.online:
            #self.response.out.write("no")
            #db.delete(gm)
        #else:
            #self.response.out.write("yes")
        

#class GamePage():
    #def get(self):
        #"""Shows a page on which a game can be played"""
        ##make sure that the user is logged in
        #pl = getCurrentPlayer()
        #if not pl:
            #self.redirect("/")
            #return None
        #gmNum=self.request.get('gameID')
        #gameID = game_key(gmNum)
        #gm=GameData.get(gameID)
        #if not gm:
            #self.redirect("/")
            #return None
        #if not gm.started:
            #self.redirect("/user")
            #return None
        #if gm.turn=="ai":
            #template_values = {"gameID":gmNum,
                               #"board":gm.board,
                               #"chtoken":pl.token,
                               #"data":sjd(Game(gm).getData()),
                               #"player":getPlayer(gm.playerO.nickname()).username,
                               #"opponent":"AI"}
        #else:
            #if not gm.winpos:
                #checkTime(gm)
            #players=[getPlayer(gm.playerX.nickname()),
                     #getPlayer(gm.playerO.nickname())]
            #pln=int(players[1]==pl)
            
            ##show the page
            #template_values = {"gameID":gmNum,
                               #"board":gm.board,
                               #"chtoken":pl.token,
                               #"data":sjd(Game(gm).getData()),
                               #"player":players[pln].username,
                               #"opponent":players[1-pln].username}
        #pageType=self.request.get('pageType')
        #file=""
        #if pageType=="" or pageType=="table":
            #file='tablegame.html'
        #if pageType=="canvas":
            #file='canvasgame.html'
        #if pageType=="threeD":
            #file='3Dgame.html'
        #if file: self.response.out.write(jinja_environment.get_template(file).render(template_values))
    
#class MakeMove ():
    #"""handles a request to make a move"""
    #@db.transactional(xg=True)
    #def post(self):
        #pl = getCurrentPlayer()
        #if not pl:
            #return None
        #gmNum=self.request.get('gameID')
        #gameID = game_key(gmNum)
        #gm=GameData.get(gameID)
        #if not gm:
            #return None
        #if gm.winpos or not checkTime(gm):
            #self.response.out.write("game's over")
            #return None
        
        #pos = self.request.get('pos')
        #if not pos:
            #self.response.out.write("error")
            #return None
        #x,y,z=(int(c) for c in pos)
        #game=Game(gm)
        #try: game.go(pl,x,y,z)
        #except InvalidInput as e:
            #self.response.out.write(e.msg)
            #return None
        #game.sync(gm)
        #gm.lastTurn=datetime.now()
        #if gm.winpos: win(gm,game.turn)
        #if gm.turn=="ai" and not gm.winpos:
            #game.aiMove(gm.timeLimit)
            #if gm.winpos: win(gm,"AI")
            #game.sync(gm)
        #gm.put()
        #for player in [gm.playerX,gm.playerO]:
            #channel.send_message(player.nickname(),sjd(game.getData()))
        #self.response.out.write("none")
    
#class GetGame ():
    #@db.transactional(xg=True)
    #def get(self):
        #"""deals with a user polling for a game, checks the time limit"""
        #gmNum=self.request.get('gameID')
        #gameID = game_key(gmNum)
        #gm=GameData.get(gameID)
        #if not gm:
            #return None
        #if gm.turn!="ai":checkTime(gm)
        #self.response.out.write(sjd(Game(gm).getData()))
    
#class SendMessage():
    #"""lets a user send a message to another user"""
    #@db.transactional(xg=True)
    #def post(self):
        #pl = getCurrentPlayer()
        #if not pl: return None
        #gmNum=self.request.get('gameID')
        #gameID = game_key(gmNum)
        #gm=GameData.get(gameID)
        #if not gm: return None
        
        #players=[gm.playerX, gm.playerO]
        #if pl.account not in players: return None
        #content=self.request.get('msg')
        #if not content:return None
        
        #m=Message(parent=gm)
        #m.sender=pl.account
        #m.content=content
        #m.put()
        
        #chmessage={"request":"message",
                   #"content":"\n<b>"+pl.username+"</b>: "+content,
                   #"gameID":gm.key().name()}
        #for player in players:
            #channel.send_message(player.nickname(),sjd(chmessage))
        

##class Clear(webapp.RequestHandler):
##    """clear all game data"""
##    def get(self):
##        db.delete(PlayerData.all(keys_only=True).run())

        
