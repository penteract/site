# !/usr/bin/env python

import os
import datetime

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.api import channel,users
from django.utils import simplejson
sjd=simplejson.dumps
import jinja2
from time import clock
from datetime import datetime,timedelta
from random import randrange

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

    
other={"X":"O","O":"X","ai":"ai"}

#error handling
class Show(Exception):
    """An error class used to tell me parts of program state when debugging"""
    def __init__(self,s):
        self.s=s
    def __str__(self):
        return repr(self.s)

class InvalidInput(Exception):
    """An error class used to report when two things do not match when they should do"""
    def __init__(self,input,excpected,msg):
        self.input=input
        self.excpected=excpected
        self.msg=msg
    def __str__(self):
        return "excpected: "+repr(self.excpected)+"\nbut recieved"+repr(self.input)+"\n"+str(self.msg)
        
def check(a,b,msg):
    """raises an error if inputs are not equal"""
    if a!=b:raise InvalidInput(a,b,msg)


    
#models
class GameData(db.Model):
    """Stores information about a game"""
    turn=db.StringProperty()#"O" or "X" or "ai"
    winpos=db.StringProperty()#"" or "xyz" or "timeup"
    board=db.StringProperty()#" ","O" or "X" 64 times
    timeCreated = db.DateTimeProperty(auto_now_add=True)
    playerX=db.UserProperty()
    playerO=db.UserProperty()
    timeLimit=db.IntegerProperty()#used as the difficulty in AI games
    lastTurn=db.DateTimeProperty()
    started=db.BooleanProperty()
  
def game_key(gameNum):
    """Constructs a Datastore key for a GameData entity with a given id."""
    if all([c in "1234567890" for c in gameNum]):
        return db.Key.from_path('GameData',gameNum)
    else: return gameNum

def checkTime(game):
    """checks that the player whose turn it is has not run out of time"""
    if game.started and game.turn=="ai":return True
    if game.started and not game.winpos and datetime.now()>game.lastTurn+timedelta(seconds=game.timeLimit):
        game.winpos="timeup"
        win(game,other[game.turn],True)
        game.put()
        return False
    return True

    
class PlayerData(db.Model):
    """Stores information about players"""
    account=db.UserProperty()
    token=db.StringProperty()
    username=db.StringProperty()
    score=db.IntegerProperty()
    lastOnline =db.DateTimeProperty()
    online=db.BooleanProperty()#if False, definitely not online (or in the <10 second testing gap)
    dateJoined = db.DateTimeProperty(auto_now_add=True)
    
def getPlayer(nickname):
    """returns the player entity from a given email address"""
    return PlayerData.get(db.Key.from_path('PlayerData',str(hash(nickname))))
    
@db.transactional
def playerName(nickname,em=False):
    """returns a player's username, with the option to add the html tag <em>"""
    p=getPlayer(nickname)
    if not p:return None
    ret=p.username
    if em:ret="<em>"+ret+"</em>"
    return ret
    
@db.transactional
def getCurrentPlayer():
    """gets the PlayerData Entity for the player currently logged in"""
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


class Message(db.Model):
    """stores a message sent between players in a game"""
    sender=db.UserProperty()
    content=db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)


#webpages
class WelcomePage(webapp.RequestHandler):
    """the front page of my website"""
    def get(self):
        user = users.get_current_user()
	template_values = {}
	template = jinja_environment.get_template('index.html')
	self.response.out.write(template.render(template_values))
        
class UserPage(webapp.RequestHandler):
    """shows a user's homepage where they can continue games and start new ones"""
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return None
        pl=getPlayer(user.nickname())
        if pl==None:#create a new user
            pl=PlayerData(key_name=str(hash(user.nickname())))
            pl.account=user
            pl.score=1000
            pl.token=channel.create_channel(user.nickname())
            pl.username="user"
        pl.lastonline=datetime.now()
        pl.online=True
        pl.put()
        players=db.GqlQuery("SELECT * "
                        "FROM PlayerData "
                        "WHERE online = TRUE "
                        "ORDER BY lastOnline DESC LIMIT 10")
        players=[{"id":hash(p.account.nickname()),
                  "name":p.username,
                  "score":p.score} for p in players]
        
        gamesX=db.GqlQuery("SELECT playerO, turn "
                           "FROM GameData "
                           "WHERE playerX = :1 AND started=TRUE AND winpos=''",
                           pl.account)
        games=[{"id":game.key().id_or_name(),
                "O":"AI" if game.turn=="ai" else playerName(game.playerO.nickname(),game.turn=="O"),
                "X":playerName(pl.account.nickname(),game.turn!="O")}
                for game in gamesX]
        gamesO=db.GqlQuery("SELECT playerX, turn "
                           "FROM GameData "
                           "WHERE playerO = :1 AND started=TRUE AND winpos=''",
                           pl.account)
        games+=[{"id":game.key().id_or_name(),
                "O":playerName(pl.account.nickname(),game.turn=="O"),
                "X":playerName(game.playerX.nickname(),game.turn=="X")}
                for game in gamesO if game.playerX!=pl.account]
        
        template_values = {"name":pl.username,
                           "score":pl.score,
                           "logouturl":users.create_logout_url("/"),
                           "chtoken":pl.token,
                           "players":players,
                           "games":games}
        template = jinja_environment.get_template('user.html')
        self.response.out.write(template.render(template_values))
        

