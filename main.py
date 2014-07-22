# !/usr/bin/env python

from tools import *
from game import Game
from players import Player,getCurrentPlayer,getPlayer
from ox3.ox3 import ox3

#(path,name,object)
GAMES={"ox3":ox3,
       "ensquared":None}



import os
import datetime
from time import clock
from datetime import datetime,timedelta
from random import randrange

import webapp2 as webapp
from google.appengine.ext import db
from google.appengine.api import channel,users
from google.appengine.api.users import User


from django.utils import simplejson
import jinja2


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.dirname(__file__),os.path.join(os.path.dirname(__file__),"OX")]),
    trim_blocks=True)

def load(s,page,values):
    return s.response.out.write(jinja_environment.get_template(page).render(values))


#webpages
class Games(webapp.RequestHandler):
    """Shows a page where a user can look at the games they're playing and start new ones.
    They do not have to be logged in."""
    def get(self):
        pl = getCurrentPlayer()
        if pl:
            
            ##to be changed
            games0=db.GqlQuery("SELECT player1, state "
                               "FROM Game "
                               "WHERE player0 = :1 AND state>3",
                               pl.account)
            games=[{"id":game.key().id_or_name(),
                    0:playerName(pl.account.nickname(),game.state&1),
                    1:"AI" if game.state&2 else getPlayer(game.player1).getName(not game.state&1)}
                    for game in games0]
            games1=db.GqlQuery("SELECT player0, state "
                               "FROM Game "
                               "WHERE player1 = :1 AND state>3",
                               pl.account)
            games+=[{"id":game.key().id_or_name(),
                    0:"AI" if game.state&2 else getPlayer(game.player0).getName(game.state&1),
                    1:playerName(pl.account.nickname(),not game.state&1)}
                    for game in games1 if game.player1!=pl.account]
            
            players=db.GqlQuery("SELECT score,playername "
            "FROM Player "
            "WHERE lastOnline > :1 "
            "ORDER BY lastOnline DESC LIMIT 10",
            datetime.now()-timedelta(seconds=120))
            
            tvals = {"name":pl.playername,
                     "score":pl.score,
                     "chtoken":pl.token,
                     "games":games,
                     "players":players}
        else:
            tvals={"loginurl":users.create_login_url(self.request.uri)}
        tvals.update({"path":[("Homepage","/"),
                              ("games","/games")],
        "game_list":list((ob.path,ob.name) for ob in GAMES.values() if ob)})
        tvals["links"]=[("logout",users.create_logout_url(self.request.uri))]
        print(tvals["links"])
        load(self,'games.html',tvals)
        
##
class HighScores(webapp.RequestHandler):
    """shows a list of highscores"""
    def get(self):
        pl = getCurrentPlayer()
        if pl:
            tvals={"player":{"name":pl.username,
                             "id":pl.account.nickname(),
                             "score":pl.score},
                   "logouturl":users.create_logout_url(self.request.uri),
                   "chtoken":pl.token}
        else:
            tvals={"player":None,"loginurl":users.create_login_url(self.request.uri)}
        
        players=db.GqlQuery("SELECT username,score,account "
                            "FROM PlayerData "
                            "ORDER BY score DESC LIMIT 10")
        tvals["players"]=[{"name":p.username,
            "score":p.score,
            "id":p.account.nickname()} for p in players]
        template = jinja_environment.get_template('highscore.html')
        self.response.out.write(template.render(tvals))

class ChangeName(webapp.RequestHandler):
    """changes a user's name"""
    @db.transactional
    def post(self):
        pl=getCurrentPlayer(put=False)
        if not pl: return None
        pl.changeName(self.request.get("name"),put=False)
        pl.put()

##
class ChannelCreator(webapp.RequestHandler):
    """creates a new token when the old one runs out - susceptible to abuse"""
    @db.transactional
    def post(self):
        pl=getCurrentPlayer(put=False)
        if not pl: return None
        pl.token=channel.create_channel(pl.account.nickname())
        pl.put()
        self.response.out.write(pl.token)

