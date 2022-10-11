# -*- coding: utf-8 -*-
from time import sleep
from pyqtgraph.Qt import QtCore, QtGui
import weakref
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
import pyqtgraph.functions as fn
from pyqtgraph.Point import Point
#from PySide import QtCore, QtGui
from .eq import *
from .Terminal import TerminalGraphicsItem,ConnectionItem
class SuperTerminal(object):
    def __init__(self, node, name,refterm, io, optional=False, multi=True, pos=None, renamable=False, removable=False, multiable=False, bypass=None):
        """
        Construct a new terminal. 
        
        ==============  =================================================================================
        **Arguments:**
        node            the node to which this terminal belongs
        name            string, the name of the terminal
        io              'in' or 'out'
        optional        bool, whether the node may process without connection to this terminal
        multi           bool, for inputs: whether this terminal may make multiple connections
                        for outputs: whether this terminal creates a different value for each connection
        pos             [x, y], the position of the terminal within its node's boundaries
        renamable       (bool) Whether the terminal can be renamed by the user
        removable       (bool) Whether the terminal can be removed by the user
        multiable       (bool) Whether the user may toggle the *multi* option for this terminal
        bypass          (str) Name of the terminal from which this terminal's value is derived
                        when the Node is in bypass mode.
        ==============  =================================================================================
        """
        self._io = io
        #self._isOutput = opts[0] in ['out', 'io']
        #self._isInput = opts[0]] in ['in', 'io']
        #self._isIO = opts[0]=='io'
        self._optional = optional
        self._multi = multi
        self._node = weakref.ref(node)
        self._name = name
        self._renamable = renamable
        self._removable = removable
        self._multiable = multiable
        self._connections = {}
        self._graphicsItem = TerminalGraphicsItem(self, parent=self._node().graphicsItem())
        self._bypass = bypass
        self._refterm = refterm 
        self.last = self.lastref(refterm)
        self._supercon={}

        self.color = None
        if multi:
            self._value = {}  ## dictionary of terminal:value pairs.
        else:
            self._value = None  
        
        self.valueOk = None
        self.recolor()
    def lastref(self,ter):
        if ter._refterm!=None:
            return self.lastref(self,ter)
        else:
             return ter
    def value(self, term=None):
        """Return the value this terminal provides for the connected terminal"""
        if term is None:
            return self._value
            
        if self.isMultiValue():
            return self._value.get(term, None)
        else:
            return self._value

    

    def bypassValue(self):
        return self.refterm()._bypass

    def setValue(self, val, process=True):
        if self._refterm._refterm!= None:
            self._refterm.setValue(val, process=process)
        
        
    def setOpts(self, **opts):
        self._renamable = opts.get('renamable', self._renamable)
        self._removable = opts.get('removable', self._removable)
        self._multiable = opts.get('multiable', self._multiable)
        if 'multi' in opts:
            self.setMultiValue(opts['multi'])
        

    def connected(self, term):
        if self.isInput() and term.isOutput():
            self.inputChanged(term)
        self.node().connected(self, term)
        
    def disconnected(self, term):
        """Called whenever this terminal has been disconnected from another. (note--this function is called on both terminals)"""
        self.node().disconnected(self, term)
        #self.node().update()

    def inputChanged(self, term, process=True):
        self._refterm.setValue(term.value(self), process=process)
        pass
            
    def valueIsAcceptable(self):
        """Returns True->acceptable  None->unknown  False->Unacceptable"""
        return self.valueOk
        
    def setValueAcceptable(self, v=True):
        self.valueOk = v
        self.recolor()
        
    def connections(self):
        return self._connections
        
    def node(self):
        return self._node()
        
    def isInput(self):
        return self._io == 'in'
    
    def isMultiValue(self):
        return self._multi
    
    def setMultiValue(self, multi):
        """Set whether this is a multi-value terminal."""
        self._multi = multi
        if not multi and len(self.inputTerminals()) > 1:
            self.disconnectAll()
            
        for term in self.inputTerminals():
            self.inputChanged(term)

    def isOutput(self):
        return self._io == 'out'
        
    def isRenamable(self):
        return self._renamable

    def isRemovable(self):
        return self._removable

    def isMultiable(self):
        return self._multiable

    def name(self):
        return self._name

    def refterm(self):
        return self._refterm

    def graphicsItem(self):
        return self._graphicsItem
        
    def isConnected(self):
        return len(self.connections()) > 0
        
    def connectedTo(self, term):
        return term in self.connections()
        
    def hasInput(self):
        #conn = self.extendedConnections()
        for t in self.connections():
            if t.isOutput():
                return True
        return False        
        
    def inputTerminals(self):
        """Return the terminal(s) that give input to this one."""
        #terms = self.extendedConnections()
        #for t in terms:
            #if t.isOutput():
                #return t
        return [t for t in self.connections() if t.isOutput()]
                
        
    def dependentNodes(self):
        """Return the list of nodes which receive input from this terminal."""
        #conn = self.extendedConnections()
        #del conn[self]
        return set([t.node() for t in self.connections() if t.isInput()])
        

    def connectTo(self, term, connectionItem=None):
        try:
            if self.connectedTo(term) or term.connectedTo(self):
                raise Exception('Already connected')
            if term is self:
                raise Exception('Not connecting terminal to self')
            if term.node() is self.node():
                raise Exception("Can't connect to terminal on same node.")
            #if self.hasInput() and term.hasInput():
                #raise Exception('Target terminal already has input')
            
            #if term in self.node().terminals.values():
                #if self.isOutput() or term.isOutput():
                    #raise Exception('Can not connect an output back to the same node.')
        except:
            if connectionItem is not None:
                connectionItem.close()
            raise
        if self.isInput():
            into = term.graphicsItem()
            out = self.graphicsItem()
        else:
            out = term.graphicsItem()
            into = self.graphicsItem()            
        if connectionItem is None:
            connectionItem = ConnectionItem(into, out)
            #self.graphicsItem().scene().addItem(connectionItem)
            self.graphicsItem().getViewBox().addItem(connectionItem)
            #connectionItem.setParentItem(self.graphicsItem().parent().parent())
        self._connections[term] = connectionItem
        if term._refterm==None:
            term._supercon[self] = connectionItem
        else:
            term._connections[self] = connectionItem
        
        
        #if self.isOutput() and term.isInput():
            #term.inputChanged(self)
        #if term.isInput() and term.isOutput():
            #self.inputChanged(term)
        
        self.connected(term)
        if term._refterm==None:
            if term not in self.last.connections():
                conn = self.last.connectTo(term)
                conn.hide()
        if term._refterm!=None:
            if term.last not in self.last.connections():
                conn = term.last.connectTo(self.last)
                conn.hide()
                term.last.recolor()
                self.last.recolor()
        self.recolor()
        term.recolor()
        return connectionItem
        




        
    def disconnectFrom(self, term):

        if not self.connectedTo(term):
            return
        item = self._connections[term]
        #print "removing connection", item
        #item.scene().removeItem(item)
        item.close()
        del self._connections[term]
        if self in term._supercon:
            del term._supercon[self]
        term.recolor()
        self.disconnected(term)

        self.refterm().disconnectFrom(term)
        self.recolor()

            
        
    def disconnectAll(self):
        for t in list(self._connections.keys()):
            self.disconnectFrom(t)
        
    def recolor(self, color=None, recurse=True):
     ## disconnected terminals are black
        self.color = self.last.color
        self.graphicsItem().setBrush(QtGui.QBrush(self.color))
        
        if recurse:
            for t in self.connections():
                t.recolor(self.color, recurse=False)

        
    def rename(self, name):
        self.refterm().rename(name)
        oldName = self._name
        self._name = name
        self.node().terminalRenamed(self, oldName)
        self.graphicsItem().termRenamed(name)
        
    def __repr__(self):
        return "<SuperTerminal %s.%s>" % (str(self.node().name()), str(self.name()))
        
    #def extendedConnections(self, terms=None):
        #"""Return list of terminals (including this one) that are directly or indirectly wired to this."""        
        #if terms is None:
            #terms = {}
        #terms[self] = None
        #for t in self._connections:
            #if t in terms:
                #continue
            #terms.update(t.extendedConnections(terms))
        #return terms
        
    def __hash__(self):
        return id(self)

    def close(self):
        self.refterm().close()
        self.disconnectAll()
        item = self.graphicsItem()
        if item.scene() is not None:
            item.scene().removeItem(item)
        
    def saveState(self):
        return {'io': self._io, 'multi': self._multi, 'optional': self._optional, 'renamable': self._renamable, 'removable': self._removable, 'multiable': self._multiable}

