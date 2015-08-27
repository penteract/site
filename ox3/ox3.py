# !/usr/bin/env python

from tools import *
from game import Game
from random import randrange
from google.appengine.api.users import User

from google.appengine.ext import db


class AI:
    def __init__(self,weights,name=None):
        if isinstance(weights,int):
            self.weights=[([0]*4,[0]*4),([1,1,1,100],[1,1,1,10]),([10,20,81,8000],[10,15,80,1000])][weights]
            self.name="AI "+["easy","medium","hard"][weights]
            self.score=[100,1000,2000][weights]
        else:
            self.weights=weights
            self.name="AI "+name
            self.score=0
            
    def play(self,game):
        """play!"""
        pscores,oscores=self.weights
        maxscore=0
        topcells=[]
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if game.getAt(x,y,z)!=" ":continue
                    score=0
                    for line,cls in game.linesThrough(x,y,z):
                        p=line.count("O")#assumes AI is always O
                        o=line.count("X")
                        if p==0: score+=oscores[o]
                        elif o==0: score+=pscores[p]
                    if score>maxscore:
                        topcells=[(x,y,z)]
                        maxscore=score
                    elif score==maxscore:topcells.append((x,y,z))
        x,y,z=choice(topcells)
        game.move(game.player1,str(x)+str(y)+str(z))


class ox3(Game):
    """a 3D version of noughts and crosses on a 4*4*4 grid"""
    board=db.StringProperty(default=" "*64)
    winpos=db.StringProperty(default="")
    wonlines=[]
    
    lastPlayerWins=True
    path="ox3"
    name="3D noughts and crosses"
    ais=[AI(diff) for diff in range(3)]+[
        AI(([1410, 2362, 6431, 689015], [699, 1656, 5501, 63965]),"evolved")]
    views=["table","perspective"]
           
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
        
        if not pl.email().startswith("a "): self.endmove()
        
        
    def checklines(self,pos=None):
        """checks if the game should be finished and sets the lines corresponding which won"""
        for chars,coords in self.alllines() if pos is None else self.linesThrough(*pos):
            c=chars[0]
            if c!=" " and all([p==c for p in chars]):
                self.wonlines.append(coords)
        return bool(self.wonlines)
            
            
    
    
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
        return [([self.getAt(*pos) for pos in l],l) for l in allL]



