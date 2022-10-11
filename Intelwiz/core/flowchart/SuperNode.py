# -*- coding: utf-8 -*-
from tkinter import N
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
import pyqtgraph.functions as fn
from .Terminal import *
from .SuperTerminal import *
from pyqtgraph.pgcollections import OrderedDict
from pyqtgraph.debug import *
import numpy as np
from .eq import *
from .Node import *
from .Node import NodeGraphicsItem
def strDict(d):
    return dict([(str(k), v) for k, v in d.items()])

class SuperNode(Node):
    
    sigOutputChanged = QtCore.Signal(object)   # self
    sigClosed = QtCore.Signal(object)
    sigRenamed = QtCore.Signal(object, object)
    sigRecolor = QtCore.Signal(object)   

    sigMerge = QtCore.Signal(object)
    sigExp = QtCore.Signal(object)
    sigSave = QtCore.Signal(object)
    sigExc = QtCore.Signal(object)   

    sigTerminalRenamed = QtCore.Signal(object, object)  # term, oldName
    sigTerminalAdded = QtCore.Signal(object, object)  # self, term
    sigTerminalRemoved = QtCore.Signal(object, object)  # self, term

    def __init__(self, name, level, subnodes, terminals=None, allowAddInput=False, allowAddOutput=False, allowRemove=True,allowMergeNodes=False,allowExpandNodes=True):
        QtCore.QObject.__init__(self)
        self.subnodes = subnodes
        self.level=level
        self.terminals = OrderedDict()
        self._inputs = OrderedDict()
        self._outputs = OrderedDict()
        self._allowAddInput = False   ## flags to allow the user to add/remove terminals
        self._allowAddOutput = False
        self._allowRemove = allowRemove
        self._allowMergeNodes = allowMergeNodes
        self._allowExpandNodes=allowExpandNodes
        self.exception = None
        self._graphicsItem = None
        self._name = name
        self._nested=False

        self._bypass = False
        self.bypassButton = None  ## this will be set by the flowchart ctrl widget..
        self._freeze = False #TODO added
        self.freezeButton = None  ## this will be set by the flowchart ctrl widget..
        for n in self.subnodes:
            n.sigRecolor.connect(self.recolor)
        for n in self.subnodes:
            n.sigExc.connect(self.setException)
        self.initC()
        if terminals is None:
            return
        for name, opts in terminals.items():
            self.addTerminal(name, **opts)


    def initC(self):
        i = 1
        for n in self.subnodes:
            
            if  n.isFreezed():
                i += 1
            if n.exception != None:
                i *= 0
                self.setException(n.exception)
        if i == 1:
            self.graphicsItem().setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        elif i >1:
            self.graphicsItem().setPen(QtGui.QPen(QtGui.QColor(0, 128, 255), 3))
        elif i == 0:
            self.graphicsItem().setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 3))
    def removeTerminal(self, term):
        """Remove the specified terminal from this Node. May specify either the 
        terminal's name or the terminal itself.
        
        Causes sigTerminalRemoved to be emitted."""
        if isinstance(term, SuperTerminal):
            name = term.name()
        else:
            name = term
            term = self.terminals[name]
        
        #print "remove", name
        #term.disconnectAll()
        term.close()
        del self.terminals[name]
        if name in self._inputs:
            del self._inputs[name]
        if name in self._outputs:
            del self._outputs[name]
        self.graphicsItem().updateTerminals()
        self.sigTerminalRemoved.emit(self, term)
        
        
    def terminalRenamed(self, term, oldName):
        """Called after a terminal has been renamed        
        
        Causes sigTerminalRenamed to be emitted."""
        newName = term.name()
        for d in [self.terminals, self._inputs, self._outputs]:
            if oldName not in d:
                continue
            d[newName] = d[oldName]
            del d[oldName]
            
        self.graphicsItem().updateTerminals()
        self.sigTerminalRenamed.emit(term, oldName)
        
    def addTerminal(self, name, **opts):
        """Add a new terminal to this Node with the given name. Extra
        keyword arguments are passed to Terminal.__init__.
                
        Causes sigTerminalAdded to be emitted."""
        name = name
        term = SuperTerminal(self, name, **opts)
        self.terminals[name] = term
        if term.isInput():
            self._inputs[name] = term
        elif term.isOutput():
            self._outputs[name] = term
        self.graphicsItem().updateTerminals()
        self.sigTerminalAdded.emit(self, term)
        return term

        
    def inputs(self):
        """Return dict of all input terminals.
        Warning: do not modify."""
        return self._inputs
        
    def outputs(self):
        """Return dict of all output terminals.
        Warning: do not modify."""
        return self._outputs
        
    def process(self, **kargs):
        """Process data through this node. This method is called any time the flowchart 
        wants the node to process data. It will be called with one keyword argument
        corresponding to each input terminal, and must return a dict mapping the name
        of each output terminal to its new value.
        
        This method is also called with a 'display' keyword argument, which indicates
        whether the node should update its display (if it implements any) while processing
        this data. This is primarily used to disable expensive display operations
        during batch processing.
        """
        return {}
    
    def graphicsItem(self):
        """Return the GraphicsItem for this node. Subclasses may re-implement
        this method to customize their appearance in the flowchart."""
        if self._graphicsItem is None:
            self._graphicsItem = NodeGraphicsItem(self)
        return self._graphicsItem
    
    ## this is just bad planning. Causes too many bugs.
    def __getattr__(self, attr):
        """Return the terminal with the given name"""
        if attr not in self.terminals:
            raise AttributeError(attr)
        else:
            import traceback
            traceback.print_stack()
            print("Warning: use of node.terminalName is deprecated; use node['terminalName'] instead.")
            return self.terminals[attr]
            
    def __getitem__(self, item):
        #return getattr(self, item)
        """Return the terminal with the given name"""
        if item not in self.terminals:
            raise KeyError(item)
        else:
            return self.terminals[item]
            
    def name(self):
        """Return the name of this node."""
        return self._name

    def rename(self, name):
        """Rename this node. This will cause sigRenamed to be emitted."""
        oldName = self._name
        self._name = name
        #self.emit(QtCore.SIGNAL('renamed'), self, oldName)
        self.sigRenamed.emit(self, oldName)

    def dependentNodes(self):
        """Return the list of nodes which provide direct input to this node"""
        nodes = set()
        for t in self.inputs().values():
            nodes |= set([i.node() for i in t.inputTerminals()])
        return nodes
        #return set([t.inputTerminals().node() for t in self.listInputs().itervalues()])
        
    def __repr__(self):
        return "<Node %s @%x>" % (self.name(), id(self))
        
    def ctrlWidget(self):
        """Return this Node's control widget. 
        
        By default, Nodes have no control widget. Subclasses may reimplement this 
        method to provide a custom widget. This method is called by Flowcharts
        when they are constructing their Node list."""
        return None

    def bypass(self, byp):
        """Set whether this node should be bypassed.
        
        When bypassed, a Node's process() method is never called. In some cases,
        data is automatically copied directly from specific input nodes to 
        output nodes instead (see the bypass argument to Terminal.__init__). 
        This is usually called when the user disables a node from the flowchart 
        control panel.
        """
        self._bypass = byp
        for node in self.subnodes:
            node.bypass(byp)
        if self.bypassButton is not None:
            self.bypassButton.setChecked(byp)


    def freeze(self, freeze):
        """Set whether this node should be freezed.

        When freezed, a Node's process() method is never called.
        This is usually called when the user freeze a node from the flowchart
        control panel.
        """
        self._freeze = self.processFreezed() if freeze else False #TODO Added
        for node in self.subnodes:
            node.freeze(freeze)
        if self.freezeButton is not None:
            self.freezeButton.setChecked(freeze)
        self.recolor()
        
    def isBypassed(self):
        """Return True if this Node is currently bypassed."""
        return self._bypass

    def isFreezed(self): #TODO added
        """Return True if this Node is currently freezed."""
        return True if self._freeze else False

    def setInput(self, **args):
        pass
        
    def inputValues(self):
        """Return a dict of all input values currently assigned to this node."""
        vals = {}
        for n, t in self.inputs().items():
            vals[n] = t.value()
        return vals
            
    def outputValues(self):
        """Return a dict of all output values currently generated by this node."""
        vals = {}
        for n, t in self.outputs().items():
            vals[n] = t.value()
        return vals
            
    def connected(self, localTerm, remoteTerm):
        """Called whenever one of this node's terminals is connected elsewhere."""
        pass
    
    def disconnected(self, localTerm, remoteTerm):
        """Called whenever one of this node's terminals is disconnected from another."""
        pass 
    
    def update(self, signal=True):
        """Collect all input values, attempt to process new output values, and propagate downstream.
        Subclasses should call update() whenever thir internal state has changed
        (such as when the user interacts with the Node's control widget). Update
        is automatically called when the inputs to the node are changed.
        """
        pass

    def processFreezed(self): #TODO added
        pass

    def setOutput(self, **vals):
        self.setOutputNoSignal(**vals)
        #self.emit(QtCore.SIGNAL('outputChanged'), self)  ## triggers flowchart to propagate new data
        self.sigOutputChanged.emit(self)  ## triggers flowchart to propagate new data

    def setOutputNoSignal(self, **vals):
        for k, v in vals.items():
            term = self.outputs()[k]
            term.setValue(v)
            #targets = term.connections()
            #for t in targets:  ## propagate downstream
                #if t is term:
                    #continue
                #t.inputChanged(term)
            term.setValueAcceptable(True)

    def setException(self, exc):
        self.exception = exc
        self.sigExc.emit(exc)
        
    def clearException(self):
        self.setException(None)
        

                
    def recolor(self,color):
         
            self.graphicsItem().setPen(color)
            self.sigRecolor.emit(color)

        


    def saveState(self):
        """Return a dictionary representing the current state of this node
        (excluding input / output values). This is used for saving/reloading
        flowcharts. The default implementation returns this Node's position,
        bypass state, and information about each of its terminals.
        
        Subclasses may want to extend this method, adding extra keys to the returned
        dict."""
        pos = self.graphicsItem().pos()
        state = {'pos': (pos.x(), pos.y()), 'bypass': self.isBypassed(), 'freeze': self._freeze} #TODO Added


        state['subnodes'] = self.getSubNTree(self.subnodes)
        state['level'] = self.level
        state['nested'] = self._nested
        return state

    def getSubNTree(self,list):
        dic = {}
        for n in list:
            name = n._name
            dic[name] =  OrderedDict()
            if isinstance(n,SuperNode):  
                dic[name]['level'] = n.level            
                dic[name]['subnodes'] = self.getSubNTree(n.subnodes)
        return dic


    def restoreState(self, state):
        """Restore the state of this node from a structure previously generated
        by saveState(). """
        pos = state.get('pos', (0,0))
        freeze = state.get('freeze', False)
        self._freeze = freeze
        self.graphicsItem().setPos(*pos)
        self.bypass(state.get('bypass', False))
        self.freeze(True if freeze else False) #TODO Added
        self._freeze = freeze
        if freeze:
            self.setOutput(**freeze)
        if 'terminals' in state:
            self.restoreTerminals(state['terminals'])

    def saveTerminals(self):
        terms = OrderedDict()
        for n, t in self.terminals.items():
            terms[n] = (t.saveState())
        return terms
        
    def restoreTerminals(self, state):
        for name in list(self.terminals.keys()):
            if name not in state:
                self.removeTerminal(name)
        for name, opts in state.items():
            if name in self.terminals:
                term = self[name]
                term.setOpts(**opts)
                continue
            try:
                opts = strDict(opts)
                self.addTerminal(name, **opts)
            except:
                printExc("Error restoring terminal %s (%s):" % (str(name), str(opts)))
                
        
    def clearTerminals(self):
        for t in self.terminals.values():
            t.close()
        for node in self.subnodes:
            for t in node.terminals.values():
                t.close()
            node.terminals = OrderedDict()
            node._inputs = OrderedDict()
            node._outputs = OrderedDict()
        self.terminals = OrderedDict()
        self._inputs = OrderedDict()
        self._outputs = OrderedDict()        
    def close(self,clear):
        """Cleans up after the node--removes terminals, graphicsItem, widget"""
        if not clear:
            for node in self.subnodes: 

                node.close()
                #self.emit(QtCore.SIGNAL('closed'), self)

        self.disconnectAll(clear)
        self.clearTerminals()
        item = self.graphicsItem()
        if item.scene() is not None:
            item.scene().removeItem(item)
        self._graphicsItem = None
        w = self.ctrlWidget()
        if w is not None:
            w.setParent(None)
        #self.emit(QtCore.SIGNAL('closed'), self)
        self.sigClosed.emit(self)

    def expand(self):
        """Cleans up after the node--removes terminals, graphicsItem, widget"""
        outcon=[]
        incon =[]
        for term in self.terminals.values():
            if term.isInput() and len(term._connections)>0:
                conn = list(term._connections.values())[0]
                incon.append((conn.source.term,term._refterm))
            if term.isOutput() and len(term._connections)>0:
                conn = list(term._connections.values())[0]
                outcon.append((term._refterm,conn.target.term))

        for node in self.subnodes:
                node.graphicsItem().show()

        for node in self.subnodes:
                for term in node.terminals.values():
                    term.graphicsItem().show()
                    for conn in term.connections().values():

                        if conn.source.isVisible() and conn.target.isVisible():
                            conn.show()
                
        item = self.graphicsItem()
        if item.scene() is not None:
            item.scene().removeItem(item)

        for term in self.terminals.values():
                 for k,conn in term.connections().items():
                    conn.hide()
                    conn.close()
                 for k,conn in term._supercon.values():
                    conn.hide()
                    conn.close()
        cons = set(outcon +incon )

        for inc,out in cons: 
            if inc not in out.connections():         
                if isinstance(inc,Terminal):
                    out.connectTo(inc).show()
                else:
                    inc.connectTo(out).show()

        
        #self.emit(QtCore.SIGNAL('closed'), self)
        self._graphicsItem = None

    def disconnectAll(self,clear):
        if clear:
            for node in self.subnodes: 
                if isinstance(node,SuperNode):
                    node.close(clear)
                else:
                    node.close()
        for t in self.terminals.values():
            t.disconnectAll()
    


