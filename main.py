# !/usr/bin/env python

from tools import *
from game import Game
from players import Player,getCurrentPlayer,getPlayer,getCurrentUser
from ox3.ox3 import ox3
from ensquared.ensquared import ensquared

#{path:object}
GAMES={"ox3":ox3,
       "ensquared":ensquared}

rgames={g:"" for g in GAMES}#I'm sorry, a non-constant global variable :(

import os
import datetime
from time import clock
from datetime import datetime,timedelta
from random import randrange

import webapp2 as webapp
from google.appengine.ext import db
from google.appengine.api import channel,users
from google.appengine.api.users import User,get_current_user


from django.utils import simplejson
import jinja2


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.dirname(__file__),os.path.join(os.path.dirname(__file__),"OX")]),
    trim_blocks=True)

def load(s,page,values):
    return s.response.out.write(jinja_environment.get_template(page).render(values))


# Webpages

class Games(webapp.RequestHandler):
    """Shows a page where a user can look at the games they're playing and start new ones.
    They do not have to be logged in."""
    def get(self):
        pl = self.request.get("playerID") or randstr()
        tvals={"path":[("/","games")],
            "game_list":list((GAME.path,GAME.name,list((n,ai.name) for n,ai in enumerate(GAME.ais))) for GAME in GAMES.values() if GAME),
            "playerid":pl
        }
        tvals["links"]=[("/about","about")]
        
        load(self,'games.html',tvals)
        



# class ChannelCreator(webapp.RequestHandler):
    # """creates a new token when the old one runs out - susceptible to abuse"""
    # @db.transactional
    # def post(self):
        # pl=getCurrentPlayer(put=False)
        # if not pl: return None
        # pl.token=channel.create_channel(pl.account.nickname())
        # pl.put()
        # self.response.out.write(pl.token)

class Base(webapp.RequestHandler):
    """a handler for the page "/gpath/" """
    def get(self,gpath):
        self.redirect("setup")


##
class AboutPage(webapp.RequestHandler):
    """a page for the description of a game"""
    def get(self,gpath):
        GAME=GAMES[gpath]
        load(self,GAME.about,{"path":[("games","/"),(GAME.name,"./"),("about","about")]})
        

class NewGamePage(webapp.RequestHandler):
    """shows a page where the user can select options for the game they want to start"""
    def get(self,gpath):
        GAME=GAMES[gpath]
        pl=getCurrentPlayer()
        tvals={}
        opps = [{"id":p.key().name(),
                 "name":p.playername,
                 "score":p.score
                }for p in players]
        opps+= [{"id":"a "+str(n),
                 "name":ai.name,
                 "score":ai.score
                 }for n,ai in enumerate(GAME.ais)]
        opps+= [{"id":"y",
                 "name":"someone else",
                 "score":"NA"
                }]
        tvals.update({"game":GAME.name,
                      "opponents":opps,
                      "path":[("/","all games"),
                              ("/"+gpath+"/",GAME.name)],
                      "links":[("about","about "+GAME.name)]})
        load(self,"newGame.html",tvals)

##needs work if one player is logged in
class NewGame(webapp.RequestHandler):
    """Handles a request to start a game:
    creates the Game object, and performs other actions depending on opponent type"""
    @db.transactional(xg=True)
    def post(self,gpath):
        GAME=GAMES[gpath]
        pl = self.request.get("playerID") or randstr()
        usr=User("p "+pl)
        kname=randstr()
        
        turn=self.request.get("turn") or "true"
        time=self.request.get("time") or 600
        state=0
        
        
        opponent=self.request.get("opp")
        if opponent=="r" and rgames[gpath]:
            kname=rgames[gpath]
            rgames[gpath]=""
            gm=GAME.get_by_key_name(kname)
            gm.player1=usr
            gm.state|=STARTED
            gm.put()
            self.response.out.write(gm.url(1))
            return None
        else:
            gm=GAME(player0=usr,
                    timeLimit=time,
                    state=0,
                    key_name=kname)
            if opponent=="r":
                    gm.player1=User("x ")
                    rgames[gpath]=kname
                    redirectUrl="/"+gpath+"/wait?gameID="+kname+"&playerID="+pl
            elif opponent=="y":
                #newgame, url, stuff
                gm.player1=User("x ")
                redirectUrl="/"+gpath+"/wait?gameID="+kname+"&playerID="+pl
            elif opponent.startswith("a"):
                diff=int(opponent[1:])
                assert diff in range(len(GAME.ais))
                gm.timeLimit=diff
                gm.player1=User("a "+str(diff))
                gm.state=AIP|STARTED
                redirectUrl=gm.url()
            else: raise HttpError(400)
            
            if turn=="false": gm.endmove()#updates state and plays for the AI
        gm.put()
        self.response.out.write(redirectUrl)


