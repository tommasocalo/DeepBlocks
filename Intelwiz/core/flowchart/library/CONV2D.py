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

class CONV2D(Node):
    """Convolutional Layer"""
    nodeName = 'Conv2D'
    
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
        self.maxbox = QtWidgets.QCheckBox("MaxPool")
        self.ICLabel = QtWidgets.QLabel('In Channels')
        self.ICLineEdit = QtWidgets.QLineEdit()
        self.ICLabel.setBuddy(self.ICLineEdit)
        self.layout.addWidget(self.ICLabel,0,0)
        self.layout.addWidget(self.ICLineEdit,0,1)
        self.DimLabel = QtWidgets.QLabel('In Dimension')
        self.DimLineEdit = QtWidgets.QLineEdit()
        self.DimLabel.setBuddy(self.DimLineEdit)
        self.layout.addWidget(self.DimLabel,1,0)
        self.layout.addWidget(self.DimLineEdit,1,1)
        self.KerLabel = QtWidgets.QLabel('Kernel Size')
        self.KerLineEdit = QtWidgets.QLineEdit()
        self.KerLabel.setBuddy(self.KerLineEdit)
        self.layout.addWidget(self.KerLabel,2,0)
        self.layout.addWidget(self.KerLineEdit,2,1)
        self.PadLabel = QtWidgets.QLabel('Padding')
        self.PadLineEdit = QtWidgets.QLineEdit()
        self.PadLabel.setBuddy(self.PadLineEdit)
        self.layout.addWidget(self.PadLabel,3,0)
        self.layout.addWidget(self.PadLineEdit,3,1)
        self.layout.addWidget(self.relubox,4,0)
        self.layout.addWidget(self.maxbox,4,1)
        self.MPKLabel = QtWidgets.QLabel('Max Pool Kernel Size')
        self.MPKLineEdit = QtWidgets.QLineEdit()
        self.MPKLabel.setBuddy(self.MPKLineEdit)
        self.layout.addWidget(self.MPKLabel,5,0)
        self.layout.addWidget(self.MPKLineEdit,5,1)
        self.MPSLabel = QtWidgets.QLabel('Max Pool Stride')
        self.MPSLineEdit = QtWidgets.QLineEdit()
        self.MPSLabel.setBuddy(self.MPSLineEdit)
        self.layout.addWidget(self.MPSLabel,6,0)
        self.layout.addWidget(self.MPSLineEdit,6,1)        
        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        
        self.fileNameLabel = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.fileNameLabel,7,0,2,2)


        self.terminals['Input']._refout=self.terminals['Output']    
        self.ICLineEdit.editingFinished.connect(self.enterPressIn)
        self.DimLineEdit.editingFinished.connect(self.enterPressDim)
        self.MPKLineEdit.editingFinished.connect(self.enterPressMP)
        self.KerLineEdit.editingFinished.connect(self.enterPressKer)
        self.PadLineEdit.editingFinished.connect(self.enterPressPad)
        self.MPSLineEdit.editingFinished.connect(self.enterPressMPS)
        self.relubox.toggled.connect(self.onClickedRelu)
        self.maxbox.toggled.connect(self.onClickedDrop)

        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        self.ui.setLayout(self.layout)

        self.in_channels = 0
        self.dim = 0
        self.kernel = 0
        self.pad = 0
        self.maxk = None
        self.maxs = None
        self.relu = False
        self.maxp = False

        self.conv = nn.Conv2d(self.in_channels, self.dim, kernel_size=self.kernel, padding=self.pad)

    def addInput(self, name="Input", **args):
        """Add a new input terminal to this Node with the given name. Extra
        keyword arguments are passed to Terminal.__init__.
        
        This is a convenience function that just calls addTerminal(io='in', ...)"""
        #print "Node.addInput called."
        term1 = self.addTerminal(name, io='in', **args)


    def updateconv(self):
        self.conv = nn.Conv2d(self.in_channels, self.dim, kernel_size=self.kernel, padding=self.pad)
    def onClickedRelu(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.relu=True
        else: 
            self.relu=False
        pass

    def onClickedDrop(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.MPKLineEdit.setEnabled(False)
            self.MPSLineEdit.setEnabled(True)
            self.maxp=True
        else: 
            self.maxp=False
            self.MPKLineEdit.setEnabled(False)
            self.MPSLineEdit.setEnabled(False)

        pass
        
    def getParams(self):
        return self.conv.parameters()
    def enterPressIn(self):
        
        try:
            self.in_features = int(self.ICLineEdit.text())
            self.updateconv()
        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressDim(self):
        try:
            self.dim = int(self.DimLineEdit.text())
            self.updateconv()

        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressMP(self):
        try:
            self.maxk = int(self.MPKLineEdit.text())
            

        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressKer(self):
        try:
            self.kernel = int(self.ICLineEdit.text())
            self.updateconv()
        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressPad(self):
        try:
            self.pad = int(self.DimLineEdit.text())
            self.updateconv()

        except:
            self.fileNameLabel.setText('Only Integers Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterPressMPS(self):
        try:
            self.maxs = float(self.MPKLineEdit.text())
            assert self.dropout_p <=1
            

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
                                    
                        
                        x = self.conv(x)
                        if self.relu:
                            x =nn.ReLU()(x),
                        if self.maxp:
                            x =nn.MaxPool2d(kernel_size=self.maxk, stride=self.maxs)(x)

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
                                    
                        x = self.conv(x)
                        if self.relu:
                            x =nn.ReLU()(x),
                        if self.maxp:
                            x =nn.MaxPool2d(kernel_size=self.maxk, stride=self.maxs)(x)

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
        state['text'] = str(self.text.toPlainText())

        state['in_channels']=self.in_channels 
        state['dim']=self.dim 
        state['kernel']=self.kernel 
        state['pad']=self.pad
        state['maxk']=self.maxk 
        state['maxs']=self.maxs
        state['relu']=self.relu
        state['maxp']=self.maxp 
        state['weights'] = self.conv.weight
        #state['terminals'] = self.saveTerminals()
        return state
        
    def restoreState(self, state):
        Node.restoreState(self, state)
        self.in_channels = state['in_channels']
        
        self.in_channels = state['in_channels']
        self.dim = state['dim']
        self.kernel = state['kernel']
        self.pad = state['pad']
        self.maxk = state['maxk']
        self.maxs = state['maxs']
        self.relu = state['relu']
        self.maxp = state['maxp']

        if self.in_channels  : 
            self.ICLineEdit.setText(self.in_channels)
        if self.dim  : 
            self.DimLineEdit.setText(self.dim)
        if self.maxk  : 
            self.MPKLineEdit.setText(self.maxk)
        if self.kernel  : 
            self.KerLineEdit.setText(self.kernel)
        if self.pad  : 
            self.PadLineEdit.setText(self.pad)
        if self.maxs  : 
            self.MPSLineEdit.setText(self.maxs)

        if self.relu  : 
            self.relubox.setChecked(True)

        if self.maxp  : 
            self.maxbox.setChecked(True)
        if state['weights']:
            self.conv.weight = state['weights']
        self.updateconv()
        self.restoreTerminals(state['terminals'])
        self.update()
