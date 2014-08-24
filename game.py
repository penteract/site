# !/usr/bin/env python

from tools import *

#import datetime

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.api import channel
    
#models
class Game(polymodel.PolyModel):
    """Base class for games"""
    timeCreated = db.DateTimeProperty(auto_now_add=True)
    player0=db.UserProperty()#the player who started the game
    player1=db.UserProperty()
    # "a AI" is the 'email' of any AI
    # players which do not have accounts are stored with an address 
    # starting "p " followed by a random string
    timeLimit=db.IntegerProperty()#used as the difficulty in AI games
    lastMessage=db.StringProperty()
    lastMessageTime=db.DateTimeProperty(auto_now_add=True)
    lastTurn=db.DateTimeProperty()
    state=db.IntegerProperty(default=0)
    # bitstring: 0btdwsap p=turn, a=ai,s=started, w=gameover d=draw t=ttimeup
    # eg 0b01101 means player1 (as opposed to player0) has won
    
        
    def url(self,player=0):
        """a general url for playing the game"""
        if player==0: e=self.player0.email()
        elif player==1: e=self.player1.email()
        else: e=""
        if e.startswith("p "):
            return "/"+self.path+"/play?gameID="+self.key().name()+"&playerID="+e[2:]
        else: return "/"+self.path+"/play?gameID="+self.key().name()
        
    
    def gameover(self):
        """returns true when the game is over"""
        return bool(self.state&4)

    def move(self,player,move):
        """a player playing at a postion
        validates a move then updates the game state"""
        abstract
    
    def checkturn(self,pl):
        """checks that it is pl's turn, and returns their number (0 or 1)
        also checks that the game is not over yet"""
        self.checkTime()
        check(self.state&GAMEOVER,0,"game's over")
        turn=self.state&TURN
        check([self.player0,self.player1][turn],pl,"it is not your turn")
        return turn
    
    def aiMove(self,diff):
        """makes a move by the AI at the given difficulty setting"""
        self.ais[diff].play(self)
        
    def endmove(self):
        """to be called after a move ends"""
        self.lastTurn=datetime.now()
        if self.state&GAMEOVER: self.win()
        elif self.state&AIP:
            self.aiMove(self.timeLimit)
            if self.state&GAMEOVER: self.win()
        else:
            self.state^=TURN
            
        self.put()
        
    ##
    def win(self,byTime=False):
        msg={"request":"gameOver", "won":not bool(self.state&DRAW),
             "reason":"timeup" if byTime else "line",
             "gameID":self.key().name()}
        if byTime: self.state^=TURN;self.state|=TIMEUP
        self.state|=GAMEOVER
        
    def getData(self):
        """returns information about the game in a format suitable to be sent to a client
        uses dataHeader but should not send time information"""
        abstract
        
    def dataHeader(self):
        """returns the part of getData common to all games"""
        d={"request":"gameUpdate", "gameID":self.key().name(),
           "finished":bool(self.state&GAMEOVER),
           "message":self.lastMessage,
           "turn":self.state&TURN}
        if d["finished"]:d["draw"]=bool(self.state&DRAW)
        return d

    def checkTime(self):
        """checks that the player whose turn it is has not run out of time"""
        if self.state&(AIP|GAMEOVER):return True
        if datetime.now()>self.lastTurn+timedelta(seconds=self.timeLimit):
            self.win(byTime=True)
            return False
        return True
        
    def tellPlayers(self,msg):
        """sends a message to all players of this game via the channel API"""
        if not isinstance(msg,str):msg=sjd(msg)
        for p in self.player0,self.player1:
            if p.email()[1]!=" ":channel.send_message(p.email(),msg)
    
        


def game_key(gameNum):
    """Constructs a Datastore key for a GameData entity with a given id."""
    #I really should know if I'm working with a key or a key name
    if all([c in "1234567890" for c in gameNum]):
        return db.Key.from_path('Game',gameNum)
    else: return gameNum
    
@db.transactional
def win(game,winner,timeup=False):
    """informs players that the game is over and updates their scores"""
    pls={"X":getPlayer(game.playerX.nickname()),
         "O":getPlayer(game.playerO.nickname())}
    msg={"request":"gameover", "won":True,
         "reason":"timeup" if timeup else "line",
         "gameID":game.key().name()}
    if game.turn=="ai":
        msg["won"]=(winner=="ai")
        channel.send_message(pls["O"].account.nickname(),sjd(msg))
        return None
    loser=other[winner]
    dScore=int(pls[loser].score/10)
    pls[winner].score+=dScore
    pls[loser].score-=dScore
    channel.send_message(pls[winner].account.nickname(),sjd(msg))
    msg["won"]=False
    channel.send_message(pls[loser].account.nickname(),sjd(msg))
    for pl in pls:pls[pl].put()
        
class Response():
    """handles the response to a game request"""
    
    @db.transactional(xg=True)
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
            gm.started=True
            gm.lastTurn=datetime.now()
            gm.put()
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
        if answer=="no":
            channel.send_message(gm.playerO.nickname(),simplejson.dumps(message))
            db.delete(gm)