class Base(webapp.RequestHandler):
    """a handler for the page "/gpath/" """
    def get(self,gname):
        self.redirect("setup")

class NewGamePage(webapp.RequestHandler):
    """handles a request by one player to start a game"""
    
    def get(self,gname):
        """shows a page where the user can select options for the game they want to start"""
        pl=getCurrentPlayer()
        if pl:
            tvals = {"name":pl.playername,
                     "chtoken":pl.token}
        else:tvals={}
        players=db.GqlQuery("SELECT * "
                            "FROM Player "
                            "WHERE lastOnline > :1 "
                            "ORDER BY lastOnline DESC LIMIT 10",
                            datetime.now()-timedelta(seconds=120))
        opps = [{"id":p.key().name(),
                 "name":p.playername,
                 "score":p.score
                }for p in players]
        opps+= [{"id":"ai"+str(n),
                 "name":ai.name,
                 "score":ai.score
                 }for n,ai in enumerate(GAMES[gname].ais)]
        opps+= [{"id":"y",
                 "name":"someone else",
                 "score":"NA"
                }]
        tvals.update({"game":gname,
                      "opponents":opps,
                      "path":[("Homepage","/"),
                              ("games","/games"),
                              (gname,"/"+gname+"/")]})
        load(self,"newGame.html",tvals)
        
class NewGame(webapp.RequestHandler):
    @db.transactional(xg=True)
    def post(self,gname):
        """creates the Game object and checks opponent is online"""
        pl=getCurrentPlayer()
        if pl:
            usr=pl.account
            tvals = {"name":pl.playername,
                     "chtoken":pl.token}
        else:
            usr=User("p "+randstr())
            tvals = {"plnum":usr.email()[2:]}
        opponent=self.request.get("opponent")
        
        if opponent=="y":
            #newgame, url, stuff
            msg="""
Give this URL to your opponent.
When they visit that page,
you will both be sent to pages
where you can play each other"""
            
            gm=GAMES[gname](player0=usr,player1=User("a AI"),
                                   timeLimit=diff,state=STARTED,
                                   key_name=randstr())
            
            
        if opponent.startswith("ai"):
            diff=int(opponent[2:])
            gm=GAMES[gname](player0=usr,player1=User("a AI"),
                                   timeLimit=diff,state=AIP|STARTED,
                                   key_name=randstr())
            gm.put()
            self.response.out.write("goto:"+gm.url())
        else:
            #needs more work
            op=PlayerData.get(db.Key.from_path('Player',opponent))
            if (not op):
                self.response.out.write("error: opponent not found")
                return None
            #

##
class AboutPage(webapp.RequestHandler):
    """handles a request by one player to start a game"""
    
    def get(self,gname):
        """shows a page where the user can select options for the game they want to start"""
        pl=getCurrentPlayer()


##
class Response(webapp.RequestHandler):
    """handles the response to a game request"""
    
    @db.transactional(xg=True)
    def post(self,gname):
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
            gm.started=True
            gm.lastTurn=datetime.now()
            gm.put()
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
        if answer=="no":
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
            db.delete(gm)

##
class CheckRequest(webapp.RequestHandler): 
    """tells a player if the opponent is online"""
    def get(self):
        gmNum=self.request.get("gameID")
        gm=GameData.get(game_key(gmNum))
        if not gm:
            self.response.out.write("no")
            return None
        opName=gm.playerX.nickname()
        op=getPlayer(opName)
        if not op or not op.online:
            self.response.out.write("no")
            db.delete(gm)
        else:
            self.response.out.write("yes")
        
