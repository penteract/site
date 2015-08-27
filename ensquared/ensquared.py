# !/usr/bin/env python

from tools import *
from game import Game
from random import randrange,seed
import math

from google.appengine.ext import db

SIZE=16
OTHER={"UD":"LR","LR":"UD","L":"R","R":"L","D":"U","U":"D"}

def move(pos,c):
    x,y=pos
    if c=="U":y-=1
    elif c=="D":y+=1
    elif c=="L":x-=1
    elif c=="R":x+=1
    return (x,y)

seeded=False
class GameState:
    """stores the state of a game in progress with methods for utility"""
    def __init__(self,g):
        """g is an instance of ensquared"""
        self.turn=int(len(g.p0)!=len(g.p1))#0 if it is the starting player's turn
        h=SIZE/2
        r=list(range(1,SIZE))
        self.board=[[x==h and y==h for y in r] for x in r]
        self.playerpos=[None,None]
        for p in [0,1]:
            x,y=h,h
            for c in [g.p0,g.p1][self.turn ^ p ^ (g.state&TURN)]:
                x,y=move((x,y),c)
                self.board[x-1][y-1]=True
            self.playerpos[p]=x,y
        self.d=perpendicular[[g.p0,g.p1][g.state&TURN][-1]]
        
    def do(self,c):
        """does a move, assumes it is legal"""
        self.playerpos[self.turn]=move(self.playerpos[self.turn],c)
        x,y=self.playerpos[self.turn]
        self.board[x-1][y-1]=True
        self.turn=1-self.turn
        if self.turn==1: self.d=OTHER[self.d]
    def loses(self,c):
        x,y=move(self.playerpos[self.turn],c)
        return x not in range(1,SIZE) or y not in range(1,SIZE) or self.board[x-1][y-1]
    def __str__(self):
        a,b=self.playerpos[self.turn]
        return "-"*SIZE+"|\n|"+"|\n|".join("".join("*" if x+1==a and y+1==b else ("#" if self.board[x][y] else " ") for x in range(SIZE-1)) for y in range(SIZE-1))+"|\n|"+"-"*SIZE

    
  
class MonteCarloAI:
    name="monte carlo"
    def play(self,game):
        """play!"""
        tree={}
        #print(GameState(game))
        for n in range(1000):
            select(tree,GameState(game))
        bestc=None
        best=-1
        for c in tree:
            visits,wins,t=tree[c]
            if visits==0:
                val=-0.5
            else: val=wins*1.0/visits
            #print(c,val)
            
            if val>best:
                bestc=c
                best=val
            elif val==best and randrange(2):
                bestc=c
        
        game.move(game.player1,bestc)

def select(tree,game):
    global seeded
    if not seeded:
        seed(0)
        seeded=True
    if tree=={}:
        for c in game.d:
            if game.loses(c):
                tree[c]=(0,-1,None)
            else:
                tree[c]=(0,0,{})
    best=-1
    bestc=None
    sumv=sum(tree[c][0] for c in tree)
    for c in tree:
        visits,wins,t=tree[c]
        if wins!=-1:
            if visits==0:
                val=10
            else: val=wins*1.0/visits+math.log(sumv)/visits
            if val>best:
                bestc=c
                best=val
            elif val==best and randrange(2):
                bestc=c
    if bestc==None:#guarenteed loss
        return False
        
    game.do(bestc)
    visits,wins,t=tree[bestc]
    result=not select(t,game)
    tree[bestc]=visits+1,wins+result,t
    return result

class ensquared(Game):
    """The amazing game of ensquared"""
    #really these could just be bitstrings saying left/right or up/down, but string stores the length as well
    p0=db.StringProperty(default="U")
    p1=db.StringProperty(default="R")
    lastPlayerWins=False
    
    path="ensquared"
    name="Ensquared"
    ais=[MonteCarloAI()]
    views=["canvas"]
           
    def __init__(self,*args,**kwargs):
        super(ensquared,self).__init__(*args,**kwargs)
    
    def getData(self):
        """returns information about the game in a format suitable to be sent to a client"""
        d=self.dataHeader()
        d.update({"p0":self.p0, "p1":self.p1})
        return d
    
    def crashes(self):
        """checks if one line crashes into the other, itself, or the edge"""
        board=[[0 for y in range(SIZE-1)] for x in range(SIZE-1)]
        r=range(1,SIZE)
        h=SIZE/2
        for s in [self.p0,self.p1]:
            x,y=h,h
            for c in s:
                x,y=move((x,y),c)
                if x not in r or y not in r or board[x-1][y-1] or (x==h and y==h):
                    return True
                board[x-1][y-1]=1
                
        
    def move(self,pl,pos):
        """validates a move then updates the game state"""
        turn=self.checkturn(pl)
        prev=[self.p0,self.p1][turn][-1]
        if pos not in "LURD":
            raise HttpError(400)
        if pos not in perpendicular[prev]:
            raise InvalidInput(pos,perpendicular[prev],"You must go at right angles to your previous move")
        if turn:self.p1+=pos
        else:self.p0+=pos
        
        if self.crashes():
            self.state|=GAMEOVER
            
        
        if not pl.email().startswith("a "): self.endmove()
        
perpendicular={"U":"LR", "D":"LR",
               "L":"UD", "R":"UD"}