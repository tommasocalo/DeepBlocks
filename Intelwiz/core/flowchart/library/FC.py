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


class FCNode(Node):
    """Fully Connected Layer."""
    nodeName = 'FCNode'
    upLn = QtCore.Signal(object)   # self

    def __init__(self, name):
        Node.__init__(self, name, 
            terminals = {
                'Input': {'io': 'in', 'renamable': False},
                'Output': {'io': 'out', 'renamable': False},
            },
            allowAddInput=True, allowAddOutput=False)
        
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        #self.addInBtn = QtGui.QPushButton('+Input')
        #self.addOutBtn = QtGui.QPushButton('+Output')
        #self.layout.addWidget(self.addInBtn, 0, 0)
        #self.layout.addWidget(self.addOutBtn, 0, 1)
        self.relubox = QtWidgets.QCheckBox("ReLU")
        self.dropbox = QtWidgets.QCheckBox("DropOut")
        self.flatbox = QtWidgets.QCheckBox("Flatten")

        self.ICLabel = QtWidgets.QLabel('In Dimension')
        self.ICLineEdit = QtWidgets.QLineEdit()
        self.ICLabel.setBuddy(self.ICLineEdit)
        self.layout.addWidget(self.ICLabel,0,0)
        self.layout.addWidget(self.ICLineEdit,0,1)
        self.DimLabel = QtWidgets.QLabel('Out Dimension')
        self.DimLineEdit = QtWidgets.QLineEdit()
        self.DimLabel.setBuddy(self.DimLineEdit)
        self.layout.addWidget(self.DimLabel,1,0)
        self.layout.addWidget(self.DimLineEdit,1,1)
        self.layout.addWidget(self.relubox,2,0)
        self.layout.addWidget(self.dropbox,2,1)
        self.MPKLabel = QtWidgets.QLabel('Dropout Probability')
        self.MPKLineEdit = QtWidgets.QLineEdit()
        self.MPKLabel.setBuddy(self.MPKLineEdit)
        self.layout.addWidget(self.MPKLabel,3,0)
        self.layout.addWidget(self.MPKLineEdit,3,1)
        self.layout.addWidget(self.flatbox,4,0)
        self.fileNameLabel = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.fileNameLabel,6,0,2,2)

        self.terminals['Input']._refout=self.terminals['Output']

        self.ICLineEdit.editingFinished.connect(self.enterPressIn)
        self.DimLineEdit.editingFinished.connect(self.enterPressOut)
        self.MPKLineEdit.editingFinished.connect(self.enterPressP)
        self.MPKLineEdit.setEnabled(False)
        self.relubox.toggled.connect(self.onClickedRelu)
        self.dropbox.toggled.connect(self.onClickedDrop)
        self.flatbox.toggled.connect(self.onClickedFlat)
        self.upLn.connect(self.updateLinear)
        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        self.ui.setLayout(self.layout)

        self.in_features = None
        self.out_features = None
        self.dropout_p = None
        self.flat=False
        self.relu = False
        self.drop = False

        self.linear=nn.Linear(in_features=100, out_features=100)



   
    def addInput(self, name="Input", **args):
        """Add a new input terminal to this Node with the given name. Extra
        keyword arguments are passed to Terminal.__init__.
        
        This is a convenience function that just calls addTerminal(io='in', ...)"""
        #print "Node.addInput called."
        term = self.addTerminal(name, io='in', **args)


    def updateLinear(self,ob):
        self.linear = nn.Linear(in_features=ob[0], out_features=ob[1])
        self.update()
    def onClickedRelu(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.relu=True
        else: 
            self.relu=False
        self.update()
        

    def getParams(self):
        return self.linear.parameters()

    def onClickedDrop(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.MPKLineEdit.setEnabled(True)
            self.drop=True
        else: 
            self.drop=False
            self.MPKLineEdit.setEnabled(False)
        self.update()

        
    def onClickedFlat(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.flat=True
        else: 
            self.flat=False
        self.update()
        

    def enterPressIn(self):
        try:
            self.in_features = int(self.ICLineEdit.text())
            if self.out_features:
                self.upLn.emit((self.in_features,self.out_features))
            else:    
                self.fileNameLabel.setText('Specify also out features')
        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressOut(self):
        try:
            self.out_features = int(self.DimLineEdit.text())
            if self.in_features:
                self.upLn.emit((self.in_features,self.out_features))
            else:    
                self.fileNameLabel.setText('Specify also in features')
        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressP(self):
        try:
            self.dropout_p = float(self.MPKLineEdit.text())
            assert self.dropout_p <=1
            self.update()

        except:
            self.fileNameLabel.setText('Only Floating from 0 to 1 \nallowed')
        else:
            self.fileNameLabel.setText('')
    def ctrlWidget(self):
        return self.ui
        
    #def addInput(self):
        #Node.addInput(self, 'input', renamable=True)
        
    #def addOutput(self):
        #Node.addOutput(self, 'output', renamable=True)
        
    def focusOutEvent(self, ev):
        text = str(self.text.toPlainText())
        if text != self.lastText:
            self.lastText = text
            self.update()
        return QtGui.QTextEdit.focusOutEvent(self.text, ev)
        
    def process(self, **arg):
        if 'Input' in arg:
            if arg['Input']!=None:
                x = arg['Input']['value']
                z = arg['Input'].copy()
                del z['value']
                if x != None:
                    try: 
                                    
                        
                        if self.flat:
                            x = x.view(x.size(0), -1)
                        x = self.linear(x),
                        if self.relu:
                            x =nn.ReLU()(x),
                        if self.drop:
                            x =nn.Dropout2d(self.dropout_p)(x)

                    except:
                            print("Error processing node: %s" % self.name())
                            raise
                    z['value']=x[0]
                    return {'Output':z}
            else: 
                return {'Output':None}
        else: 
                return {'Output':None}
    def train(self, **arg):
        if 'Input' in arg:
            if arg['Input']!=None:
                x = arg['Input']['value']
                z = arg['Input'].copy()
                del z['value']
                if x != None:
                    try: 
                                    
                        
                        if self.flat:
                            x = x.view(x.size(0), -1)
                        x = self.linear(x),
                        if self.relu:
                            x =nn.ReLU()(x),
                        if self.drop:
                            x =nn.Dropout2d(self.dropout_p)(x)

                    except:
                            print("Error processing node: %s" % self.name())
                            raise
                z['value']=x[0]
                return {'Output':z}
            else: 
                    return {'Output':None}  
        else: 
                    return {'Output':None}        
    def saveState(self):
        state = Node.saveState(self)
        state['in_features']=self.in_features
        state['out_features']=self.out_features
        state['dropout_p']=self.dropout_p
        state['flat']=self.flat
        state['relu']=self.relu
        state['drop']=self.drop
        #state['linear']=self.linear.weight
        #state['terminals'] = self.saveTerminals()
        return state
        
    def restoreState(self, state):

        Node.restoreState(self, state)
        self.in_features = state['in_features']
        self.out_features = state['out_features']
        self.dropout_p = state['dropout_p']
        self.flat=state['flat']
        self.relu = state['relu']
        self.drop = state['drop']

        if self.in_features  : 
            self.upLn.emit((self.in_features,100))
            self.ICLineEdit.setText(str(self.in_features))
        if self.out_features : 
            self.upLn.emit((100,self.out_features))
            self.DimLineEdit.setText(str(self.out_features))
        if self.out_features and  self.in_features : 
            self.upLn.emit((self.in_features,self.out_features))

            
        if self.dropout_p  : 
            self.MPKLineEdit.setText(str(self.dropout_p))
        if self.flat  : 
            self.flatbox.setChecked(True)

        if self.relu  : 
            self.relubox.setChecked(True)

        if self.drop  : 
            self.dropbox.setChecked(True)

        #self.linear.weight=state['weights']
        self.restoreTerminals(state['terminals'])
        self.update()