class StartGame(webapp.RequestHandler):
    """starts a game between the player who created the url and the player accessing this page
    basically just does a post request so that Facebook won't trigger it"""
    def get(self,gpath):
        GAME=GAMES[gpath]
        pl=getCurrentPlayer()
        gmNum=self.request.get("gameID")
        load(self,"startGame.html",{"gameID":gmNum})

class StartGamePost(webapp.RequestHandler):
    """starts a game between the player who created the url and the player accessing this page"""
    def post(self,gpath):
        GAME=GAMES[gpath]
        pl=getCurrentPlayer()
        gmNum=self.request.get("gameID")
        gm=GAME.get_by_key_name(gmNum)
        assert gm.player1.email()=="x "
        assert not pl
        pNum=randstr()
        gm.player1=User("p "+pNum)
        self.response.out.write("play?gameID="+gmNum+"&playerID="+pNum)
        gm.state|=STARTED
        gm.lastTurn=datetime.now()
        gm.put()
        



class Response(webapp.RequestHandler):
    """handles the response to a game request"""
    @db.transactional(xg=True)
    def post(self,gpath):
        pl=getCurrentPlayer()
        if not pl:return None
        GAME=GAMES[gpath]
        kname=self.request.get("gameID")
        gm=GAME.get_by_key_name(kname)
        if not gm or gm.state&STARTED:
            self.response.out.write("no")
            return None
        check(pl.account,gm.player1,"player replying to a game which they are not part of")
        answer=self.request.get("answer")
        assert answer in ["yes","no"]
        message={"request":"reply","answer":answer}
        p0=getPlayer(gm.player0)
        if p0: p0.send(message)
        if answer=="yes":
            gm.state|=STARTED
            gm.lastTurn=datetime.now()
            gm.put()
        if answer=="no":
            db.delete(gm)

class WaitPage(webapp.RequestHandler):
    """used when waiting for another player to respond to a game"""
    
    def get(self,gpath):
        GAME=GAMES[gpath]
        pl=getCurrentPlayer()
        if pl: tvals={"chtoken":pl.token}
        else: tvals={"playerID":self.request.get("playerID")}
        kname=self.request.get("gameID")
        gm=GAME.get_by_key_name(kname)
        tvals.update({"game":GAME.name,
                      "gameID":kname,
                      "path":[("/","all games"),
                               ("/"+gpath+"/",GAME.name)]})
        
        if gm.player1.email().startswith("x "):
            tvals["url"]="%s/%s/startgame?gameID=%s"%(self.request.host,gpath,kname)
        load(self,"wait.html",tvals)
    

## now used more for polling
class CheckRequest(webapp.RequestHandler): 
    """tells a player if the opponent is online, also polls to check if the game has started"""
    def get(self,gpath):
        gmNum=self.request.get("gameID")
        gm=Game.get_by_key_name(gmNum)
        
        if not gm:
            self.response.out.write("no")
            return None
        pl = getCurrentUser(self.request.get("playerID"))
        check(pl,gm.player0,"information restricted")
        message={"gameID":gmNum}
        if gm.state&STARTED:
            message.update({"request":"goto","target":gm.url(0)})
        elif  gm.timeCreated<datetime.now()-timedelta(seconds=OFFLINE):
            self.response.out.write("no")
            db.delete(gm)
        else: message.update({"request":"wait"})
        self.response.out.write(sjd(message))    