##tentatively working
class PlayPage(webapp.RequestHandler):
    def get(self,gname):
        """Shows a page on which a game can be played"""
        pl = getCurrentPlayer()
        gmNum=self.request.get('gameID')
        gm=GAMES[gname].get_by_key_name(gmNum)
        if not gm:
            self.redirect("/")
            return None
        if not gm.state&STARTED:crash
        
        if pl:
            tvals = {"player":pl.playername,
                     "chtoken":pl.token}
            if gm.player0==pl.account:   opp=gm.player1
            elif gm.player1==pl.account: opp=gm.player0
            else:return None
        else:
            pnum=self.request.get("player")
            if gm.player0.email()=="p "+pnum: opp=gm.player1
            elif gm.player1.email()=="p "+pnum: opp=gm.player0
            else:return None
            tvals = {"player":"you","playerID":pnum}
            
        if opp.email().startswith("p "): tvals["opponent"]="opponent"
        elif gm.state&AIP: tvals["opponent"]="AI"
        else: tvals["opponent"]=getPlayer(gm.player1).playername
        
        pagetype=gm.norm[self.request.get("pageType")]
        tvals["gameID"]=gmNum
        tvals["data"]=sjd(gm.getData())
        tvals["path"]=[("Homepage","/"),
                       ("games","/games"),
                       (pagetype+" view","")]
        tvals["links"]=[(ptype+" view",
                         "?pageType="+ptype+"&gameID="+gmNum+
                          ("" if pl else "&player="+pnum))
                       for ptype in gm.views if ptype!=pagetype]
        
        load(self,"/%s/%s.html"%(gname,pagetype),tvals)


## in progress
class MakeMove (webapp.RequestHandler):
    """handles a request to make a move"""
    @errordec
    @db.transactional(xg=True)
    def post(self,gname):
        pl = getCurrentPlayer()
        gmNum=self.request.get('gameID')
        gm=GAMES[gname].get_by_key_name(gmNum)
        if not gm:
            self.response.out.write("error, game not found")
            return None
        if not gm.state&STARTED:crash
        
        if pl:
            pl=pl.account
        else:
            pnum=self.request.get("playerID")
            #raise MyError(pnum)
            pl=User("p "+pnum)
        try:
            gm.move(pl,self.request.get('pos'))
        except InvalidInput as e:
            self.response.out.write(e.msg)
            return None
        
        dat=sjd(gm.getData())
        gm.tellPlayers(dat)
        self.response.out.write(dat)

##
class GetGame (webapp.RequestHandler):
    @db.transactional(xg=True)
    def get(self):
        """deals with a user polling for a game, checks the time limit"""
        gmNum=self.request.get('gameID')
        gm=GAMES[gname].get_by_key_name(gmNum)
        if not gm:
            return None
        if gm.turn!="ai":checkTime(gm)
        self.response.out.write(sjd(Game(gm).getData()))

##
class SendMessage(webapp.RequestHandler):
    """lets a user send a message to another user"""
    @db.transactional(xg=True)
    def post(self):
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
                        "WHERE started = False ")
        db.delete(games)
        games=db.GqlQuery("SELECT __key__ "
                        "FROM Game "
                        "WHERE winpos > '' ")
        db.delete(games)



#page,handler

gamepages=[("",Base),
           ("setup",NewGamePage),
           ("play",PlayPage),
           ("highscores",HighScores),
           ("about",AboutPage)]

#path,title
Pages=[("/", "Games")] + [
    ("/"+ob.path+"/"+page,ob.name+" - "+page, [])
    for ob in GAMES.values() if ob
    for page,handler in gamepages]

gameserv=[
    ('newgame', NewGame),
    ('respond', Response),
    ('checkrequest', CheckRequest),
    ('makemove', MakeMove),
    ('getgame', GetGame),
    ('msg', SendMessage)]

services=[
    ('/changename', ChangeName),
    ('/newchannel', ChannelCreator),
    ('clr', ClearGames)]

allpages= [("/",Games)] + services + [
    ("/(.+)/"+page, handler)
    for page,handler in gamepages+gameserv]

print(allpages)
    
app = webapp.WSGIApplication(allpages, debug=True)
        
