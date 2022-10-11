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


class XOR(Node):
    """Xor between two inputs."""
    nodeName = 'XOR'
    upLn = QtCore.Signal(object)   # self

    def __init__(self, name):
        Node.__init__(self, name, 
            terminals = {
                'Input0': {'io': 'in', 'renamable': False},
                'Input1': {'io': 'in', 'renamable': False},
                'Output': {'io': 'out', 'renamable': False},
            },
            allowAddInput=True, allowAddOutput=False)
        
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
       
    def ctrlWidget(self):
        return self.ui
        
    #def addInput(self):
        #Node.addInput(self, 'input', renamable=True)
        
    #def addOutput(self):
        #Node.addOutput(self, 'output', renamable=True)
        
    def process(self, **arg):
        z = {}
        for k,v in arg.items():
            if v!=None:
                return {'Output':v}
        return {'Output':None}
        
    def train(self, **arg):
        z = {}
        for k,v in arg.items():
            if v!=None:
                return {'Output':v}
        
        return {'Output':None}
        
           
    def saveState(self):
        state = Node.saveState(self)
        return state
        
    def restoreState(self, state):

        Node.restoreState(self, state)
        #self.linear.weight=state['weights']
        self.restoreTerminals(state['terminals'])
        self.update()