class HighScores(webapp.RequestHandler):
    """shows a list of highscores"""
    def get(self):
        user = users.get_current_user()
        if user:
            pl=getPlayer(user.nickname())
            if pl==None:
                self.redirect("/user")
                return None
            template_values={
                "player":{"name":pl.username,
                          "id":pl.account.nickname(),
                          "score":pl.score},
                "logouturl":users.create_logout_url(self.request.uri),
                "chtoken":pl.token}
        else:
            template_values={"player":None,"loginurl":users.create_login_url(self.request.uri)}
        
        players=db.GqlQuery("SELECT username,score,account "
                            "FROM PlayerData "
                            "ORDER BY score DESC LIMIT 10")
        template_values["players"]=[{"name":p.username,
            "score":p.score,
            "id":p.account.nickname()} for p in players]
        template = jinja_environment.get_template('highscore.html')
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
        """shows a page where the user can select options for the game they want to start"""
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
        

class AIGame(webapp.RequestHandler):
    """handles a request to start a game with the AI"""
    
    def get(self):
        """returns a page where the user can select options for the game they want to start"""
        pl=getCurrentPlayer()
        if not pl:
            self.redirect("/")
            return None
        template_values = {"chtoken":pl.token}
        template = jinja_environment.get_template('aioffer.html')
        self.response.out.write(template.render(template_values))
        
        
    @db.transactional(xg=True)
    def post(self):
        """starts a game against the AI"""
        pl=getCurrentPlayer()
        if not pl:
            return None
        #create the game Entity
        difficulty=int(self.request.get("difficulty"))
        assert difficulty in range(3)
        gm=True
        while gm:
            gmNum=str(randrange(100000000))
            gm=GameData.get(game_key(gmNum))
        gm=GameData(key_name=gmNum)
        gm.turn="ai"
        gm.board=" "*64
        gm.winpos=""
        gm.started=True
        gm.playerO=pl.account
        gm.playerX=pl.account#saves trouble but may cause problems
        gm.timeLimit=difficulty
        gm.put()
        self.response.out.write(gmNum)
        
        
class Response(webapp.RequestHandler):
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
        

class GamePage(webapp.RequestHandler):
    def get(self):
        """Shows a page on which a game can be played"""
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
        if not gm.started:
            self.redirect("/user")
            return None
        if gm.turn=="ai":
            template_values = {"gameID":gmNum,
                               "board":gm.board,
                               "chtoken":pl.token,
                               "data":sjd(Game(gm).getData()),
                               "player":getPlayer(gm.playerO.nickname()).username,
                               "opponent":"AI"}
        else:
            if not gm.winpos:
                checkTime(gm)
            players=[getPlayer(gm.playerX.nickname()),
                     getPlayer(gm.playerO.nickname())]
            pln=int(players[1]==pl)
            
            #show the page
            template_values = {"gameID":gmNum,
                               "board":gm.board,
                               "chtoken":pl.token,
                               "data":sjd(Game(gm).getData()),
                               "player":players[pln].username,
                               "opponent":players[1-pln].username}
        pageType=self.request.get('pageType')
        file=""
        if pageType=="" or pageType=="table":
            file='tablegame.html'
        if pageType=="canvas":
            file='canvasgame.html'
        if pageType=="threeD":
            file='3Dgame.html'
        if file: self.response.out.write(jinja_environment.get_template(file).render(template_values))
    
