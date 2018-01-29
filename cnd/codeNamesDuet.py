# !/usr/bin/env python

from tools import *
from game import Game
from random import randrange,shuffle
from google.appengine.api.users import User

from google.appengine.ext import db


class codeNamesDuet(Game):
    """play codenames duet (with a codenames set)"""
    board=db.StringProperty(default=" "*50)

    lastPlayerWins=True
    path="cnd"
    name="Codenames Duet"
    ais = []
    views=["table"]

    def __init__(self,*args,**kwargs):
        super(codeNamesDuet,self).__init__(*args,**kwargs)
        if self.board==" "*50:
            l =(["GW","WG"]*5+["WW"]*7+["BB","WB","BW","BG","GB"]+["GG"]*3)
            shuffle(l)
            self.board = "".join(l)


    def getData(self):
        """returns information about the game in a format suitable to be sent to a client"""
        d=self.dataHeader()
        d.update({"board":self.board})
        #d["board"]="".join(["".join(["".join(y) for y in z]) for z in self.board])
        return d

    def move(self,pl,pos):
        """validates a move then updates the game state"""
        pass

    def checkTime(self):
        return True
