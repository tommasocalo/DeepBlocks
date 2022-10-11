# -*- coding: utf-8 -*-
from ..Node import Node
from pyqtgraph.Qt import QtGui, QtCore,QtWidgets
import numpy as np
from .common import *
from pyqtgraph.SRTTransform import SRTTransform
from pyqtgraph.Point import Point
from pyqtgraph.widgets.TreeWidget import TreeWidget
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem

from . import functions
import numpy as np
import torch.nn as nn
from ..Terminal import *
import torch

class Concat(Node):
    """Xor between two inputs."""
    nodeName = 'Concat'
    upLn = QtCore.Signal(object)   # self

    def __init__(self, name):
        Node.__init__(self, name, 
            terminals = {
                'Input0': {'io': 'in', 'renamable': False},
                'Input1': {'io': 'in', 'renamable': False},
                'Output': {'io': 'out', 'renamable': False},
            },
            allowAddInput=False, allowAddOutput=False)
        
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        
    def ctrlWidget(self):
        return self.ui
        
    #def addInput(self):
        #Node.addInput(self, 'input', renamable=True)
        
    #def addOutput(self):
        #Node.addOutput(self, 'output', renamable=True)
        
    def process(self, **arg):
        j = []
        
        for k,v in arg.items():
            
            if v!=None:
                if not any(v['value'] is d_ for d_ in j):
                    j.append(v['value'])

        if len(j)==1:
            return {'Output':{"value":j[0],"state":"proc"}}
        elif len(j)>1:
            return {'Output':{"value":torch.cat(j,dim=0),"state":"proc"}}
        else:
            return {'Output':None}

    def train(self, **arg):
        j = []
        for k,v in arg.items():
            if v!=None:
                if not any(v['value'] is d_ for d_ in j):
                    j.append(v['value'])
        if len(j)==1:
            return {'Output':j[0]}
        elif len(j)>1:
            return {'Output':torch.cat(j)}
        else:
            return {'Output':None}

        
           
    def saveState(self):
        state = Node.saveState(self)
        return state
        
    def restoreState(self, state):

        Node.restoreState(self, state)
        #self.linear.weight=state['weights']
        self.restoreTerminals(state['terminals'])
        self.update()

