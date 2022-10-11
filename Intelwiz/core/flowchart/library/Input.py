# -*- coding: utf-8 -*-
from ..Node import Node
from pyqtgraph.Qt import QtGui, QtCore,QtWidgets
import numpy as np
from .common import *
from pyqtgraph.SRTTransform import SRTTransform
from pyqtgraph.Point import Point
from pyqtgraph.widgets.TreeWidget import TreeWidget
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem
import pyqtgraph as pg
import torch
from . import functions
from .CustomDialog import CustomDialog 
import pandas as pd
from torch.autograd import Variable
from sklearn.model_selection import train_test_split
import copy

class InputNode(Node):
    """Return the output of a string evaluated/executed by the python interpreter.
    The string may be either an expression or a python script, and inputs are accessed as the name of the terminal. 
    For expressions, a single value may be evaluated for a single output, or a dict for multiple outputs.
    For a script, the text will be executed as the body of a function."""
    nodeName = 'Input'
    
    def __init__(self, name):
        Node.__init__(self, name, 
            terminals = {
               
                'Output': {'io': 'out', 'renamable': False},
            },
            allowAddInput=False, allowAddOutput=True)
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        #self.addInBtn = QtGui.QPushButton('+Input')
        #self.addOutBtn = QtGui.QPushButton('+Output')


        self.dataLabel = QtWidgets.QLabel('No Dataset')
        self.addDatabtn= QtWidgets.QPushButton('Add Data...')

        self.trainPerLabel = QtWidgets.QLabel('Val%')
        self.TPLineEdit = QtWidgets.QLineEdit()
        self.trainPerLabel.setBuddy(self.TPLineEdit)
        self.testPerLabel = QtWidgets.QLabel('Test%',)
        self.TePLineEdit = QtWidgets.QLineEdit()
        self.testPerLabel.setBuddy(self.TePLineEdit)


        self.noiseLabel = QtWidgets.QLabel('Noise Dim',)
        self.noiseLineEdit = QtWidgets.QLineEdit()
        self.noiseLabel.setBuddy(self.noiseLineEdit)
        self.orderLabel = QtWidgets.QLabel('Order',)
        self.orderLineEdit = QtWidgets.QLineEdit()
        self.orderLabel.setBuddy(self.orderLineEdit)




        self.btnNoise = QtWidgets.QCheckBox("Noise")
        self.btnInference = QtWidgets.QCheckBox("Inference")
        self.custombtn= QtWidgets.QPushButton('Custom Preprocess')
        self.preprocessBtn= QtWidgets.QPushButton('Preprocess')

        #self.layout.addWidget(self.addInBtn, 0, 0)
        #self.layout.addWidget(self.addOutBtn, 0, 1)
        self.layout.addWidget(self.btnNoise,0,0,1,1)
        self.layout.addWidget(self.btnInference,0,1,1,1)

        self.layout.addWidget(self.noiseLabel,1,0,1,1)
        self.layout.addWidget(self.noiseLineEdit,1,1,1,1)

        self.layout.addWidget(self.dataLabel,2,0,1,1)
        self.layout.addWidget(self.addDatabtn,2,1,1,1)
        self.layout.addWidget(self.orderLabel,3,0,1,1)
        self.layout.addWidget(self.orderLineEdit,3,1,1,1)
        self.layout.addWidget(self.trainPerLabel,5,0,1,1)
        self.layout.addWidget(self.TPLineEdit ,5,1,1,1)
        self.layout.addWidget(self.testPerLabel,4,0,1,1)
        self.layout.addWidget(self.TePLineEdit ,4,1,1,1)
        self.layout.addWidget(self.preprocessBtn, 6, 0, 1, 2)
        self.layout.addWidget(self.custombtn, 7, 0, 1, 2)

        self.fileNameLabel = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.addWidget(self.fileNameLabel,8,0,2,2)
        self.ui.setLayout(self.layout)
        
        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        self.lastText = None
        self.dataPath = None
        self.testP = None
        self.trainP = None
        self.noisD = None

        self.isNoise = False
        self.isInference = False

        self.flat=False
        self.relu = False
        self.BS = 32
        self.drop = False
        self.GT = None
        
        self.startDir=None
        self.fileName=None
        self.dlg = CustomDialog()
        self.noiseLineEdit.editingFinished.connect(self.enternoiseD)

        self.TPLineEdit.editingFinished.connect(self.entertrainPer)
        self.TePLineEdit.editingFinished.connect(self.entertestPer)
        self.orderLineEdit.editingFinished.connect(self.enterorder)

        self.noiseLineEdit.setEnabled(False)
        self.orderLineEdit.setText('0')
        self.btnNoise.toggled.connect(self.onClickednois)
        self.btnInference.toggled.connect(self.onClickedinf)
        self.addDatabtn.clicked.connect(self.addData)
        self.custombtn.clicked.connect(self.textdlg)
        self.preprocessBtn.clicked.connect(self.preprocess)
        self.currOrder=0
        self.totOrder=0
        self.order=[0]
        self.datas = None
        self.dataiter = None

    def textdlg(self):
        self.preprocessBtn.setEnabled(True)
        if self.dlg.exec():
            self.lastText=self.dlg.text.toPlainText()
            

    def addData(self):
        self.loadFile()

    def loadFile(self,fileName = None , startDir=None):
        if fileName is None:
            if startDir is None:
                startDir = '.'
            self.fileDialog = pg.FileDialog(None, "Load Flowchart..", startDir, None)
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            #self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.savefile)
            return
            ## NOTE: was previously using a real widget for the file dialog's parent, but this caused weird mouse event bugs..
            #fileName = QtGui.QFileDialog.getOpenFileName(None, "Load Flowchart..", startDir, "Flowchart (*.fc)")
        
    def savefile(self,file):
        self.fileName = str(file)
        self.dataLabel.setText(self.fileName.split('/')[-1])

    def onClickedinf(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.addDatabtn.setEnabled(True)

            self.TPLineEdit.setEnabled(False)
            self.TePLineEdit.setEnabled(False)
            self.ValLineEdit.setEnabled(False)
            self.isInference=True
        else: 
            self.isInference=False
            self.TPLineEdit.setEnabled(True)
            self.TePLineEdit.setEnabled(True)
            self.ValLineEdit.setEnabled(True)
        
    def onClickednois(self):
        cbutton = self.sender()
        if cbutton.isChecked():
            self.addDatabtn.setEnabled(False)
            self.noiseLineEdit.setEnabled(True)
            self.TPLineEdit.setEnabled(False)
            self.TePLineEdit.setEnabled(False)
            self.ValLineEdit.setEnabled(False)
            self.isNoise=True
        else: 
            self.addDatabtn.setEnabled(True)
            self.isNoise=False
            self.noiseLineEdit.setEnabled(False)
            self.TPLineEdit.setEnabled(True)
            self.TePLineEdit.setEnabled(True)
            self.ValLineEdit.setEnabled(True)
    def setBS(self,bs):
        self.BS = bs
        self.preprocessBtn.setEnabled(True)

    def enternoiseD(self):
        try:
            self.noisD = int(self.noiseLineEdit.text())
            
        except:
            self.fileNameLabel.setText('Only Int Allowed')
        else:
            self.fileNameLabel.setText('')
    def entertrainPer(self):
        try:
            self.trainP = int(self.TPLineEdit.text())
            self.preprocessBtn.setEnabled(True)

            
        except:
            self.fileNameLabel.setText('Only Int Allowed')
        else:
            self.fileNameLabel.setText('')
    def enterorder(self):
        try:
            spl = str(self.orderLineEdit.text()).split(',')
            self.order = []
            if len(spl)>1:
                for el in spl:
                     self.order.append(int(el)) 
            elif len(spl)==1:
                self.order.append(int(spl[0])) 
            else:
                raise
            
        except:
            self.fileNameLabel.setText('Only Int,Int.. Allowed')
        else:
            self.fileNameLabel.setText('')
    def entertestPer(self):
        try:
            self.testP = int(self.TePLineEdit.text())
            self.preprocessBtn.setEnabled(True)

            
        except:
            self.fileNameLabel.setText('Only Int Allowed')
        else:
            self.fileNameLabel.setText('')
  
    def ctrlWidget(self):
        return self.ui
        
    #def addInput(self):
        #Node.addInput(self, 'input', renamable=True)
        
    #def addOutput(self):
        #Node.addOutput(self, 'output', renamable=True)

    def preprocess(self):

        if self.isNoise:
            self.datas = Variable(torch.randn(self.BS, self.noisD))
            return self.datas
        ## try eval first, then exec
        if self.lastText:
            try:
                out=None
                fn = "def fn(**args):\n"
                run = "\nout=fn(**args)\n"
                text = fn + "\n".join(["    "+l for l in str(self.lastText).split('\n')]) + run

                exec(text, globals())
                self.datas = out
            except:
                print("Error processing node: %s" % self.name())
                raise
        else:
            data = pd.read_csv(self.fileName)
            target = data['label']
            del data['label']
            val,val_label = np.array([]),np.array([])
            test,test_label = np.array([]),np.array([])

            if not self.testP and not self.trainP:
                train,train_label = data.to_numpy(),target.to_numpy()
            if self.testP:
                train,test,train_label,test_label=train_test_split(data.to_numpy(),target.to_numpy(), test_size= self.testP/100 ,random_state=42)
            if self.trainP:
                train,val,train_label,val_label=train_test_split(train,train_label, test_size= self.trainP/100 ,random_state=42)
            train_tensor = torch.as_tensor(train).type(torch.FloatTensor).view(-1,28, 28)
            train_label = torch.as_tensor(train_label)

            test_tensor = torch.as_tensor(test).type(torch.FloatTensor).view(-1,28, 28)
            test_label = torch.as_tensor(test_label)
            val_tensor = torch.as_tensor(val).type(torch.FloatTensor).view(-1,28, 28)
            val_label = torch.as_tensor(val_label)
            train_dataset = torch.utils.data.TensorDataset(train_tensor, train_label)
            trainloader = torch.utils.data.DataLoader(train_dataset, batch_size = self.BS, shuffle = True)
            rnd = torch.utils.data.DataLoader(train_dataset, batch_size = self.BS, shuffle = True)

            self.datas = trainloader,[test_tensor,test_label],[val_tensor,val_label]
            self.dataiter = {}
            self.size= next(iter(rnd))[0].size()
            self.preprocessBtn.setEnabled(False)
            self.update()
            return 
    def process(self,**args):
        if not self.isNoise:
            return {'Output':{'value':torch.randn(self.size),'state':'proc'}}
        else:
            return {'Output':{'value':torch.randn(self.noisD),'state':'proc'}}
    def init_inputs(self,orders):
        self.totOrder = max(orders)
        for o in orders:
            self.dataiter[o] = iter(copy.deepcopy(self.datas[0]))

    def train(self,**args):
        
        if self.currOrder not in self.order:
            oldorder = self.currOrder
            if self.currOrder   == self.totOrder:
                self.currOrder = 0
            else:
                self.currOrder = self.currOrder +1  
            return {'Output':None}
        else:
            oldorder = self.currOrder
            if self.currOrder  == self.totOrder:
                self.currOrder = 0
            else:
                self.currOrder = self.currOrder +1  

            if not self.isNoise:

                value,labels = next(self.dataiter[oldorder],(None,None))
                if (value,labels)==(None,None):
                        return {'Output':{'value':self.datas[1][0],'labels':self.datas[1][1],'state':'test','order':oldorder}}
                else:
                    return {'Output':{'value':value,'labels':labels,'state':'train','order':oldorder}}
            else:
                return {'Output':{'value':torch.randn(self.noisD),'labels':torch.ones(self.noisD),'state':'train','order':oldorder}}
    def saveState(self):
        state = Node.saveState(self)
        state['text'] = self.lastText
        state['dataPath']= self.dataPath
        state['testP'] = self.testP
        state['trainP'] = self.trainP
        state['noisD']= self.noisD
        state['isNoise'] = self.isNoise
        state['isInference']= self.isInference
        state['relu'] = self.relu
        state['drop']= self.drop
        state['startDir'] = self.startDir
        state['fileName']= self.fileName
        state['flat']=self.flat
        #state['terminals'] = self.saveTerminals()
        return state
        
    def restoreState(self, state):
        Node.restoreState(self, state)
        self.lastText=state['text']
        self.dlg.text.setText(self.lastText)
        self.dataPath = state['dataPath']
        

        self.testP = state['testP']
        self.trainP = state['trainP']

        self.TPLineEdit.setText(str(self.trainP))
        self.TePLineEdit.setText(str(self.testP))
        self.noisD = state['noisD']
        self.noiseLineEdit.setText(state['noisD'])
        self.isNoise = state['isNoise']
        if self.isNoise:
            self.btnNoise.setChecked(True)

            self.addDatabtn.setEnabled(False)
            self.noiseLineEdit.setEnabled(True)
            self.TPLineEdit.setEnabled(False)
            self.TePLineEdit.setEnabled(False)
            self.ValLineEdit.setEnabled(False)
        self.isInference = state['isInference']
        if self.isInference:
            self.btnInference.setChecked(True)
            self.addDatabtn.setEnabled(True)
            self.TPLineEdit.setEnabled(False)
            self.TePLineEdit.setEnabled(False)
            self.ValLineEdit.setEnabled(False)

        self.flat=state['flat']
        self.relu = state['relu']
        self.drop = state['drop']
        
        self.startDir=state['startDir']
        self.fileName=state['fileName']
        self.savefile(self.fileName)
        self.restoreTerminals(state['terminals'])
        self.preprocess()

