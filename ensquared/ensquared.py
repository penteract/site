# !/usr/bin/env python

from tools import *
from game import Game
from random import randrange

from google.appengine.ext import db

SIZE=16


class ensquared(Game):
    """The amazing game of ensquared"""
    #really these could just be bitstrings saying left/right or up/down, but string stores the length as well
    p0=db.StringProperty(default="U")
    p1=db.StringProperty(default="L")
    
    path="ensquared"
    name="Ensquared"
    ais=[]
    views=["canvas"]
    norm={"":"canvas"}#normalizes the name of the view
    norm.update({v:v for v in views})
           
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
                if c=="U":y-=1
                elif c=="D":y+=1
                elif c=="L":x-=1
                elif c=="R":x+=1
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
            self.state^=TURN #because the player who crashes loses
            
        
        self.endmove()
        
perpendicular={"U":"LR","D":"LR",
               "L":"UD", "R":"UD"}