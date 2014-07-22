# !/usr/bin/env python

from tools import *
from game import Game
from random import randrange

from google.appengine.ext import db


class AI:
    def __init__(self,diff):
        self.weights=[([0]*4,[0]*4),([1,1,1,100],[1,1,1,10]),([10,20,81,8000],[10,15,80,1000])][diff]
        self.name="AI "+["easy","medium","hard"][diff]
        self.score=[100,1000,2000][diff]
    def nextmove(self,board,pos):
        return pos##fails


class ox3(Game):
    """a 3D version of noughts and crosses on a 4*4*4 grid"""
    board=db.StringProperty(default=" "*64)
    winpos=db.StringProperty(default="")
    wonlines=[]
    
    path="ox3"
    name="3D noughts and crosses"
    ais=[AI(diff) for diff in range(3)]
    views=["table","canvas","perspective"]
    norm={"":"table",
          "threeD":"perspective"}#normalizes the name of the view
    norm.update({v:v for v in views})
           
    def __init__(self,*args,**kwargs):
        super(ox3,self).__init__(*args,**kwargs)
        self.wonlines=[]
        if self.winpos: self.checklines(int(c) for c in self.winpos)
    
    def getData(self):
        """returns information about the game in a format suitable to be sent to a client"""
        d=self.dataHeader()
        d.update({"wonlines":self.wonlines, "board":self.board})
        #d["board"]="".join(["".join(["".join(y) for y in z]) for z in self.board])
        return d
        
    def getAt(self,x,y,z):
        """returns the token at position x,y,z"""
        return self.board[16*z+4*y+x]
        
    def setAt(self,x,y,z,tok):
        """sets the token at position x,y,z"""
        self.board=self.board[:16*z+4*y+x]+tok+self.board[16*z+4*y+x+1:]
        
    def move(self,pl,pos):
        """validates a move then updates the game state"""
        tok=["X","O"][self.checkturn(pl)]
        if not pos:
            raise HttpError(400)
        x,y,z=(int(c) for c in pos)
        check(self.getAt(x,y,z)," ","you must go in an empty cell")
        self.setAt(x,y,z,tok)
        if self.checklines((x,y,z)):
            self.winpos=str(x)+str(y)+str(z)
            self.state|=GAMEOVER
        
        self.endmove()
        
        
    def checklines(self,pos=None):
        """checks if the game should be finished and sets the lines corresponding which won"""
        for chars,coords in self.alllines() if pos is None else self.linesThrough(*pos):
            c=chars[0]
            if c!=" " and all([p==c for p in chars]):
                self.wonlines.append(coords)
        return bool(self.wonlines)
            
            
        
    def aiMove(self,difficulty):
        """makes a move by the AI at the given difficulty setting"""
        pscores=[[0]*4,[1,1,1,100],[10,20,81,8000]][difficulty]
        oscores=[[0]*4,[1,1,1,10],[10,15,80,1000]][difficulty]
        maxscore=0
        topcells=[]
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if self.getAt(x,y,z)!=" ":continue
                    score=0
                    for line,cls in self.linesThrough(x,y,z):
                        p=line.count("O")#assumes AI is always O
                        o=line.count("X")
                        if p==0: score+=oscores[o]
                        elif o==0: score+=pscores[p]
                    if score>maxscore:
                        topcells=[(x,y,z)]
                        maxscore=score
                    elif score==maxscore:topcells.append((x,y,z))
        x,y,z=choice(topcells)
        self.setAt(x,y,z,"O")
        if self.checklines((x,y,z)):
            self.state|=TURN|GAMEOVER
    
    def linesThrough(self,x,y,z):
        """returns a list of the lines through a point
           in the form [(["X","O","O","O"],[(0,2,3),(1,2,3),(2,2,3),(3,2,3)]),
           (["O"...],[...]),...]"""
        lines=[[],[],[]]
        for n in range(4):
            lines[0].append((x,y,n))
            lines[1].append((x,n,z))
            lines[2].append((n,y,z))
        xp=abs(x-1.5)
        yp=abs(y-1.5)
        zp=abs(z-1.5)
        if zp==yp:
            lines.append([])
            for n in range(4):
                lines[-1].append((x,n if y==z else 3-n,n))
        if zp==xp:
            lines.append([])
            for n in range(4):
                lines[-1].append((n if x==z else 3-n,y,n))
        if yp==xp:
            lines.append([])
            for n in range(4):
                lines[-1].append((n if y==x else 3-n,n,z))
        if zp==yp and zp==xp:
            lines.append([])
            for n in range(4):
                lines[-1].append((n if z==x else 3-n,n if y==z else 3-n,n))
        return [([self.getAt(*pos) for pos in l],l) for l in lines]
        
    def allLines(self):
        """returns all lines through the board, in the same format as above"""
        allL=[[(3,0,0),(2,0,0),(1,0,0),(0,0,0)],[(3,1,0),(2,1,0),(1,1,0),(0,1,0)],[(3,2,0),(2,2,0),(1,2,0),(0,2,0)],[(3,3,0),(2,3,0),(1,3,0),(0,3,0)],[(0,3,0),(0,2,0),(0,1,0),(0,0,0)],[(1,3,0),(1,2,0),(1,1,0),(1,0,0)],[(2,3,0),(2,2,0),(2,1,0),(2,0,0)],[(3,3,0),(3,2,0),(3,1,0),(3,0,0)],[(3,3,0),(2,2,0),(1,1,0),(0,0,0)],[(5,3,0),(5,2,0),(5,1,0),(5,0,0)],[(3,0,1),(2,0,1),(1,0,1),(0,0,1)],[(3,1,1),(2,1,1),(1,1,1),(0,1,1)],[(3,2,1),(2,2,1),(1,2,1),(0,2,1)],[(3,3,1),(2,3,1),(1,3,1),(0,3,1)],[(0,3,1),(0,2,1),(0,1,1),(0,0,1)],[(1,3,1),(1,2,1),(1,1,1),(1,0,1)],[(2,3,1),(2,2,1),(2,1,1),(2,0,1)],[(3,3,1),(3,2,1),(3,1,1),(3,0,1)],[(3,3,1),(2,2,1),(1,1,1),(0,0,1)],[(5,3,1),(5,2,1),(5,1,1),(5,0,1)],[(3,0,2),(2,0,2),(1,0,2),(0,0,2)],[(3,1,2),(2,1,2),(1,1,2),(0,1,2)],[(3,2,2),(2,2,2),(1,2,2),(0,2,2)],[(3,3,2),(2,3,2),(1,3,2),(0,3,2)],[(0,3,2),(0,2,2),(0,1,2),(0,0,2)],[(1,3,2),(1,2,2),(1,1,2),(1,0,2)],[(2,3,2),(2,2,2),(2,1,2),(2,0,2)],[(3,3,2),(3,2,2),(3,1,2),(3,0,2)],[(3,3,2),(2,2,2),(1,1,2),(0,0,2)],[(5,3,2),(5,2,2),(5,1,2),(5,0,2)],[(3,0,3),(2,0,3),(1,0,3),(0,0,3)],[(3,1,3),(2,1,3),(1,1,3),(0,1,3)],[(3,2,3),(2,2,3),(1,2,3),(0,2,3)],[(3,3,3),(2,3,3),(1,3,3),(0,3,3)],[(0,3,3),(0,2,3),(0,1,3),(0,0,3)],[(1,3,3),(1,2,3),(1,1,3),(1,0,3)],[(2,3,3),(2,2,3),(2,1,3),(2,0,3)],[(3,3,3),(3,2,3),(3,1,3),(3,0,3)],[(3,3,3),(2,2,3),(1,1,3),(0,0,3)],[(5,3,3),(5,2,3),(5,1,3),(5,0,3)],[(0,0,3),(0,0,2),(0,0,1),(0,0,0)],[(1,0,3),(1,0,2),(1,0,1),(1,0,0)],[(2,0,3),(2,0,2),(2,0,1),(2,0,0)],[(3,0,3),(3,0,2),(3,0,1),(3,0,0)],[(3,0,3),(2,0,2),(1,0,1),(0,0,0)],[(5,0,3),(5,0,2),(5,0,1),(5,0,0)],[(0,1,3),(0,1,2),(0,1,1),(0,1,0)],[(1,1,3),(1,1,2),(1,1,1),(1,1,0)],[(2,1,3),(2,1,2),(2,1,1),(2,1,0)],[(3,1,3),(3,1,2),(3,1,1),(3,1,0)],[(3,1,3),(2,1,2),(1,1,1),(0,1,0)],[(5,1,3),(5,1,2),(5,1,1),(5,1,0)],[(0,2,3),(0,2,2),(0,2,1),(0,2,0)],[(1,2,3),(1,2,2),(1,2,1),(1,2,0)],[(2,2,3),(2,2,2),(2,2,1),(2,2,0)],[(3,2,3),(3,2,2),(3,2,1),(3,2,0)],[(3,2,3),(2,2,2),(1,2,1),(0,2,0)],[(5,2,3),(5,2,2),(5,2,1),(5,2,0)],[(0,3,3),(0,3,2),(0,3,1),(0,3,0)],[(1,3,3),(1,3,2),(1,3,1),(1,3,0)],[(2,3,3),(2,3,2),(2,3,1),(2,3,0)],[(3,3,3),(3,3,2),(3,3,1),(3,3,0)],[(3,3,3),(2,3,2),(1,3,1),(0,3,0)],[(5,3,3),(5,3,2),(5,3,1),(5,3,0)],[(0,3,3),(0,2,2),(0,1,1),(0,0,0)],[(1,3,3),(1,2,2),(1,1,1),(1,0,0)],[(2,3,3),(2,2,2),(2,1,1),(2,0,0)],[(3,3,3),(3,2,2),(3,1,1),(3,0,0)],[(3,3,3),(2,2,2),(1,1,1),(0,0,0)],[(5,3,3),(5,2,2),(5,1,1),(5,0,0)],[(0,5,3),(0,5,2),(0,5,1),(0,5,0)],[(1,5,3),(1,5,2),(1,5,1),(1,5,0)],[(2,5,3),(2,5,2),(2,5,1),(2,5,0)],[(3,5,3),(3,5,2),(3,5,1),(3,5,0)],[(5,5,3),(5,5,2),(5,5,1),(5,5,0)],[(5,3,5),(5,2,5),(5,1,5),(5,0,5)]]
        return [([self.getAt(*pos) for pos in l],l) for l in allL]


class AIGame():
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

class CheckRequest(): 
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
        

class GamePage():
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
    
class MakeMove ():
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
    
class GetGame ():
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
    
class SendMessage():
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
        


class Gamee():
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