class MakeMove (webapp.RequestHandler):
    """handles a request to make a move"""
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
        if gm.winpos or not checkTime(gm):
            self.response.out.write("game's over")
            return None
        
        pos = self.request.get('pos')
        if not pos:
            self.response.out.write("error")
            return None
        x,y,z=(int(c) for c in pos)
        game=Game(gm)
        try: game.go(pl,x,y,z)
        except InvalidInput as e:
            self.response.out.write(e.msg)
            return None
        game.sync(gm)
        gm.lastTurn=datetime.now()
        if gm.winpos: win(gm,game.turn)
        if gm.turn=="ai" and not gm.winpos:
            game.aiMove(gm.timeLimit)
            if gm.winpos: win(gm,"AI")
            game.sync(gm)
        gm.put()
        for player in [gm.playerX,gm.playerO]:
            channel.send_message(player.nickname(),sjd(game.getData()))
        self.response.out.write("none")
    
class GetGame (webapp.RequestHandler):
    @db.transactional(xg=True)
    def get(self):
        """deals with a user polling for a game, checks the time limit"""
        gmNum=self.request.get('gameID')
        gameID = game_key(gmNum)
        gm=GameData.get(gameID)
        if not gm:
            return None
        if gm.turn!="ai":checkTime(gm)
        self.response.out.write(sjd(Game(gm).getData()))
    
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
        


class Game():
    """a game object that supports manipulation"""
    def __init__(self,gmData):
        """creates the object from an Entity """
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
        self.started=gmData.started
        self.Num=gmData.key().name()
        self.winpos=gmData.winpos
        self.wonlines=[]
        if gmData.winpos not in ["","timeup"]:
            x,y,z=(int(n) for n in self.winpos)
            c=self.board[z][y][x]
            for line in self.linesThrough(x,y,z):
                if all([p==c for p in line[0]]):
                    self.wonlines.append(line[1])
        
            
        
    def getData(self):
        """returns information about the game in a format suitable to be sent to a client"""
        d={"request":"gameUpdate", "gameID":self.Num,
            "wonlines":self.wonlines}
        d["board"]="".join(["".join(["".join(y) for y in z]) for z in self.board])
        return d
        
    def go(self,player,x,y,z):
        """validates a move then updates the game state"""
        tok=["O","X"][int(player=="ai")] if self.turn=="ai" else self.turn
        check(self.started,True,"this game has not yet started")
        check(self.winpos,"","game's over")
        if player!="ai":check(player.account,self.players[tok],"it is not your turn")
        check(self.board[z][y][x]," ","you must go in an empty cell")
        self.board[z][y][x]=tok
        for line in self.linesThrough(x,y,z):
            if all([p==tok for p in line[0]]):
                self.wonlines.append(line[1])
        if self.wonlines: self.winpos=str(x)+str(y)+str(z)
        else:self.turn=other[self.turn]
        
    def aiMove(self,difficulty):
        """makes a move by the AI at the given difficulty setting"""
        pscores=[[0]*4,[1,1,1,100],[10,20,81,8000]][difficulty]
        oscores=[[0]*4,[1,1,1,10],[10,15,80,1000]][difficulty]
        maxscore=0
        topcells=[]
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if self.board[z][y][x]!=" ":continue
                    score=0
                    for line,cls in self.linesThrough(x,y,z):
                        p=line.count("X")#assumes AI is always X
                        o=line.count("O")
                        if p==0: score+=oscores[o]
                        elif o==0: score+=pscores[p]
                    if score>maxscore:
                        topcells=[(x,y,z)]
                        maxscore=score
                    elif score==maxscore:topcells.append((x,y,z))
        x,y,z=topcells[randrange(len(topcells))]
        self.go("ai",x,y,z)
        
    def sync(self,gameData):
        """updates a Gamedata entity to match the current status of this game"""
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
    def get(self):
        games=db.GqlQuery("SELECT __key__ "
                        "FROM GameData "
                        "WHERE started = False ")
        db.delete(games)
        games=db.GqlQuery("SELECT __key__ "
                        "FROM GameData "
                        "WHERE winpos > '' ")
        db.delete(games)

#class Clear(webapp.RequestHandler):
#    """clear all game data"""
#    def get(self):
#        db.delete(PlayerData.all(keys_only=True).run())

        
app = webapp.WSGIApplication([
    ('/', WelcomePage),
    ('/3Dox', UserPage),
    ('/highscores', HighScores),
    ('/changeName', ChangeName),
    ('/newChannel', ChannelCreator),
    ('/newGame', NewGame),
    ('/aiGame', AIGame),
    ('/respond', Response),
    ('/checkRequest', CheckRequest),
    ('/game', GamePage),
    ('/makeMove', MakeMove),
    ('/clr', ClearGames),
    ('/getGame', GetGame),
    ('/msg', SendMessage),
    #('/clrall', Clear),
     ], debug=True)
        