allL=[[(3,0,0),(2,0,0),(1,0,0),(0,0,0)],[(3,1,0),(2,1,0),(1,1,0),(0,1,0)],[(3,2,0),(2,2,0),(1,2,0),(0,2,0)],[(3,3,0),(2,3,0),(1,3,0),(0,3,0)],[(0,3,0),(0,2,0),(0,1,0),(0,0,0)],[(1,3,0),(1,2,0),(1,1,0),(1,0,0)],[(2,3,0),(2,2,0),(2,1,0),(2,0,0)],[(3,3,0),(3,2,0),(3,1,0),(3,0,0)],[(3,3,0),(2,2,0),(1,1,0),(0,0,0)],[(5,3,0),(5,2,0),(5,1,0),(5,0,0)],[(3,0,1),(2,0,1),(1,0,1),(0,0,1)],[(3,1,1),(2,1,1),(1,1,1),(0,1,1)],[(3,2,1),(2,2,1),(1,2,1),(0,2,1)],[(3,3,1),(2,3,1),(1,3,1),(0,3,1)],[(0,3,1),(0,2,1),(0,1,1),(0,0,1)],[(1,3,1),(1,2,1),(1,1,1),(1,0,1)],[(2,3,1),(2,2,1),(2,1,1),(2,0,1)],[(3,3,1),(3,2,1),(3,1,1),(3,0,1)],[(3,3,1),(2,2,1),(1,1,1),(0,0,1)],[(5,3,1),(5,2,1),(5,1,1),(5,0,1)],[(3,0,2),(2,0,2),(1,0,2),(0,0,2)],[(3,1,2),(2,1,2),(1,1,2),(0,1,2)],[(3,2,2),(2,2,2),(1,2,2),(0,2,2)],[(3,3,2),(2,3,2),(1,3,2),(0,3,2)],[(0,3,2),(0,2,2),(0,1,2),(0,0,2)],[(1,3,2),(1,2,2),(1,1,2),(1,0,2)],[(2,3,2),(2,2,2),(2,1,2),(2,0,2)],[(3,3,2),(3,2,2),(3,1,2),(3,0,2)],[(3,3,2),(2,2,2),(1,1,2),(0,0,2)],[(5,3,2),(5,2,2),(5,1,2),(5,0,2)],[(3,0,3),(2,0,3),(1,0,3),(0,0,3)],[(3,1,3),(2,1,3),(1,1,3),(0,1,3)],[(3,2,3),(2,2,3),(1,2,3),(0,2,3)],[(3,3,3),(2,3,3),(1,3,3),(0,3,3)],[(0,3,3),(0,2,3),(0,1,3),(0,0,3)],[(1,3,3),(1,2,3),(1,1,3),(1,0,3)],[(2,3,3),(2,2,3),(2,1,3),(2,0,3)],[(3,3,3),(3,2,3),(3,1,3),(3,0,3)],[(3,3,3),(2,2,3),(1,1,3),(0,0,3)],[(5,3,3),(5,2,3),(5,1,3),(5,0,3)],[(0,0,3),(0,0,2),(0,0,1),(0,0,0)],[(1,0,3),(1,0,2),(1,0,1),(1,0,0)],[(2,0,3),(2,0,2),(2,0,1),(2,0,0)],[(3,0,3),(3,0,2),(3,0,1),(3,0,0)],[(3,0,3),(2,0,2),(1,0,1),(0,0,0)],[(5,0,3),(5,0,2),(5,0,1),(5,0,0)],[(0,1,3),(0,1,2),(0,1,1),(0,1,0)],[(1,1,3),(1,1,2),(1,1,1),(1,1,0)],[(2,1,3),(2,1,2),(2,1,1),(2,1,0)],[(3,1,3),(3,1,2),(3,1,1),(3,1,0)],[(3,1,3),(2,1,2),(1,1,1),(0,1,0)],[(5,1,3),(5,1,2),(5,1,1),(5,1,0)],[(0,2,3),(0,2,2),(0,2,1),(0,2,0)],[(1,2,3),(1,2,2),(1,2,1),(1,2,0)],[(2,2,3),(2,2,2),(2,2,1),(2,2,0)],[(3,2,3),(3,2,2),(3,2,1),(3,2,0)],[(3,2,3),(2,2,2),(1,2,1),(0,2,0)],[(5,2,3),(5,2,2),(5,2,1),(5,2,0)],[(0,3,3),(0,3,2),(0,3,1),(0,3,0)],[(1,3,3),(1,3,2),(1,3,1),(1,3,0)],[(2,3,3),(2,3,2),(2,3,1),(2,3,0)],[(3,3,3),(3,3,2),(3,3,1),(3,3,0)],[(3,3,3),(2,3,2),(1,3,1),(0,3,0)],[(5,3,3),(5,3,2),(5,3,1),(5,3,0)],[(0,3,3),(0,2,2),(0,1,1),(0,0,0)],[(1,3,3),(1,2,2),(1,1,1),(1,0,0)],[(2,3,3),(2,2,2),(2,1,1),(2,0,0)],[(3,3,3),(3,2,2),(3,1,1),(3,0,0)],[(3,3,3),(2,2,2),(1,1,1),(0,0,0)],[(5,3,3),(5,2,2),(5,1,1),(5,0,0)],[(0,5,3),(0,5,2),(0,5,1),(0,5,0)],[(1,5,3),(1,5,2),(1,5,1),(1,5,0)],[(2,5,3),(2,5,2),(2,5,1),(2,5,0)],[(3,5,3),(3,5,2),(3,5,1),(3,5,0)],[(5,5,3),(5,5,2),(5,5,1),(5,5,0)],[(5,3,5),(5,2,5),(5,1,5),(5,0,5)]]