class PlayPage(webapp.RequestHandler):
    def get(self,gpath):
        """Shows a page on which a game can be played"""
        pl = getCurrentPlayer()
        GAME=GAMES[gpath]
        gmNum=self.request.get('gameID')
        gm=GAME.get_by_key_name(gmNum)
        if not gm:
            self.redirect("/")
            return None
        if not gm.state&STARTED:
            logging.error("accessing a game which has not started")
            crash
        
        if pl:
            tvals = {"player":pl.playername,
                     "chtoken":pl.token}
            if gm.player0==pl.account:   playern=0;opp=gm.player1
            elif gm.player1==pl.account: playern=1;opp=gm.player0
            else:return None
        else:
            pnum=self.request.get("playerID")
            if gm.player0.email()=="p "+pnum: playern=0;opp=gm.player1
            elif gm.player1.email()=="p "+pnum: playern=1;opp=gm.player0
            else:return None
            tvals = {"player":"You","playerID":pnum}
            
        if opp.email().startswith("p "): tvals["opponent"]="Opponent"
        elif gm.state&AIP: tvals["opponent"]="AI"
        else: tvals["opponent"]=getPlayer(opp).playername
        
        tvals["playern"]=playern
        tvals["player0"]=tvals["opponent"] if playern else tvals["player"]
        tvals["player1"]=tvals["player"] if playern else tvals["opponent"]
        
        pagetype=self.request.get("pageType")
        if not pagetype:pagetype=gm.views[0]
        tvals["gameID"]=gmNum
        tvals["data"]=sjd(gm.getData())
        tvals["path"]=[("/","all games"),
                       ("",pagetype+" view")]
        tvals["links"]=[("?pageType="+ptype+"&gameID="+gmNum+
                         ("" if pl else "&playerID="+pnum),
                         ptype+" view")
                       for ptype in gm.views if ptype!=pagetype]
        
        load(self,"/%s/%s.html"%(gpath,pagetype),tvals)


## in progress
class MakeMove (webapp.RequestHandler):
    """handles a request to make a move"""
    @errordec
    @db.transactional(xg=True)
    def post(self,gpath):
        pl = getCurrentUser(self.request.get("playerID"))
        gmNum=self.request.get('gameID')
        gm=GAMES[gpath].get_by_key_name(gmNum)
        if not gm:
            self.response.out.write("error, game not found")
            return None
        if not gm.state&STARTED:crash
        try:
            gm.move(pl,self.request.get('pos'))
        except InvalidInput as e:
            self.response.out.write(e.msg)
            return None
        
        dat=sjd(gm.getData())
        gm.tellPlayers(dat)
        self.response.out.write(dat)


class GetGame (webapp.RequestHandler):
    @db.transactional(xg=True)
    def get(self,gpath):
        """deals with a user polling for a game, checks the time limit"""
        gmNum=self.request.get('gameID')
        gm=GAMES[gpath].get_by_key_name(gmNum)
        if not gm:
            return None
        if gm.state&AIP==0: gm.checkTime()
        self.response.out.write(sjd(gm.getData()))

## disabled
class SendMessage(webapp.RequestHandler):
    """lets a user send a message to another user"""
    @db.transactional(xg=True)
    def post(self,gpath):
        return None ####
        pl = getCurrentPlayer()
        if not pl: return None
        gmNum=self.request.get('gameID')
        gameID = game_key(gmNum)
        gm=GameData.get(gameID)
        if not gm: return None
        
        players=[gm.playerX, gm.playerO]
        if pl.account not in players: return None
        content=self.request.get('msg')
        if not content:return None
        
        m=Message(parent=gm)
        m.sender=pl.account
        m.content=content
        m.put()
        
        chmessage={"request":"message",
                   "content":"\n<b>"+pl.username+"</b>: "+content,
                   "gameID":gm.key().name()}
        for player in players:
            channel.send_message(player.nickname(),sjd(chmessage))
        

class ClearGames(webapp.RequestHandler):
    """clear all game data"""
    def get(self):
        games=db.GqlQuery("SELECT __key__ "
                        "FROM Game "
                        "WHERE state >= "+str(GAMEOVER))
        db.delete(games)





#page,handler

gamepages=[("",Base),
           ("setup",NewGamePage),
           ("startgame",StartGame),
           ("startgamepost",StartGamePost),
           ('new', NewGame),
           ("play",PlayPage),
           #("highscores",HighScores),
           ("about",AboutPage),
           ("wait",WaitPage)]

#path,title
Pages=[("/", "Games")] + [
    ("/"+ob.path+"/"+page,ob.name+" - "+page, [])
    for ob in GAMES.values() if ob
    for page,handler in gamepages]

gameserv=[
    ('respond', Response),
    ('checkrequest', CheckRequest),
    ('makemove', MakeMove),
    ('getgame', GetGame),
    ('msg', SendMessage)]

services=[
    #('/changename', ChangeName),
    #('/newchannel', ChannelCreator),
    ('/clr', ClearGames)]

allpages= [("/",Games)] + services + [
    ("/(.+)/"+page, handler)
    for page,handler in gamepages+gameserv]

##print(allpages)
    
app = webapp.WSGIApplication(allpages, debug=True)
        
