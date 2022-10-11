# -*- coding: utf-8 -*-

# PoC need to take control of libcode
# from pyqtgraph.flowchart.library.common import CtrlNode
# from pyqtgraph.flowchart import Flowchart, Node
# import pyqtgraph.flowchart.library as fclib
from intelwiz.core.flowchart.library.common import CtrlNode
from intelwiz.core.flowchart import Flowchart, Node
import intelwiz.core.flowchart.library as fclib

from pyqtgraph.Qt import QtGui, QtCore
from json import dumps
import urllib3
import torch

app = QtGui.QApplication([])


# Create main window with a grid layout inside
win = QtGui.QMainWindow()
win.setWindowTitle('DeepBlocks')
cw = QtGui.QWidget()
win.setCentralWidget(cw)
layout = QtGui.QGridLayout()
cw.setLayout(layout)

# Create an empty flowchart with a single input and output
fc = Flowchart(terminals={
    'output': {'io': 'out', 'multi': True, 'renamable': True, 'removable': True}
})

# Workaround to remove the default 'Input' node
# fc.removeNode(fc._nodes['Input'])
fc.removeNode(fc._nodes['Output'])

# Flowchart list and control boutons
w = fc.widget()

# TextEdit (for JSON results)
textArea = QtGui.QTextEdit()
textArea.setReadOnly(True)
cursor = QtGui.QTextCursor(textArea.document())
#cursor.insertText("hello world")

# Refresh zone (outputs->JSON)
# button = QtGui.QPushButton('Update JSON')
# def handleButton():
#     textArea.clear()
#     print str(fc.outputNode.inputValues())
#     cursor.insertText(str(dumps(fc.outputNode.inputValues(), indent=4)))
# button.clicked.connect(handleButton)

# GUI stuffs
# w.chartWidget.hoverDock.hide()
# w.chartWidget.selDock.hide()
layout.addWidget(w, 0, 0, 2, 1)
layout.addWidget(w.cwWin, 0, 1, 2, 1)
layout.addWidget(w.modules, 0, 2, 2, 1)
# layout.addWidget(button, 0, 2, 1, 1)
layout.setColumnMinimumWidth(0, 300)
layout.setColumnMinimumWidth(1, 400)
layout.setColumnMinimumWidth(2, 300)

# layout.setColumnMinimumWidth(2, 300)
w.ui.showChartBtn.toggle()
win.show()


class OutputNode(CtrlNode):
    """Computes Loss Function and Optimize Network"""
    nodeName = 'Output'

    def __init__(self, name):
        Node.__init__(self, name,
            terminals = {
                'Result': {'io': 'in', 'renamable': True, 'removable': True},
            },
            allowAddInput=True, allowAddOutput=False, allowRemove=False)

        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.saveBtn = QtGui.QPushButton('Save As..')
        self.saveBtn.setEnabled(False)
        self.showJsonBtn = QtGui.QPushButton('Show JSON')
        self.showJsonBtn.setToolTip("Show Output in JSON format")
        self.showJsonBtn.setCheckable(True)
        # if textArea.x :
        #
        self.showJsonBtn.setChecked(True)
        # if self.showJsonBtn.released ==  True:
        #     self.showJsonBtn.setEnabled(False)
        self.showJsonBtn.clicked.connect(self.showJsonClicked)
        # self.text = QtGui.QTextEdit()
        # self.text.setTabStopWidth(30)
        # self.text.setPlainText("Hello world!")
        self.layout.addWidget(self.showJsonBtn, 0, 0)
        self.layout.addWidget(self.saveBtn, 0, 1)
        # self.layout.addWidget(self.text, 1, 0, 1, 2)
        self.ui.setLayout(self.layout)

        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        # self.text.focusOutEvent = self.focusOutEvent
        # self.lastText = None
        self.lr = 0
        self.opt = None
        self.RS = 0
        self.loss = torch.nn.CrossEntropyLoss() 
        self.opt='SGD'
        self.params=list()
        self.lossTxt=None
        # To force update for all node inputs and ctrls (and launch some requests ...)
        self.optimizer = None
        self.GT=None
        self.test = None
    def updateParams(self,params):
        if self.params == None:
            self.params=list(params)
        else:
            self.params=self.params.append(list(params))
    def showJsonClicked(self):  #TODO Added
        pass
    def get_accuracy(self,predictions, true_labels):
        _, predicted = torch.max(predictions, 1)
        corrects = (predicted == true_labels).sum()
        accuracy = 100.0 * corrects/len(true_labels)
        return accuracy.item()
    def ctrlWidget(self):
        return self.ui
    def setopt(self):
        if self.opt=='SGD':
            self.optimizer =torch.optim.SGD(self.params, lr=self.lr)
        elif self.opt =='ADAM':
            self.optimizer =torch.optim.Adam(self.params, lr=self.lr)
    def setTest(self,test):
        self.test=test
    def train(self, **args):
        if args['Result']!=None:
            if args['Result']['state'] =='test':
                test = self.get_accuracy(args['Result']['value'], args['Result']['labels'])
                return test,'test'
            elif args['Result']['state'] =='train':
                loss = self.loss(args['Result']['value'], args['Result']['labels'])
                accuracy = self.get_accuracy(args['Result']['value'], args['Result']['labels'])
                    
                    # computing gradients
                loss.backward()
                    
                    # changing the weights
                self.optimizer.step()
                self.optimizer.zero_grad()
                #total_batch+=1
                #train_loss += loss.item()
                #train_accuracy += accuracy
                return accuracy,'train'
    def process(self, **args):

        return None
    def setLR(self,lr):
        self.lr = lr
    def setOptim(self,opt):
        self.opt = opt 
    def setRS(self,RS):
        self.RS = RS
    def setGT(self,GT):    
        self.GT = GT    

    def setLoss(self,loss):   
        
        self.loss = loss   
    def setLossTxt(self,losstxt):    
        self.lossTxt = losstxt    
        
    def saveState(self):  # TODO Added
        state = Node.saveState(self)
        # state['json'] = True
        #state['terminals'] = self.saveTerminals()
        return state

    def restoreState(self, state):  # TODO Added
        Node.restoreState(self, state)
        # self.text.clear()
        # self.text.insertPlainText(state['text'])
        # self.restoreTerminals(state['terminals'])
        #self.update()


# We will define an unsharp masking filter node as a subclass of CtrlNode.
# CtrlNode is just a convenience class that automatically creates its
# control widget based on a simple data structure.
class GetSourceNode(CtrlNode):
    """Return the source code behind a website url"""
    nodeName = "GetSource"
    uiTemplate = [
        ('timeout', 'spin', {'value': 3.0, 'dec': True, 'step': 0.5, 'minStep': 0.01, 'range': [0.0, None]}),
        ('retry',  'intSpin', {'value': 0, 'step': 1, 'range': [0, None]}),
    ]

    def __init__(self, name):
        ## Define the input / output terminals available on this node
        terminals = {
            'urlIn': dict(io='in'),    # each terminal needs at least a name and
            'cookieIn': dict(io='in'),
            'urlOut': dict(io='out'),  # to specify whether it is input or output
            'cookieOut': dict(io='out'),
            'source': dict(io='out'),
        }                              # other more advanced options are available
                                       # as well..

        CtrlNode.__init__(self, name, terminals=terminals)
        
    def process(self, urlIn, cookieIn, display=True):
        if urlIn is not None:
            timeout = self.ctrls['timeout'].value()
            retry = self.ctrls['retry'].value()
            # if bypass is None:
            net = Network()
            urlOut, cookieOut, source = net.req(urlIn, cookieIn, timeout, retry)
            # else:
            #     urlOut, cookieOut, source = urlIn, cookieIn, bypass
            return {'urlOut': urlOut, 'cookieOut': cookieOut, 'source': source}


class TextEditNode(Node):
    """Return the output of a string."""
    nodeName = 'TextEdit'

    def __init__(self, name):
        Node.__init__(self, name,
            terminals = {
                'output': {'io': 'out', 'renamable': True},
            },
            allowAddInput=True, allowAddOutput=True)

        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        # self.addInBtn = QtGui.QPushButton('+Input')
        # self.addOutBtn = QtGui.QPushButton('+Output')
        self.text = QtGui.QTextEdit()
        self.text.setTabStopWidth(30)
        self.text.setPlainText("Hello world!")
        # self.layout.addWidget(self.addInBtn, 0, 0)
        # self.layout.addWidget(self.addOutBtn, 0, 1)
        self.layout.addWidget(self.text, 1, 0, 1, 2)
        self.ui.setLayout(self.layout)

        #QtCore.QObject.connect(self.addInBtn, QtCore.SIGNAL('clicked()'), self.addInput)
        #self.addInBtn.clicked.connect(self.addInput)
        #QtCore.QObject.connect(self.addOutBtn, QtCore.SIGNAL('clicked()'), self.addOutput)
        #self.addOutBtn.clicked.connect(self.addOutput)
        self.text.focusOutEvent = self.focusOutEvent
        self.lastText = None

        # To force update for all node inputs and ctrls (and launch some requests ...)
        self.update()

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

    def process(self, display=True):
        if len(str(self.text.toPlainText())):
            return {'output': str(self.text.toPlainText())}
        else:
            return {'output': None}
    def saveState(self):
        state = Node.saveState(self)
        state['text'] = str(self.text.toPlainText())
        #state['terminals'] = self.saveTerminals()
        return state

    def restoreState(self, state):
        Node.restoreState(self, state)
        self.text.clear()
        self.text.insertPlainText(state['text'])
        self.restoreTerminals(state['terminals'])
        self.update()


class Network():
    def req(self, urlIn, cookieIn, timeout, retry):
        #TODO timeout, retry, user-agent spoofer, proxy
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2",}
        if cookieIn is not None:
            headers['Cookie'] = cookieIn
        request = urllib3.Request(urlIn, None, headers)
        urlfile = urllib3.urlopen(request)
        source = urlfile.read()
        urlfile.close()

        cookieOut = urlfile.info().getheader("Set-Cookie")
        if len(cookieOut):
            cookieOut = cookieOut.replace(',',';')
        # print "[i] Cookie : %s" % cookieOut

        return urlIn, cookieOut, source


# register the class so it will appear in the menu of node types.
# It will appear in a new 'Web' and 'Input' sub-menu.

fclib.registerNodeType(GetSourceNode, [('Web',)])
fclib.registerNodeType(TextEditNode, [('Input',)])
fclib.registerNodeType(OutputNode, [])

# Now we will programmatically add nodes to define the function of the flowchart.
# Normally, the user will do this manually or by loading a pre-generated
# flowchart file.

# tNode = fc.createNode('TextEdit', pos=(-150, 0))
# fNode = fc.createNode('GetSource', pos=(0, 0))
# fNode.update()
# fc.inputNode = tNode

# fc.connectTerminals(tNode['output'], fNode['urlIn'])
# fc.connectTerminals(fNode['source'], fc['dataOut'])


# tNode = fc.createNode('TextEdit', pos=(-150, 0))
# fc.inputNode = tNode
# fc.connectTerminals(tNode['output'], fc['dataOut'])

myOutputNode = fc.createNode('Output', pos=(300, 0))
fc.outputNode = myOutputNode

def main():
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    main()
