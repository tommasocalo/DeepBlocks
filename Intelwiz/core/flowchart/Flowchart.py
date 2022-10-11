# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore,QtWidgets, QtGui, USE_PYSIDE
from .Node import *
from pyqtgraph.pgcollections import OrderedDict
from pyqtgraph.widgets.TreeWidget import *
from pyqtgraph.widgets.TreeWidget import TreeWidget
import functools
## pyside and pyqt use incompatible ui files.
if USE_PYSIDE:
    from . import FlowchartTemplate_pyside as FlowchartTemplate
    from . import FlowchartCtrlTemplate_pyside as FlowchartCtrlTemplate
else:
    from . import FlowchartTemplate_pyqt as FlowchartTemplate
    from . import FlowchartCtrlTemplate_pyqt as FlowchartCtrlTemplate
    from . import FlowchartModulesTemplate_pyqt as FlowchartModulesTemplate

from .Terminal import Terminal
from .SuperNode import SuperNode
from .library.FC import FCNode
from .library.CONV2D import CONV2D
from .library.Input import InputNode
import random

from numpy import ndarray
from . import library
import torch.nn as nn

from pyqtgraph.debug import printExc
import pyqtgraph.configfile as configfile
import pyqtgraph.dockarea as dockarea
import pyqtgraph as pg
from . import FlowchartGraphicsView
import json 
import torch 
import matplotlib

matplotlib.use('Qt5Agg')

import re

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

def cmp(a, b):
    return (a[0] > b[0]) - (a[0] < b[0]) 
def strDict(d):
    return dict([(str(k), v) for k, v in d.items()])


def toposort(deps, nodes=None, seen=None, stack=None, depth=0):
    """Topological sort. Arguments are:
      deps    dictionary describing dependencies where a:[b,c] means "a depends on b and c"
      nodes   optional, specifies list of starting nodes (these should be the nodes 
              which are not depended on by any other nodes) 
    """
    
    if nodes is None:
        ## run through deps to find nodes that are not depended upon
        rem = set()
        for dep in deps.values():
            rem |= set(dep)
        nodes = set(deps.keys()) - rem
    if seen is None:
        seen = set()
        stack = []
    sorted = []
    #print "  "*depth, "Starting from", nodes
    for n in nodes:
        if n in stack:
            raise Exception("Cyclic dependency detected", stack + [n])
        if n in seen:
            continue
        seen.add(n)
        #print "  "*depth, "  descending into", n, deps[n]
        sorted.extend( toposort(deps, deps[n], seen, stack+[n], depth=depth+1))
        #print "  "*depth, "  Added", n
        sorted.append(n)
        #print "  "*depth, "  ", sorted
    return sorted


class Flowchart(Node):
    
    sigFileLoaded = QtCore.Signal(object)
    sigFileSaved = QtCore.Signal(object)
    updateGraph = QtCore.Signal(object)
    updateBar = QtCore.Signal(object)
    
    #sigOutputChanged = QtCore.Signal() ## inherited from Node
    sigChartLoaded = QtCore.Signal()
    sigStateChanged = QtCore.Signal()
    
    def __init__(self, terminals=None, name=None, filePath=None):
        if name is None:
            name = "Flowchart"
        if terminals is None:
            terminals = {}
        self.filePath = filePath
        Node.__init__(self, name, allowAddInput=True, allowAddOutput=True)  ## create node without terminals; we'll add these later
        
        
        self.inputWasSet = False  ## flag allows detection of changes in the absence of input change.
        self._nodes = {}
        self.nextZVal = 10
        #self.connects = []
        #self._chartGraphicsItem = FlowchartGraphicsItem(self)
        self._widget = None
        self._scene = None
        self.processing = False ## flag that prevents recursive node updates
        self.epochs=100
        self.loss= nn.CrossEntropyLoss() 
        self.optim = "SGD" 
        self.bs = None 
        self.widget()    
        self.custom = {}
        # self.inputNode = Node('Input', allowRemove=False, allowAddOutput=True)
        # self.outputNode = None
        self.outputNode = Node('Output', allowRemove=False, allowAddInput=True)
        # self.addNode(self.inputNode, 'Input', [-150, 0])
        self.addNode(self.outputNode, 'Output', [300, 0])
        self.updateGraph.connect(self.widget().modules.update_plot)
        self.updateBar.connect(self.widget().chartWidget.setValueP)
        #self.outputNode.sigOutputChanged.connect(self.outputChanged)
        self.outputNode.sigTerminalRenamed.connect(self.internalTerminalRenamed)
        # # self.inputNode.sigTerminalRenamed.connect(self.internalTerminalRenamed)
        self.outputNode.sigTerminalRemoved.connect(self.internalTerminalRemoved)
        # # self.inputNode.sigTerminalRemoved.connect(self.internalTerminalRemoved)
        self.outputNode.sigTerminalAdded.connect(self.internalTerminalAdded)
        # # self.inputNode.sigTerminalAdded.connect(self.internalTerminalAdded)
        self.outputNode.sigMerge.connect(self.mergeNodes)
        self.outputNode.sigSave.connect(self.addModule)

        self.viewBox.autoRange(padding = 0.04)
        for name, opts in terminals.items():
            self.addTerminal(name, **opts)
      
    def setInput(self, **args):
        """Set the input values of the flowchart. This will automatically propagate
        the new values throughout the flowchart, (possibly) causing the output to change.
        """
        #print "setInput", args
        #Node.setInput(self, **args)
        #print "  ....."
        self.inputWasSet = True
        self.inputNode.setOutput(**args)
        
    def outputChanged(self):
        ## called when output of internal node has changed
        vals = self.outputNode.inputValues()
        self.widget().outputChanged(vals)
        self.setOutput(**vals)
        #self.sigOutputChanged.emit(self)
        print ("test" ) # TODO
        
    def output(self):
        """Return a dict of the values on the Flowchart's output terminals.
        """
        return self.outputNode.inputValues()
        
    def nodes(self):
        return self._nodes
        
    def addTerminal(self, name, **opts):
        term = Node.addTerminal(self, name, **opts)
        name = term.name()
        if opts['io'] == 'in':  ## inputs to the flowchart become outputs on the input node
            opts['io'] = 'out'
            opts['multi'] = False
            self.inputNode.sigTerminalAdded.disconnect(self.internalTerminalAdded)
            try:
                term2 = self.inputNode.addTerminal(name, **opts)
            finally:
                self.inputNode.sigTerminalAdded.connect(self.internalTerminalAdded)
                
        else:
            opts['io'] = 'in'
            #opts['multi'] = False
            self.outputNode.sigTerminalAdded.disconnect(self.internalTerminalAdded)
            try:
                term2 = self.outputNode.addTerminal(name, **opts)
            finally:
                self.outputNode.sigTerminalAdded.connect(self.internalTerminalAdded)
        return term

    def removeTerminal(self, name):
        #print "remove:", name
        term = self[name]
        inTerm = self.internalTerminal(term)
        Node.removeTerminal(self, name)
        inTerm.node().removeTerminal(inTerm.name())
        
    def internalTerminalRenamed(self, term, oldName):
        self[oldName].rename(term.name())
        
    def internalTerminalAdded(self, node, term):
        if term._io == 'in':
            io = 'out'
        else:
            io = 'in'
        Node.addTerminal(self, term.name(), io=io, renamable=term.isRenamable(), removable=term.isRemovable(), multiable=term.isMultiable())
        
    def internalTerminalRemoved(self, node, term):
        try:
            Node.removeTerminal(self, term.name())
        except KeyError:
            pass
        
    def terminalRenamed(self, term, oldName):
        newName = term.name()
        #print "flowchart rename", newName, oldName
        #print self.terminals
        Node.terminalRenamed(self, self[oldName], oldName)
        #print self.terminals
        for n in [self.inputNode, self.outputNode]:
            if oldName in n.terminals:
                n[oldName].rename(newName)


    def createNode(self, nodeType, name=None, pos=None):
        if (name is None) or (name in self._nodes) :
            n = 0
            while True:
                if not n:
                    name = nodeType
                else:
                    name = "%s.%d" % (nodeType, n)
                if name not in self._nodes:
                    break
                n += 1
        node = library.getNodeType(nodeType)(name)
        self.addNode(node, name, pos)
        return node
        
    def addNode(self, node, name, pos=None):
        if pos is None:
            pos = [0, 0]
        if type(pos) in [QtCore.QPoint, QtCore.QPointF]:
            pos = [pos.x(), pos.y()]
        item = node.graphicsItem()
        item.setZValue(self.nextZVal*2)
        self.nextZVal += 1
        self.viewBox.addItem(item)
        item.moveBy(*pos)
        self._nodes[name] = node
        self.widget().addNode(node) 
        node.sigClosed.connect(self.nodeClosed)
        node.sigRenamed.connect(self.nodeRenamed)
        node.sigOutputChanged.connect(self.nodeOutputChanged)
        node.sigMerge.connect(self.mergeNodes)
        node.sigSave.connect(self.addModule)
        if isinstance(node, SuperNode):
            node.sigExp.connect(self.expandNode)


    def recurN(self,level):
        max = 0 
        for name in self._nodes.keys():
            if name.startswith("SuperN"):
                le = int(name.split("_")[1].split('.')[0][1:])
                if le==level:
                    if int(name.split(".")[1]) >= max:
                        max = int(name.split(".")[1])+1
        return max 

    def newN(self,name,list):
        name2 = name
        i = 1
        while name2 in list:
            name2 = "%s.%d" % (name, i)
            i += 1
        return name2

    def mergeNodes(self,node):
        nodes = node.scene().selectedItems()
        
        level = 0 
        for node in nodes:
            if isinstance(node.node, SuperNode):
                if node.node.level>=level:

                    level = node.node.level+1
        n = self.recurN(level)
        sname = 'SuperN_L'+str(level)+'.'+str(n)
        nt=[]
        for node in nodes:
            nt.append(node.node)
        supernode = SuperNode(sname, level,nt)

        opts={}
        terminals = []
        if len(nodes)>0:
            self.addNode(supernode, sname, nodes[-1].pos())

            for node in nodes: 
                for name,terminal in node.terminals.items():
                        terminals.append(terminal[1])
                        for term in terminal[0].connections():
                            if term.node().graphicsItem() not in nodes and term.node().graphicsItem().isVisible():
                                if terminal[0].isInput():
                                    opts["_io"] = 'in'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())
                                    supernode.addTerminal(name, refterm=terminal[0],io='in', renamable=True, removable=True, multiable=False)
                                    supernode.terminals[name].connectTo(term)

                                if terminal[0].isOutput():
                                    opts["_io"] = 'out'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())                                    
                                    supernode.addTerminal(name, refterm=terminal[0],io='out', renamable=True, removable=True, multiable=False)
                                    supernode.terminals[name].connectTo(term)
                        for term in terminal[0]._supercon:
                            if term.node().graphicsItem() not in nodes and term.node().graphicsItem().isVisible():
                                if terminal[0].isInput():
                                    opts["_io"] = 'in'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())
                                    supernode.addTerminal(name, refterm=terminal[0],io='in', renamable=True, removable=True, multiable=False)
                                    supernode.terminals[name].connectTo(term)


                                if terminal[0].isOutput():
                                    opts["_io"] = 'out'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())                                    
                                    supernode.addTerminal(name, refterm=terminal[0],io='out', renamable=True, removable=True, multiable=False)
                                    supernode.terminals[name].connectTo(term)
                        if len(terminal[0].connections())==0:
                                if terminal[0].isOutput():
                                    opts["_io"] = 'out'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())                                    
                                    supernode.addTerminal(name, refterm=terminal[0],io='out', renamable=True, removable=True, multiable=False)

                                if terminal[0].isInput():
                                    opts["_io"] = 'in'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())
                                    supernode.addTerminal(name, refterm=terminal[0],io='in', renamable=True, removable=True, multiable=False)
      
            for node in nodes:
                for term in node.terminals.values():
                    term[1].hide()
                    for conn in term[0].connections().values():
                            conn.hide()
                    for conn in term[0]._supercon.values():
                            conn.hide()
                node.hide()
        
        return 
                
    def expandNode(self,nodes):
        nodes.node.expand()
        del self._nodes[nodes.node.name()]
        self.widget().expandNode(nodes.node)
        

    def checkIntegrity (self,nodes):
        #for node in nodes: 
        return True
    def removeNode(self, node):
        node.close(False)
        
    def nodeClosed(self, node):
        del self._nodes[node.name()]
        self.widget().removeNode(node)
        try:
            node.sigClosed.disconnect(self.nodeClosed)
        except TypeError:
            pass
        try:
            node.sigRenamed.disconnect(self.nodeRenamed)
        except TypeError:
            pass

        
    def nodeRenamed(self, node, oldName):
        del self._nodes[oldName]
        self._nodes[node.name()] = node
        self.widget().nodeRenamed(node, oldName)
        
    def arrangeNodes(self):
        pass
        

    def getMeanPos(self):
        
        mylist = []    

        for n in self._nodes.values():
            pos = n.graphicsItem().pos()
            mylist.append([pos.x(),pos.y()])
        return np.array(mylist).mean(axis=0)
    def internalTerminal(self, term):
        """If the terminal belongs to the external Node, return the corresponding internal terminal"""
        if term.node() is self:
            if term.isInput():
                return self.inputNode[term.name()]
            else:
                return self.outputNode[term.name()]
        else:
            return term
        
    def connectTerminals(self, term1, term2):
        """Connect two terminals together within this flowchart."""
        term1 = self.internalTerminal(term1)
        term2 = self.internalTerminal(term2)
        term1.connectTo(term2)
        
    



    def getOrder(self,term,l):
        l.append(term._node())
        if term._refout != None:
            self.getOrder(list(term._refout._connections.keys())[0],l)
        return l 


    def getOrdersNodes(self):
        ordersInput={}
        ordersNodes = {}
        inputs = list(filter(lambda n: isinstance(n, InputNode), self._nodes.values()))
        for i in inputs:
            if not (i.order in ordersInput.keys()):
                ordersInput[i.order] = []
                ordersInput[i.order].append(i)
            else:
                ordersInput[i.order].append(i)
        orders = sorted(list(ordersInput.keys()))
        for o in orders:
            for i in ordersInput[o]:
                order = [i]
                if list(i.terminals['Output']._connections.keys())[0]:
                    self.getOrder(list(i.terminals['Output']._connections.keys())[0],order)
                ordersNodes[i] = order
        return inputs,ordersInput,ordersNodes

    def train(self):
        ordersInput={}
        inputorders=[]
        inputs = list(filter(lambda n: isinstance(n, InputNode), self._nodes.values()))
        for i in inputs:
            for o in i.order:
                if o not in inputorders:
                    inputorders.append(o)
 
        orders = sorted(list(set(inputorders)))
        # for i in inputs:
        #     if not (i.order in ordersInput.keys()):
        #         ordersInput[i.order] = []
        #         ordersInput[i.order].append(i)
        #     else:
        #         ordersInput[i.order].append(i)     
        #orders = sorted(list(ordersInput.keys()))
        for n in self._nodes.values():
            if isinstance(n, FCNode) or isinstance(n, CONV2D):
                self.outputNode.updateParams(n.getParams())
        self.outputNode.setopt()
        # noto = {}
        # for o in orders:
        #     noto[o]= list(filter(lambda n: n not in ordersInput[o], inputs))
        for e in range(self.epochs):
            for n in inputs:
                n.init_inputs(orders)
            res = (1,1) 
            acc = {o:[] for o in orders}
            test = {o:[] for o in orders}
            acc_means={}
            cont = True
            finished = {o:False  for o in orders}
            while(cont):
                for o in orders:
                    if not finished[o]:
                        # for n in noto[o]: 
                        #     n.skip(True)
                        res = self.processN()
                        print(o,res)

                        if res[1] != 'test':
                            acc[o].append(res[0])
                        else: 
                            test[o] = res[0]
                            finished[o]=True

                if all(finished.values()):
                    cont = False   
                    # for n in noto[o]: 
                    #     n.skip(False)
            for o in orders:
                acc_means[o] = np.array(acc[o]).mean()
            
            self.updateGraph.emit((e,acc_means,test))
            self.updateBar.emit(e+1)    
            

    def processN(self):
        """
        Process data through the flowchart, returning the output.
        
        Keyword arguments must be the names of input terminals. 
        The return value is a dict with one key per output terminal.
        
        """
        data = {}  ## Stores terminal:value pairs
        
        ## determine order of operations
        ## order should look like [('p', node1), ('p', node2), ('d', terminal1), ...] 
        ## Each tuple specifies either (p)rocess this node or (d)elete the result from this terminal
        order = self.processOrder()
        #print "ORDER:", order
        

        ret = {}
            
        ## process all in order
        for c, arg in order:
            
            if c == 'p':     ## Process a single node
                #print "===> process:", arg
                node = arg

                            
                ## get input and output terminals for this node
                outs = list(node.outputs().values())
                ins = list(node.inputs().values())
                
                ## construct input value dictionary
                args = {}
                for inp in ins:
                    inputs = inp.inputTerminals()
                    if len(inputs) == 0:
                        continue
                    args[inp.name()] = data[inputs[0]]  
                        
                if node is self.outputNode:
                    ret = node.train(**args)  ## we now have the return value, but must keep processing in case there are other endpoint nodes in the chart
                else:
                    try:
                        if node.isBypassed():
                            result = node.processBypassed(**args)
                        else:
                            result = node.train(**args)
                    except:
                        print("Error processing node %s. Args are: %s" % (str(node), str(args)))
                        raise
                    for out in outs:
                        #print "    Output:", out, out.name()
                        #print out.name()
                        try:
                            
                            data[out] = result[out.name()]
                        except:
                            print(out, out.name())
                            raise
            #elif c == 'd':   ## delete a terminal result (no longer needed; may be holding a lot of memory)
                #print "===> delete", arg
                #if arg in data:
                   # del data[arg]
                    
        return ret
        
    def processOrder(self):
        """Return the order of operations required to process this chart.
        The order returned should look like [('p', node1), ('p', node2), ('d', terminal1), ...] 
        where each tuple specifies either (p)rocess this node or (d)elete the result from this terminal
        """
        
        ## first collect list of nodes/terminals and their dependencies
        deps = {}
        tdeps = {}   ## {terminal: [nodes that depend on terminal]}
        for name, node in self._nodes.items():
            #if node not in order:
                deps[node] = node.dependentNodes()
                for t in node.outputs().values():
                    tdeps[t] = t.dependentNodes()
            
        #print "DEPS:", deps
        ## determine correct node-processing order
        #deps[self] = []
        order = toposort(deps)
        #print "ORDER1:", order
        
        ## construct list of operations
        ops = [('p', n) for n in order]
        
        ## determine when it is safe to delete terminal values
        dels = []
        for t, nodes in tdeps.items():
            lastInd = 0
            lastNode = None
            for n in nodes:  ## determine which node is the last to be processed according to order
                if n is self:
                    lastInd = None
                    break
                else:
                    try:
                        ind = order.index(n)
                    except ValueError:
                        continue
                if lastNode is None or ind > lastInd:
                    lastNode = n
                    lastInd = ind
            #tdeps[t] = lastNode
            if lastInd is not None:
                dels.append((lastInd+1, t))
        dels=sorted(dels,key = functools.cmp_to_key(cmp))
        for i, t in dels:
            ops.insert(i, ('d', t))
            
        return ops
        
        
    def nodeOutputChanged(self, startNode):
        """Triggered when a node's output values have changed. (NOT called during process())
        Propagates new data forward through network."""
        ## first collect list of nodes/terminals and their dependencies
        
        if self.processing:
            return
        self.processing = True
        try:
            deps = {}
            for name, node in self._nodes.items():
                deps[node] = []
                for t in node.outputs().values():
                    deps[node].extend(t.dependentNodes())
            
            ## determine order of updates 
            order = toposort(deps, nodes=[startNode])
            order.reverse()
            
            ## keep track of terminals that have been updated
            terms = set(startNode.outputs().values())
            
            #print "======= Updating", startNode
            #print "Order:", order
            for node in order[1:]:
                #print "Processing node", node
                for term in list(node.inputs().values()):
                    #print "  checking terminal", term
                    deps = list(term.connections().keys())
                    update = False
                    for d in deps:
                        if d in terms:
                            #print "    ..input", d, "changed"
                            update = True
                            term.inputChanged(d, process=False)
                    if update:
                        #print "  processing.."
                        node.update()
                        terms |= set(node.outputs().values())
                    
        finally:
            self.processing = False
            if self.inputWasSet:
                self.inputWasSet = False
            else:
                self.sigStateChanged.emit()
        
        
    def setBS (self,bs):
        self.bs=bs
    def chartGraphicsItem(self):
        """Return the graphicsItem which displays the internals of this flowchart.
        (graphicsItem() still returns the external-view item)"""
        #return self._chartGraphicsItem
        return self.viewBox
        
    def widget(self):
        if self._widget is None:
            self._widget = FlowchartCtrlWidget(self)
            self.scene = self._widget.scene()
            self.viewBox = self._widget.viewBox()
            #self._scene = QtGui.QGraphicsScene()
            #self._widget.setScene(self._scene)
            #self.scene.addItem(self.chartGraphicsItem())
            
            #ci = self.chartGraphicsItem()
            #self.viewBox.addItem(ci)
            #self.viewBox.autoRange()
        return self._widget

    def listConnections(self):
        conn = set()
        for n in self._nodes.values():
            if not isinstance(n, SuperNode):
                terms = n.outputs()
                for n, t in terms.items():
                    for c in t.connections():
                        conn.add((t, c))
        return conn

    def saveState(self):
        state = Node.saveState(self)
        state['nodes'] = []
        state['connects'] = []
        #state['terminals'] = self.saveTerminals()
        
        for name, node in self._nodes.items():
            cls = type(node)
            if hasattr(cls, 'nodeName'):
                clsName = cls.nodeName
                pos = node.graphicsItem().pos()
                ns = {'class': clsName, 'name': name, 'pos': (pos.x(), pos.y()), 'state': node.saveState()}
                state['nodes'].append(ns)
            else :
                pos = node.graphicsItem().pos()
                ns = {'class': 'SuperNode', 'name': name, 'pos': (pos.x(), pos.y()), 'state': node.saveState()}
                state['nodes'].append(ns)
            
        conn = self.listConnections()
        for a, b in conn:
            state['connects'].append((a.node().name(), a.name(), b.node().name(), b.name()))
        
        # state['inputNode'] = self.inputNode.saveState()
        state['outputNode'] = self.outputNode.saveState()
        return state
    def addModule(self,node):

        cls = type(node)
        if hasattr(cls, 'nodeName'):
            clsName = cls.nodeName
            ns = {'class': clsName, 'name': node.name(), 'state': node.saveState()}
            self.custom[node.name()]=ns
        else :
            ns = {'class': 'SuperNode', 'name': node.name(),'state': node.saveState()}
                        
            terminals=[]
            subnodes = self.getsubnodes(node,[])
            ns['connects'] = []

            ns['subnodes'] = []

            for n in subnodes:
                for name,terminal in n.terminals.items():
                    terminals.append(terminal)
            for n in subnodes:
                for term in n.terminals.values():
                        for conn in term.connections().values():
                            if (conn.source.term in terminals) and (conn.target.term in terminals):
                                if not (conn.source.term.node().name(), conn.source.term.name(), conn.target.term.node().name(), conn.target.term.name()) in ns['connects']:
                                    ns['connects'].append((conn.source.term.node().name(), conn.source.term.name(), conn.target.term.node().name(), conn.target.term.name()))
            for n in subnodes:
                cls = type(n)
                clsName = cls.nodeName
                ls = {'class': clsName, 'name': n.name(), 'state': n.saveState()}
                ns['subnodes'].append(ls)
            self.custom[node.name()]=ns 
        self.widget().modules.addModule(node.name(),'Custom')
        
    def saveModules(self):
        return self.custom
    def restoreModules(self,state):
        for k,v in state.items():
            if k not in self.custom:
                self.custom[k] = v
                self.widget().modules.addModule(k,'Custom')
        
    def insertModule(self,name):
        node = self.custom[name]
        namedict = {}
        if node['class']=='SuperNode':
            for n in node['subnodes']:
                    old_name = n['name']
                    new_name = self.checkName(n['name'])
                    namedict[old_name]=new_name
                    no = self.createNode(n['class'], name=new_name)
                    no.restoreState(n['state'])

                #node.graphicsItem().moveBy(*n['pos'])
            for n1, t1, n2, t2 in node['connects']:

                try:
                    self.connectTerminals(self._nodes[namedict[n1]][t1], self._nodes[namedict[n2]][t2])
                except:
                    print(self._nodes[n1].terminals)
                    print(self._nodes[n2].terminals)
                    printExc("Error connecting terminals %s.%s - %s.%s:" % (n1, t1, n2, t2))
            name = self.checkName(node['name'])   
            di = {}   
            self.recMapK(di,node['state']['subnodes'],namedict)
            
            self.recMerge(name,node['state']['level'],di)


        else:
               
                    n = self.createNode(node['class'], name=node['name'])
                    n.restoreState(node['state'])

        pass
    def getsubnodes(self,node,l):
        for n in node.subnodes:
            if isinstance(n, SuperNode):
                self.getsubnodes(n,l)
            else:
                l.append(n)
        return l



    def restoreState(self, state, clear=False):
        self.blockSignals(True)
        try:
            if clear:
                self.clear()
            Node.restoreState(self, state)
            nodes = state['nodes']
            nodes.sort(key = lambda a: a['pos'][0])
            supernodess = filter(lambda n: 'subnodes' in n['state'].keys(), nodes)
            nodes = filter(lambda n:'subnodes' not in n['state'].keys(), nodes)
            supernodes = filter(lambda n: not n['state']['nested'], supernodess)
            for n in nodes:
                if n['name'] in self._nodes:
                    #self._nodes[n['name']].graphicsItem().moveBy(*n['pos'])
                    self._nodes[n['name']].restoreState(n['state'])
                    continue
                try:
                    node = self.createNode(n['class'], name=n['name'])
                    node.restoreState(n['state'])
                except:
                    printExc("Error creating node %s: (continuing anyway)" % n['name'])
                #node.graphicsItem().moveBy(*n['pos'])
                
            # self.inputNode.restoreState(state.get('inputNode', {}))
            self.outputNode.restoreState(state.get('outputNode', {}))
                
            #self.restoreTerminals(state['terminals'])
            for n1, t1, n2, t2 in state['connects']:

                try:
                    self.connectTerminals(self._nodes[n1][t1], self._nodes[n2][t2])
                except:
                    print(self._nodes[n1].terminals)
                    print(self._nodes[n2].terminals)
                    printExc("Error connecting terminals %s.%s - %s.%s:" % (n1, t1, n2, t2))
            for supernode in supernodes:
                self.recMerge(supernode['name'],supernode['state']['level'],supernode['state']['subnodes'])
                
        finally:
            self.blockSignals(False)
            
        self.sigChartLoaded.emit()
        # self.outputChanged()
        self.sigStateChanged.emit()
        #self.sigOutputChanged.emit()

    def recMapK(self,di,subnodes,diz):

        for k in subnodes.keys():

            mapk = diz[k]  
            di[mapk] = subnodes[k]

            for k1,v1 in subnodes[k].items():

               if k1=='subnodes' :
                  
                  self.recMapK(k,subnodes[k]['level'],subnodes[k]['subnodes'],diz)


        


    def recMerge(self,name,level,subnodes):
        for k,v in subnodes.items():
            for k1,v1 in subnodes[k].items():
               if k1=='subnodes' :
                  
                  self.recMerge(k,subnodes[k]['level'],subnodes[k]['subnodes'])
        
        self.mergeNodesfromlist(name,level,subnodes)
        return


    def ground(self,list):
        ground = True
        for el in list:
            if el['subnodes']:
                ground = False
    def checkName(self,name):
        if name in self._nodes:
            while True:
                if len(name.split('.'))>1:
                    number = int(name.split('.')[-1])
                    number += 1 
                    name = name.split('.')[0]+'.'+str(number)
                else: 
                    name = name+'.1'
                if name not in self._nodes:
                        return name
        else:
            return name
    def mergeNodesfromlist(self,name,level,list):
        nodes = [self._nodes[n]._graphicsItem for n in list.keys()]
        

        sname = name
        
        nt=[]
        for node in nodes:
            nt.append(node.node)
        supernode = SuperNode(sname, level,nt)
        opts={}
        terminals = []
        if len(nodes)>0:
            self.addNode(supernode, sname, nodes[-1].pos())

            for node in nodes: 
                for name,terminal in node.terminals.items():
                        terminals.append(terminal[1])
                        for term in terminal[0].connections():
                            if term.node().graphicsItem() not in nodes:
                                if terminal[0].isInput():
                                    opts["_io"] = 'in'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())
                                    supernode.addTerminal(name, refterm=terminal[0],io='in', renamable=True, removable=True, multiable=False)
                                    supernode.terminals[name].connectTo(term)

                                if terminal[0].isOutput():
                                    opts["_io"] = 'out'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())                                    
                                    supernode.addTerminal(name, refterm=terminal[0],io='out', renamable=True, removable=True, multiable=False)

                                    supernode.terminals[name].connectTo(term)
                        if len(terminal[0].connections())==0:
                                if terminal[0].isOutput():
                                    opts["_io"] = 'out'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())                                    
                                    supernode.addTerminal(name, refterm=terminal[0],io='out', renamable=True, removable=True, multiable=False)
                                    
                                if terminal[0].isInput():
                                    opts["_io"] = 'in'
                                    if name in supernode.terminals.keys():
                                        name = self.newN(name,supernode.terminals.keys())
                                    supernode.addTerminal(name, refterm=terminal[0],io='in', renamable=True, removable=True, multiable=False)
    
            for node in nodes:
                for term in node.terminals.values():
                    term[1].hide()
                    for conn in term[0].connections().values():
                        if (conn.source in terminals) and (conn.target in terminals):
                            conn.hide()
                node.hide()
        self._nodes[sname] = supernode
        return 


    def loadFile(self, fileName=None, startDir=None):
        if fileName is None:
            if startDir is None:
                startDir = self.filePath
            if startDir is None:
                startDir = '.'
            self.fileDialog = pg.FileDialog(None, "Load Flowchart..", startDir, "Flowchart (*.fc)")
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            #self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.loadFile)
            return
            ## NOTE: was previously using a real widget for the file dialog's parent, but this caused weird mouse event bugs..
            #fileName = QtGui.QFileDialog.getOpenFileName(None, "Load Flowchart..", startDir, "Flowchart (*.fc)")
        fileName = str(fileName)
        state = configfile.readConfigFile(fileName)
        self.restoreState(state, clear=True)
        self.viewBox.autoRange()
        #self.emit(QtCore.SIGNAL('fileLoaded'), fileName)
        self.sigFileLoaded.emit(fileName)
        
    def saveFile(self, fileName=None, startDir=None, suggestedFileName='flowchart.fc'):
        if fileName is None:
            if startDir is None:
                startDir = self.filePath
            if startDir is None:
                startDir = '.'
            self.fileDialog = pg.FileDialog(None, "Save Flowchart..", startDir, "Flowchart (*.fc)")
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            #self.fileDialog.setDirectory(startDir)
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.saveFile)
            return
            #fileName = QtGui.QFileDialog.getSaveFileName(None, "Save Flowchart..", startDir, "Flowchart (*.fc)")
        configfile.writeConfigFile(self.saveState(), fileName)
        self.sigFileSaved.emit(fileName)

    def saveModulesFile(self, fileName=None, startDir=None, suggestedFileName='modules.fc'):
        if fileName is None:
            if startDir is None:
                startDir = self.filePath
            if startDir is None:
                startDir = '.'
            self.fileDialog_mod = pg.FileDialog(None, "Save Flowchart..", startDir, "Modules (*.fc)")
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog_mod.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            #self.fileDialog.setDirectory(startDir)
            self.fileDialog_mod.show()
            self.fileDialog_mod.fileSelected.connect(self.saveModulesFile)
            return
            #fileName = QtGui.QFileDialog.getSaveFileName(None, "Save Flowchart..", startDir, "Flowchart (*.fc)")
        configfile.writeConfigFile(self.saveModules(), fileName)
        #self.sigFileSaved.emit(fileName)

    def loadModules(self, fileName=None, startDir=None):
        if fileName is None:
            if startDir is None:
                startDir = self.filePath
            if startDir is None:
                startDir = '.'
            self.fileDialog_mod = pg.FileDialog(None, "Load Moules..", startDir, "Modules (*.fc)")
            #self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            #self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog_mod.show()
            self.fileDialog_mod.fileSelected.connect(self.loadModules)
            return
            ## NOTE: was previously using a real widget for the file dialog's parent, but this caused weird mouse event bugs..
            #fileName = QtGui.QFileDialog.getOpenFileName(None, "Load Flowchart..", startDir, "Flowchart (*.fc)")
        fileName = str(fileName)
        state = configfile.readConfigFile(fileName)
        self.restoreModules(state)
        self.viewBox.autoRange()
        #self.emit(QtCore.SIGNAL('fileLoaded'), fileName)
        #self.sigFileLoaded.emit(fileName)
    def clear(self):
        for n in list(self._nodes.values()):
            if n is self.outputNode:
                continue
            n.close(True)  ## calls self.nodeClosed(n) by signal
        #self.clearTerminals()
        self.widget().clear()
        
    def clearTerminals(self):
        Node.clearTerminals(self)
        # self.inputNode.clearTerminals()
        self.outputNode.clearTerminals()

#class FlowchartGraphicsItem(QtGui.QGraphicsItem):
class FlowchartGraphicsItem(GraphicsObject):
    
    def __init__(self, chart):
        #print "FlowchartGraphicsItem.__init__"
        #QtGui.QGraphicsItem.__init__(self)
        GraphicsObject.__init__(self)
        self.chart = chart ## chart is an instance of Flowchart()
        self.updateTerminals()
        
    def updateTerminals(self):
        #print "FlowchartGraphicsItem.updateTerminals"
        self.terminals = {}
        bounds = self.boundingRect()
        inp = self.chart.inputs()
        dy = bounds.height() / (len(inp)+1)
        y = dy
        for n, t in inp.items():
            item = t.graphicsItem()
            self.terminals[n] = item
            item.setParentItem(self)
            item.setAnchor(bounds.width(), y)
            y += dy
        out = self.chart.outputs()
        dy = bounds.height() / (len(out)+1)
        y = dy
        for n, t in out.items():
            item = t.graphicsItem()
            self.terminals[n] = item
            item.setParentItem(self)
            item.setAnchor(0, y)
            y += dy
        
    def boundingRect(self):
        #print "FlowchartGraphicsItem.boundingRect"
        return QtCore.QRectF()
        
    def paint(self, p, *args):
        #print "FlowchartGraphicsItem.paint"
        pass
        #p.drawRect(self.boundingRect())
    
class FlowchartModules(dockarea.DockArea):
    def __init__(self, chart):
        #QtGui.QWidget.__init__(self)
        dockarea.DockArea.__init__(self)
        self.chart = chart
        self.hoverItem = None
        #self.setMinimumWidth(250)
        #self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding))
        
        #self.ui = FlowchartTemplate.Ui_Form()
        #self.ui.setupUi(self)
        
        ## build user interface (it was easier to do it here than via developer)
        self.ui = FlowchartModulesTemplate.Ui_Form()
        self.ui.setupUi(self)
        self.ui.moduleList.setColumnCount(2)

        #self.ui.ctrlList.setColumnWidth(0, 200)
        self.ui.moduleList.setColumnWidth(1, 300)
        self.ui.moduleList.setVerticalScrollMode(self.ui.moduleList.ScrollPerPixel)
        self.ui.moduleList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


        
        self.modulesDock = dockarea.Dock('Modules', size=(1000, 20))

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.graphDock = dockarea.Dock('Chart', size=(1000, 20))
        self.trainAcc  = {}
        self.testAcc  = {}
        self.colors  = None
        self.graphDock.addWidget(self.canvas)
        self.saveBtn = QtWidgets.QPushButton('Save')
        self.loadBtn = QtWidgets.QPushButton('Load')
        self.default= {}

                
        self.modulesDock.addWidget(self.ui.moduleList,0,0,4,4)
        self.modulesDock.addWidget(self.saveBtn,5,0,1,2)
        self.modulesDock.addWidget(self.loadBtn,5,2,1,2)
        self.types={}
        self.addDock(self.modulesDock)
        self.addDock(self.graphDock, 'bottom')
        self.saveBtn.clicked.connect(self.saveModules)
        self.loadBtn.clicked.connect(self.loadModules)
        self.initModules("Default")
        self.initModules("Custom")
        for _, nodes in library.getNodeTree().items():
            for name in nodes:
                self.addModule(name,'Default')
    def saveModules(self):
        try:

            newFile = self.chart.saveModulesFile()
            #self.ui.saveAsBtn.success("Saved.")
            #print "Back to saveAsClicked."
        except:
            #self.saveBtn.failure("Error")
            raise
            
        #self.setCurrentFile(newFile)
        pass
    def loadModules(self):
        self.chart.loadModules()
        pass
    def gencol(self,n):
        if self.colors==None:
            self.colors=[]
            for i  in range(1,2*(n+1)):
                self.colors.append("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]))
        else: 
            return self.colors

    def update_plot(self,sub):
        epoch,trAcc,testAcc = sub
        self.gencol(len(list(trAcc.keys()))*2)

        self.xdata = list(range(1,epoch+2))
        # Drop off the first y element, append a new one.
        for k,v in trAcc.items():
            if k not in self.trainAcc:
                self.trainAcc[k]=[]
            if k not in self.testAcc:
                self.testAcc[k]=[]
            self.trainAcc[k].append(trAcc[k])
            self.testAcc[k].append(testAcc[k]) 

        self.canvas.axes.cla()  # Clear the canvas.
        for k,v in self.trainAcc.items():

            self.canvas.axes.plot(self.xdata, self.trainAcc[k], color = self.colors[k+1], label="Train_Acc_"+str(k))
            self.canvas.axes.plot(self.xdata, self.testAcc[k], color =self.colors[(k+1)*2],label="Test_Acc_"+str(k))

        self.canvas.axes.legend(loc="upper left")
        # Trigger the canvas to update and redraw.
        self.canvas.draw()


    def addModule(self,name,type):
        item2 = self.types[type]
        item = QtGui.QTreeWidgetItem([name, '', ''])

        freeze = QtWidgets.QPushButton('+')
        freeze.setToolTip("Add")
        freeze.setFixedWidth(30)
        freeze.clicked.connect(self.addTriggered)
        freeze.name=name

        item.freezeBtn = freeze
        # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)

        #freeze.clicked.connect(self.freezeClicked)

        btnsWidget = QtGui.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(freeze)
        btnsWidget.setLayout(layout)
        item2.addChild(item)

        self.ui.moduleList.setItemWidget(item, 1, btnsWidget)
                    

    def initModules(self, name):
        #if ctrl is None:
            #return
        item = QtGui.QTreeWidgetItem([name, '', ''])


        # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)

        #freeze.clicked.connect(self.freezeClicked)


        self.ui.moduleList.addTopLevelItem(item)

        self.types[name]=  item                 

        #self.nodeMenu.triggered.connect(self.addTriggered)

        #self.ui.addNodeBtn.mouseReleaseEvent = self.addNodeBtnReleased
            
    def addTriggered(self):
        btn = QtCore.QObject.sender(self)

        if btn.name in self.chart.custom:
            self.chart.insertModule(btn.name)
        else:   
            self.chart.createNode(btn.name, pos=self.chart.getMeanPos())
         #self.chart.createNode(nodeType, pos=pos)

        

    def reloadLibrary(self):
        #QtCore.QObject.disconnect(self.nodeMenu, QtCore.SIGNAL('triggered(QAction*)'), self.nodeMenuTriggered)
        pass
        
    def buildMenu(self, pos=None):
        pass
    
    def menuPosChanged(self, pos):
        pass
    def showViewMenu(self, ev):
        pass
        
    def scene(self):
        return self._scene ## the GraphicsScene item

    def viewBox(self):
        return self._viewBox ## the viewBox that items should be added to

    def nodeMenuTriggered(self, action):
        pass


    def selectionChanged(self):
        #print "FlowchartWidget.selectionChanged called."
        items = self._scene.selectedItems()
        pass

    def hoverOver(self, items):
        pass



class FlowchartCtrlWidget(QtGui.QWidget):
    """The widget that contains the list of all the nodes in a flowchart and their controls, as well as buttons for loading/saving flowcharts."""
    
    def __init__(self, chart):
        self.items = {}
        #self.loadDir = loadDir  ## where to look initially for chart files
        self.currentFileName = None
        QtGui.QWidget.__init__(self)
        self.chart = chart
        self.ui = FlowchartCtrlTemplate.Ui_Form()
        self.ui.setupUi(self)
        self.ui.ctrlList.setColumnCount(2)

        #self.ui.ctrlList.setColumnWidth(0, 200)
        self.ui.ctrlList.setColumnWidth(1, 40)
        self.ui.ctrlList.setVerticalScrollMode(self.ui.ctrlList.ScrollPerPixel)
        self.ui.ctrlList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.chartWidget = FlowchartWidget(chart, self)
        #self.chartWidget.viewBox().autoRange()
        self.cwWin = QtGui.QMainWindow()
        self.cwWin.setWindowTitle('Flowchart')
        self.cwWin.setCentralWidget(self.chartWidget)
        self.cwWin.resize(1000, 800)
        
        self.modules = FlowchartModules(chart)
        h = self.ui.ctrlList.header()
        h.setResizeMode(0, h.Stretch)
        self.modules.ui.moduleList.setColumnCount(2)
        self.modules.ui.moduleList.setColumnWidth(1, 200)

        self.modules.ui.moduleList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        h = self.modules.ui.moduleList.header()
        h.setResizeMode(0, h.Stretch)
        self.ui.ctrlList.itemChanged.connect(self.itemChanged)
        self.ui.loadBtn.clicked.connect(self.loadClicked)
        self.ui.saveBtn.clicked.connect(self.saveClicked)
        self.ui.saveAsBtn.clicked.connect(self.saveAsClicked)
        self.ui.showChartBtn.toggled.connect(self.chartToggled)
        self.chart.sigFileLoaded.connect(self.setCurrentFile)
        self.ui.reloadBtn.clicked.connect(self.reloadClicked)
        self.chart.sigFileSaved.connect(self.fileSaved)
        
    
        
    #def resizeEvent(self, ev):
        #QtGui.QWidget.resizeEvent(self, ev)
        #self.ui.ctrlList.setColumnWidth(0, self.ui.ctrlList.viewport().width()-20)
        
    def chartToggled(self, b):
        if b:
            self.cwWin.show()
        else:
            self.cwWin.hide()

    def reloadClicked(self):
        try:
            self.chartWidget.reloadLibrary()
            self.ui.reloadBtn.success("Reloaded.")
        except:
            self.ui.reloadBtn.success("Error.")
            raise
            
            
    def loadClicked(self):
        newFile = self.chart.loadFile()
        #self.setCurrentFile(newFile)
        
    def fileSaved(self, fileName):
        self.setCurrentFile(fileName)
        self.ui.saveBtn.success("Saved.")
        
    def saveClicked(self):
        if self.currentFileName is None:
            self.saveAsClicked()
        else:
            try:
                self.chart.saveFile(self.currentFileName)
                #self.ui.saveBtn.success("Saved.")
            except:
                self.ui.saveBtn.failure("Error")
                raise
        
    def saveAsClicked(self):
        try:
            if self.currentFileName is None:
                newFile = self.chart.saveFile()
            else:
                newFile = self.chart.saveFile(suggestedFileName=self.currentFileName)
            #self.ui.saveAsBtn.success("Saved.")
            #print "Back to saveAsClicked."
        except:
            self.ui.saveBtn.failure("Error")
            raise
            
        #self.setCurrentFile(newFile)
            
    def setCurrentFile(self, fileName):
        self.currentFileName = fileName
        if fileName is None:
            self.ui.fileNameLabel.setText("<b>[ new ]</b>")
        else:
            self.ui.fileNameLabel.setText("<b>%s</b>" % os.path.split(str(self.currentFileName))[1])
        self.resizeEvent(None)

    def itemChanged(self, *args):
        pass
    
    def scene(self):
        return self.chartWidget.scene() ## returns the GraphicsScene object
    
    def viewBox(self):
        return self.chartWidget.viewBox()

    def nodeRenamed(self, node, oldName):
        self.items[node].setText(0, node.name())

    def addNode(self, node):
        ctrl = node.ctrlWidget()
        #if ctrl is None:
            #return
        item = QtGui.QTreeWidgetItem([node.name(), '', ''])

        self.ui.ctrlList.addTopLevelItem(item)

        byp = QtGui.QPushButton('X')
        byp.setToolTip("Bypass that node")
        byp.setCheckable(True)
        byp.setFixedWidth(20)
        item.bypassBtn = byp
        # self.ui.ctrlList.setItemWidget(item, 1, byp)
        byp.node = node
        node.bypassButton = byp
        byp.setChecked(node.isBypassed())
        byp.clicked.connect(self.bypassClicked)

        freeze = QtGui.QPushButton('F') #TODO added
        freeze.setToolTip("Freeze that node")
        freeze.setCheckable(True)
        freeze.setFixedWidth(20)
        item.freezeBtn = freeze
        # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
        freeze.node = node
        node.freezeButton = freeze
        freeze.setChecked(node.isFreezed())
        freeze.clicked.connect(self.freezeClicked)


        btnsWidget = QtGui.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(freeze)
        layout.addWidget(byp)
        btnsWidget.setLayout(layout)
        self.ui.ctrlList.setItemWidget(item, 1, btnsWidget)
                

        if ctrl is not None:
            item2 = QtGui.QTreeWidgetItem()
            item.addChild(item2)
            self.ui.ctrlList.setItemWidget(item2, 0, ctrl)
        self.items[node] = item
        # btnsWidget = freeze
        if isinstance(node, SuperNode):

            for subnode in node.subnodes:
                self.ui.ctrlList.removeTopLevelItem(self.items[subnode])
                item.addChild(self.items[subnode])
                child = item.child(item.indexOfChild(self.items[subnode]))
                ctrl = subnode.ctrlWidget()

                byp = QtGui.QPushButton('X')
                byp.setToolTip("Bypass that node")
                byp.setCheckable(True)
                byp.setFixedWidth(20)
                child.bypassBtn = byp
                # self.ui.ctrlList.setItemWidget(item, 1, byp)
                byp.node = node
                node.bypassButton = byp
                byp.setChecked(node.isBypassed())
                byp.clicked.connect(self.bypassClicked)

                freeze = QtGui.QPushButton('F') #TODO added
                freeze.setToolTip("Freeze that node")
                freeze.setCheckable(True)
                freeze.setFixedWidth(20)
                child.freezeBtn = freeze
                # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
                freeze.node = node
                node.freezeButton = freeze
                freeze.setChecked(node.isFreezed())
                freeze.clicked.connect(self.freezeClicked)


                btnsWidget = QtGui.QWidget()
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(0)
                layout.addWidget(freeze)
                layout.addWidget(byp)
                btnsWidget.setLayout(layout)
                self.ui.ctrlList.setItemWidget(child, 1, btnsWidget)

                if ctrl is not None:
                    item2 = QtGui.QTreeWidgetItem()
                    child.takeChildren()
                    child.addChild(item2)
                    clr = child.child(child.indexOfChild(item2))

                    self.ui.ctrlList.setItemWidget(clr, 0, ctrl)
                if isinstance(subnode, SuperNode):
                    subnode._nested = True
                    self.recAdd(subnode)

    def recAdd(self, node):
            item = self.items[node]

            for subnode in node.subnodes:
                child = item.child(item.indexOfChild(self.items[subnode]))
                ctrl = subnode.ctrlWidget()

                byp = QtGui.QPushButton('X')
                byp.setToolTip("Bypass that node")
                byp.setCheckable(True)
                byp.setFixedWidth(20)
                child.bypassBtn = byp
                # self.ui.ctrlList.setItemWidget(item, 1, byp)
                byp.node = node
                node.bypassButton = byp
                byp.setChecked(node.isBypassed())
                byp.clicked.connect(self.bypassClicked)

                freeze = QtGui.QPushButton('F') #TODO added
                freeze.setToolTip("Freeze that node")
                freeze.setCheckable(True)
                freeze.setFixedWidth(20)
                child.freezeBtn = freeze
                # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
                freeze.node = node
                node.freezeButton = freeze
                freeze.setChecked(node.isFreezed())
                freeze.clicked.connect(self.freezeClicked)


                btnsWidget = QtGui.QWidget()
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(0)
                layout.addWidget(freeze)
                layout.addWidget(byp)
                btnsWidget.setLayout(layout)
                self.ui.ctrlList.setItemWidget(child, 1, btnsWidget)

                if ctrl is not None:
                    item2 = QtGui.QTreeWidgetItem()
                    child.takeChildren()
                    child.addChild(item2)
                    clr = child.child(child.indexOfChild(item2))

                    self.ui.ctrlList.setItemWidget(clr, 0, ctrl)
                if isinstance(subnode, SuperNode):
                    self.recAdd(subnode)


    def recExp(self,node):

            item = self.items[node]
            par = item.parent()
            for subnode in node.subnodes:
                child = item.child(item.indexOfChild(self.items[subnode]))
                ctrl = subnode.ctrlWidget()
                subitem = self.items[subnode]
                item.removeChild(subitem)
                par.addChild(child)
                #if ctrl is None:
                    #return
                subitem = self.items[subnode]
                item.removeChild(subitem)
                self.ui.ctrlList.addTopLevelItem(subitem)

                byp = QtGui.QPushButton('X')
                byp.setToolTip("Bypass that node")
                byp.setCheckable(True)
                byp.setFixedWidth(20)
                subitem.bypassBtn = byp
                # self.ui.ctrlList.setItemWidget(item, 1, byp)
                byp.node = node
                node.bypassButton = byp
                byp.setChecked(node.isBypassed())
                byp.clicked.connect(self.bypassClicked)

                freeze = QtGui.QPushButton('F') #TODO added
                freeze.setToolTip("Freeze that node")
                freeze.setCheckable(True)
                freeze.setFixedWidth(20)
                subitem.freezeBtn = freeze
                # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
                freeze.node = node
                node.freezeButton = freeze
                freeze.setChecked(node.isFreezed())
                freeze.clicked.connect(self.freezeClicked)


                btnsWidget = QtGui.QWidget()
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(0)
                layout.addWidget(freeze)
                layout.addWidget(byp)
                btnsWidget.setLayout(layout)
                self.ui.ctrlList.setItemWidget(subitem, 1, btnsWidget)
               
                if ctrl is not None:
                    item2 = QtGui.QTreeWidgetItem()
                    subitem.takeChildren()
                    subitem.addChild(item2)

                    self.ui.ctrlList.setItemWidget(item2, 0, ctrl)
                self.items[subnode] = subitem
                if isinstance(subnode, SuperNode):
                    self.recAdd(subnode)

        

        
        
    def expandNode (self,node):
        item = self.items[node]
        if item.parent()==None:

            for subnode in node.subnodes:
                ctrl = subnode.ctrlWidget()
                #if ctrl is None:
                    #return
                subitem = self.items[subnode]
                item.removeChild(subitem)
                self.ui.ctrlList.addTopLevelItem(subitem)

                byp = QtGui.QPushButton('X')
                byp.setToolTip("Bypass that node")
                byp.setCheckable(True)
                byp.setFixedWidth(20)
                subitem.bypassBtn = byp
                # self.ui.ctrlList.setItemWidget(item, 1, byp)
                byp.node = node
                node.bypassButton = byp
                byp.setChecked(node.isBypassed())
                byp.clicked.connect(self.bypassClicked)

                freeze = QtGui.QPushButton('F') #TODO added
                freeze.setToolTip("Freeze that node")
                freeze.setCheckable(True)
                freeze.setFixedWidth(20)
                subitem.freezeBtn = freeze
                # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
                freeze.node = node
                node.freezeButton = freeze
                freeze.setChecked(node.isFreezed())
                freeze.clicked.connect(self.freezeClicked)


                btnsWidget = QtGui.QWidget()
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(0)
                layout.addWidget(freeze)
                layout.addWidget(byp)
                btnsWidget.setLayout(layout)
                self.ui.ctrlList.setItemWidget(subitem, 1, btnsWidget)
                        

                if ctrl is not None:
                    item2 = QtGui.QTreeWidgetItem()
                    subitem.takeChildren()
                    subitem.addChild(item2)
                    
                    self.ui.ctrlList.setItemWidget(item2, 0, ctrl)
                self.items[subnode] = subitem
                if isinstance(subnode, SuperNode):
                    subnode._nested = False
                    self.recAdd(subnode)

            self.ui.ctrlList.removeTopLevelItem(self.items[node]) 
        else:
            par = item.parent()
            for subnode in node.subnodes:
                ctrl = subnode.ctrlWidget()
                #if ctrl is None:
                    #return
                child = item.child(item.indexOfChild(self.items[subnode]))
                ctrl = subnode.ctrlWidget()
                subitem = self.items[subnode]
                item.removeChild(subitem)
                par.addChild(child)

                byp = QtGui.QPushButton('X')
                byp.setToolTip("Bypass that node")
                byp.setCheckable(True)
                byp.setFixedWidth(20)
                subitem.bypassBtn = byp
                # self.ui.ctrlList.setItemWidget(item, 1, byp)
                byp.node = node
                node.bypassButton = byp
                byp.setChecked(node.isBypassed())
                byp.clicked.connect(self.bypassClicked)

                freeze = QtGui.QPushButton('F') #TODO added
                freeze.setToolTip("Freeze that node")
                freeze.setCheckable(True)
                freeze.setFixedWidth(20)
                subitem.freezeBtn = freeze
                # self.ui.ctrlList.setItemWidget(item, 1, freez, byp)
                freeze.node = node
                node.freezeButton = freeze
                freeze.setChecked(node.isFreezed())
                freeze.clicked.connect(self.freezeClicked)


                btnsWidget = QtGui.QWidget()
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.setSpacing(0)
                layout.addWidget(freeze)
                layout.addWidget(byp)
                btnsWidget.setLayout(layout)
                self.ui.ctrlList.setItemWidget(subitem, 1, btnsWidget)
                        

                if ctrl is not None:
                    item2 = QtGui.QTreeWidgetItem()
                    subitem.takeChildren()
                    subitem.addChild(item2)
                    self.ui.ctrlList.setItemWidget(item2, 0, ctrl)
                self.items[subnode] = subitem
                if isinstance(subnode, SuperNode):
                    self.recAdd(subnode)

            par.removeChild(self.items[node])             
        return


    def removeNode(self, node):
        if node in self.items:
            item = self.items[node]
            #self.disconnect(item.bypassBtn, QtCore.SIGNAL('clicked()'), self.bypassClicked)
            try:
                item.bypassBtn.clicked.disconnect(self.bypassClicked)
            except TypeError:
                pass
            if self.ui.ctrlList.indexOfTopLevelItem(item)!=-1:
                self.ui.ctrlList.removeTopLevelItem(item)
            else: 
                item.parent().removeChild(item)
            del self.items[node]
            
    def bypassClicked(self):
        btn = QtCore.QObject.sender(self)
        btn.node.bypass(btn.isChecked())

    def freezeClicked(self): #TODO Added
        btn = QtCore.QObject.sender(self)
        btn.node.freeze(btn.isChecked())

    def chartWidget(self):
        return self.chartWidget

    def outputChanged(self, data):
        pass
        #self.ui.outputTree.setData(data, hideRoot=True)

    def clear(self):
        self.chartWidget.clear()
        
    def select(self, node):
        item = self.items[node]
        self.ui.ctrlList.setCurrentItem(item)





class FlowchartWidget(dockarea.DockArea):
    """Includes the actual graphical flowchart and debugging interface"""
    def __init__(self, chart, ctrl):
        #QtGui.QWidget.__init__(self)
        dockarea.DockArea.__init__(self)
        self.chart = chart
        self.ctrl = ctrl
        self.hoverItem = None
        #self.setMinimumWidth(250)
        #self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding))
        
        #self.ui = FlowchartTemplate.Ui_Form()
        #self.ui.setupUi(self)
        
        ## build user interface (it was easier to do it here than via developer)
        self.view = FlowchartGraphicsView.FlowchartGraphicsView(self)
        self.viewDock = dockarea.Dock('view', size=(1000,600))
        self.viewDock.addWidget(self.view)
        self.viewDock.hideTitleBar()
        self.addDock(self.viewDock)
    

        self.hoverText = QtGui.QTextEdit()
        self.hoverText.setReadOnly(True)
        # self.hoverText.setLineWrapMode(QtGui.QTextEdit.NoWrap)  # TODO make configurable
        self.hoverDock = dockarea.Dock('Hover Info', size=(1000, 20))
        self.hoverDock.addWidget(self.hoverText)
        #self.addDock(self.hoverDock, 'bottom')

        self.selInfo = QtGui.QWidget()
        self.selInfoLayout = QtGui.QGridLayout()
        self.selInfo.setLayout(self.selInfoLayout)
        self.selDescLabel = QtGui.QLabel()
        self.selNameLabel = QtGui.QLabel()
        self.selDescLabel.setWordWrap(True)
        self.selectedTree = DataTreeWidget()
        self.selectedTree.setWordWrap(True)  # TODO Added
        #self.selectedTree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        #self.selInfoLayout.addWidget(self.selNameLabel)
        self.selInfoLayout.addWidget(self.selDescLabel)
        self.selInfoLayout.addWidget(self.selectedTree)
        self.selDock = dockarea.Dock('Selected Node', size=(1000, 200))
        #self.selDock.addWidget(self.selInfo)
        #self.addDock(self.selDock, 'bottom')
        
        self.selViz = QtGui.QWidget()
        self.selVizLayout = QtGui.QGridLayout()
        self.selViz.setLayout(self.selVizLayout)
        self.selVizDescLabel = QtGui.QLabel()
        self.selVizNameLabel = QtGui.QLabel()
        self.selVizDescLabel.setWordWrap(True)
        self.selVizTree = VizTreeWidget()
        self.selVizTree.setWordWrap(True)  # TODO Added
        #self.selectedTree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        #self.selInfoLayout.addWidget(self.selNameLabel)
        self.selVizLayout.addWidget(self.selVizDescLabel)
        self.selVizLayout.addWidget(self.selVizTree)
        #self.selDock.addWidget(self.selInfo)
        
        
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtGui.QWidget()
        self.tabs.resize(300,200)

        # Add tabs
        self.tabs.addTab(self.tab1,"Optimization")
        self.tabs.addTab(self.selInfo,"Debug")
        self.tabs.addTab(self.selViz,"Visualization")



        self.selInfoLayout = QtGui.QGridLayout()
        self.tabs.setLayout(self.selInfoLayout)




        self.progress = QtGui.QProgressBar(self)

        



        self.nameLabel = QtWidgets.QLabel('Loss Function')
        self.btnCustom= QtWidgets.QPushButton('Custom...')
        self.combobox = QtWidgets.QComboBox()
        self.combobox.addItem('CE')
        self.combobox.addItem('MSE')


        self.EPLabel = QtWidgets.QLabel('Epochs',self)
        self.BSLabel = QtWidgets.QLabel('Batch Size',self)
        self.EPLineEdit = QtWidgets.QLineEdit(self)
        self.EPLabel.setBuddy(self.EPLineEdit)
        self.BSLineEdit = QtWidgets.QLineEdit(self)
        self.BSLabel.setBuddy(self.BSLineEdit)

        self.nameLabel1 = QtWidgets.QLabel('Optimizer')
        self.btnCustom1= QtWidgets.QPushButton('Custom...')
        self.combobox1 = QtWidgets.QComboBox()
        self.combobox1.addItem('SGD')
        self.combobox1.addItem('ADAM')

        self.LRLabel = QtWidgets.QLabel('Learning Rate',self)
        self.btnCustomLR= QtWidgets.QPushButton('Custom...')
        self.LRLineEdit = QtWidgets.QLineEdit(self)
        self.LRLabel.setBuddy(self.LRLineEdit)

        self.btnTrain= QtWidgets.QPushButton('Train')
        self.btnStop= QtWidgets.QPushButton('Stop')
        self.btnInfer= QtWidgets.QPushButton('Infer')


        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.addWidget(self.nameLabel,0,0)
        mainLayout.addWidget(self.combobox,0,1)
        mainLayout.addWidget(self.btnCustom,0,3)
        mainLayout.addWidget(self.EPLabel,0,4)
        mainLayout.addWidget(self.EPLineEdit,0,5)
        mainLayout.addWidget(self.BSLabel,0,6)
        mainLayout.addWidget(self.BSLineEdit,0,7)


        mainLayout.addWidget(self.nameLabel1,1,0)
        mainLayout.addWidget(self.combobox1,1,1)
        mainLayout.addWidget(self.btnCustom1,1,3)
        mainLayout.addWidget(self.LRLabel,1,4)
        mainLayout.addWidget(self.LRLineEdit,1,5)
        mainLayout.addWidget(self.btnCustomLR,1,6,1,2)


        mainLayout.addWidget(self.btnTrain,2,0)
        mainLayout.addWidget(self.btnStop,2,1)
        mainLayout.addWidget(self.progress,2,2,1,5)
        mainLayout.addWidget(self.btnInfer,2,7)
        #self.pushButton1 = QtWidgets.QPushButton("PyQt5 button")
        self.fileNameLabel = QtWidgets.QLabel()

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignLeft)
        mainLayout.addWidget(self.fileNameLabel,3,0,2,2)
        self.tab1.setLayout(mainLayout)

        self.selDock = dockarea.Dock('', size=(1000, 200))
        self.selDock.addWidget(self.tabs)
        self.addDock(self.selDock, 'bottom')
        
        
        
        
        
        
        
        self._scene = self.view.scene()
        self._viewBox = self.view.viewBox()
        #self._scene = QtGui.QGraphicsScene()
        #self._scene = FlowchartGraphicsView.FlowchartGraphicsScene()
        #self.view.setScene(self._scene)
        
        self.buildMenu()
        #self.ui.addNodeBtn.mouseReleaseEvent = self.addNodeBtnReleased
            
        self._scene.selectionChanged.connect(self.selectionChanged)
        self._scene.sigMouseHover.connect(self.hoverOver)
        #self.view.sigClicked.connect(self.showViewMenu)
        #self._scene.sigSceneContextMenu.connect(self.showViewMenu)
        #self._viewBox.sigActionPositionChanged.connect(self.menuPosChanged)
        self.combobox.currentIndexChanged.connect(self.setLoss)
        self.combobox1.currentIndexChanged.connect(self.setOptim)
        self.EPLineEdit.editingFinished.connect(self.setEP)
        self.BSLineEdit.editingFinished.connect(self.setBS)
        self.LRLineEdit.editingFinished.connect(self.setLR)


        self.btnTrain.clicked.connect(self.startTrain)
        self.btnStop.clicked.connect(self.stopTrain)
        self.btnInfer.clicked.connect(self.infer)
        self.thread = QtCore.QThreadPool()
        
        
    def textdlg(self):
        
        if self.dlg.exec():
            self.chart.outputNode.setLossTxt(self.dlg.text.toPlainText())
            

    def setLoss(self):
        losstxt = self.combobox.currentText()
        if losstxt == 'CE':
            loss = nn.CrossEntropyLoss()
        if losstxt == 'MSE':
            loss = nn.MSELoss()

        self.chart.outputNode.setLoss(loss)
        return 
    def setOptim(self):
        optim = self.combobox1.currentText()
        
        self.chart.outputNode.setOptim(optim)
        return 

    def setEP(self):
        try:
            self.chart.epochs = int(self.EPLineEdit.text())
            self.progress.setMaximum(int(self.EPLineEdit.text()))
        except:
            self.fileNameLabel.setText('Only Int Allowed')
        else:
            self.fileNameLabel.setText('')        
        

        return 
    def setValueP(self,value):
        self.progress.setValue(int(value))
        return     
    def setBS(self):
        try:
            self.chart.setBS(int(self.BSLineEdit.text()))
            
        except:
            self.fileNameLabel.setText('Only Int Allowed')
        else:
            self.fileNameLabel.setText('')        
        

        return 

    def setLR(self):
        try:
            self.chart.outputNode.setLR(float(self.LRLineEdit.text()))
            
        except:
            self.fileNameLabel.setText('Only float Allowed')
        else:
            self.fileNameLabel.setText('')        
        

        return 

    def startTrain(self):
        self.chart.widget().modules.canvas.axes.cla()
        self.thread.start(self.chart.train)
        
    def stopTrain(self):
        self.chart.stopTrain=True

    def infer(self):
        self.chart.stopTrain=True


                
    def reloadLibrary(self):
        #QtCore.QObject.disconnect(self.nodeMenu, QtCore.SIGNAL('triggered(QAction*)'), self.nodeMenuTriggered)
        self.nodeMenu.triggered.disconnect(self.nodeMenuTriggered)
        self.nodeMenu = None
        self.subMenus = []
        library.loadLibrary(reloadLibs=True)
        self.buildMenu()
        
    def buildMenu(self, pos=None):
        self.nodeMenu = QtGui.QMenu()
        self.subMenus = []
        for section, nodes in library.getNodeTree().items():
            menu = QtGui.QMenu(section)
            self.nodeMenu.addMenu(menu)
            for name in nodes:
                act = menu.addAction(name)
                act.nodeType = name
                act.pos = pos
            self.subMenus.append(menu)

        self.nodeMenu.triggered.connect(self.nodeMenuTriggered)
        return self.nodeMenu
    
    def menuPosChanged(self, pos):
        self.menuPos = pos
    
    def showViewMenu(self, ev):
        #QtGui.QPushButton.mouseReleaseEvent(self.ui.addNodeBtn, ev)
        #if ev.button() == QtCore.Qt.RightButton:
            #self.menuPos = self.view.mapToScene(ev.pos())
            #self.nodeMenu.popup(ev.globalPos())
        #print "Flowchart.showViewMenu called"

        #self.menuPos = ev.scenePos()
        self.buildMenu(ev.scenePos())
        self.nodeMenu.popup(ev.screenPos())
        
    def scene(self):
        return self._scene ## the GraphicsScene item

    def viewBox(self):
        return self._viewBox ## the viewBox that items should be added to

    def nodeMenuTriggered(self, action):
        nodeType = action.nodeType
        if action.pos is not None:
            pos = action.pos
        else:
            pos = self.menuPos
        pos = self.viewBox().mapSceneToView(pos)

        self.chart.createNode(nodeType, pos=pos)

    def buildSuperData(self,node):
        data ={}
        for n in node.subnodes:
            if isinstance(n,SuperNode):
                if n.exception!=None:

                    data[n.name()+'_exc']=self.buildSuperData(n)
                else:
                    data[n.name()]=self.buildSuperData(n)
            else:
                if n.exception!=None:
                    data[n.name()+'_exc']={'outputs': n.outputValues(), 'inputs': n.inputValues(),'exception':n.exception}
                else:
                    data[n.name()]={'outputs': n.outputValues(), 'inputs': n.inputValues()}

        return data

    def selectionChanged(self):
        #print "FlowchartWidget.selectionChanged called."
        items = self._scene.selectedItems()
        data = None
        if len(items) > 1:
            if hasattr(items[-1], 'node') and isinstance(items[-1].node, SuperNode):
                n = items[-1].node
                self.ctrl.select(n)
                if n.exception!=None:
                    data = {n.name()+'_exc':self.buildSuperData(n)}
                else:
                    data = {n.name():self.buildSuperData(n)}
                self.selNameLabel.setText(n.name())
                self.selDescLabel.setText("<b>%s</b>: %s" % (n.name(), 'Supernode'))
                self.selVizDescLabel.setText("<b>%s</b>: %s" % (n.name(), 'Supernode'))


                for it in items:
                    it.menu.actions()[3].setEnabled(True)
                datat = {'outputs': n.outputValues(), 'inputs': n.inputValues()}
                self.selVizTree.setData(datat, hideRoot=True)
            elif hasattr(items[-1], 'node') and isinstance(items[-1].node, Node):
                n = items[0].node
                self.ctrl.select(n)
                data = {'outputs': n.outputValues(), 'inputs': n.inputValues()}
                self.selNameLabel.setText(n.name())
                if hasattr(n, 'nodeName'):
                    self.selDescLabel.setText("<b>%s</b>: %s" % (n.nodeName, n.__class__.__doc__))
                    self.selVizDescLabel.setText("<b>%s</b>: %s" % (n.nodeName, n.__class__.__doc__))
                else:
                    self.selDescLabel.setText("")
                    self.selVizDescLabel.setText("")
                if n.exception is not None:
                    data['exception'] = n.exception
                data= {n.name():data}
                for it in items:
                    it.menu.actions()[3].setEnabled(True)
                self.selVizTree.setData(data, hideRoot=True)


                

        #print "     scene.selectedItems: ", items
        elif len(items) == 0:
            data = None
        elif hasattr(items[0], 'node') and isinstance(items[0].node, SuperNode):
                n = items[-1].node
                self.ctrl.select(n)
                if n.exception!=None:
                    data = {n.name()+'_exc':self.buildSuperData(n)}
                else:
                    data = {n.name():self.buildSuperData(n)}
                
                self.selNameLabel.setText(n.name())
                self.selDescLabel.setText("<b>%s</b>: %s" % (n.name(), 'Supernode'))
                self.selVizDescLabel.setText("<b>%s</b>: %s" % (n.name(), 'Supernode'))

                for it in items:
                    it.menu.actions()[3].setEnabled(True)
                datat = {'outputs': n.outputValues(), 'inputs': n.inputValues()}
                self.selVizTree.setData(datat, hideRoot=True)
        elif hasattr(items[0], 'node') and isinstance(items[0].node, Node):

                item = items[0]
                item.menu.actions()[3].setEnabled(False)          
                n = item.node
                self.ctrl.select(n)
                
                data = {'outputs': n.outputValues(), 'inputs': n.inputValues()}
                
                self.selNameLabel.setText(n.name())
                if hasattr(n, 'nodeName'):
                    self.selDescLabel.setText("<b>%s</b>: %s" % (n.nodeName, n.__class__.__doc__))
                    self.selVizDescLabel.setText("<b>%s</b>: %s" % (n.nodeName, n.__class__.__doc__))
                else:
                    self.selDescLabel.setText("")
                    self.selVizDescLabel.setText("")
                if n.exception is not None:
                    data['exception'] = n.exception
                data= {n.name():data}
                self.selVizTree.setData(data, hideRoot=True)

        self.selectedTree.setData(data, hideRoot=True)
    def hoverOver(self, items):
        #print "FlowchartWidget.hoverOver called."
        term = None
        for item in items:
            if item is self.hoverItem:
                return
            self.hoverItem = item

            if hasattr(item, 'term') and isinstance(item.term, Terminal):
                term = item.term
                break
        if term is None:
            self.hoverText.setPlainText("")
        else:
            val = term.value()
            if isinstance(val, ndarray):
                val = "%s %s %s" % (type(val).__name__, str(val.shape), str(val.dtype))
            else:
                val = str(val)
                # if len(val) > 400: #TODO
                #     val = val[:400] + "..."
            self.hoverText.setPlainText("%s.%s = %s" % (term.node().name(), term.name(), val))
            #self.hoverLabel.setCursorPosition(0)

    

    def clear(self):
        #self.outputTree.setData(None)
        self.selectedTree.setData(None)
        self.hoverText.setPlainText('')
        self.selNameLabel.setText('')
        self.selDescLabel.setText('')
        
        
class FlowchartNode(Node):
    pass

class DataTreeWidget(QtWidgets.QTreeWidget):
    """
    Widget for displaying hierarchical python data structures
    (eg, nested dicts, lists, and arrays)
    """
    def __init__(self, parent=None, data=None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setData(data)
        self.setColumnCount(3)
        self.setHeaderLabels(['key / index', 'type', 'value'])
        self.setAlternatingRowColors(True)

        
    def setData(self, data, hideRoot=False):
        """data should be a dictionary."""
        self.clear()
        self.widgets = []
        self.nodes = {}
        self.buildTree(data, self.invisibleRootItem(), hideRoot=hideRoot)
        self.resizeColumnToContents(0)

        
    def buildTree(self, data, parent, name='', hideRoot=False, path=(),red=False):

        typeStr, desc, childs, widget = self.parse(data)
        if not (name=='exception' and typeStr=='bool'):
            if hideRoot:
                node = parent
            else:

                node = QtWidgets.QTreeWidgetItem([name, "", ""])
                parent.addChild(node)
            label_n = QtWidgets.QLabel(name)
            if name.split('_')[-1]=='exc' :
                label_n.setStyleSheet("color: rgb(255, 0, 0);")
                label_n.setText(''.join(name.split('_')[0:-1]))
            if red :
                label_n.setStyleSheet("color: rgb(255, 0, 0);")
            # record the path to the node so it can be retrieved later
            # (this is used by DiffTreeWidget)
            self.nodes[path] = node
            # Truncate description and add text box if needed
            if len(desc) > 100:
                desc = desc[:97] + '...'
                if widget is None:
                    widget = QtWidgets.QPlainTextEdit(str(data))
                    widget.setMaximumHeight(200)
                    widget.setReadOnly(True)

            node.setText(1, typeStr)
            #node.setText(2, desc)
            label = QtWidgets.QLabel(desc)
            label.setWordWrap(True)
            self.setItemWidget(node, 2, label)
            node.setText(0,"")
            self.setItemWidget(node, 0, label_n)

            # Add widget to new subnode
            if widget is not None:
                self.widgets.append(widget)
                subnode = QtWidgets.QTreeWidgetItem(["", "", ""])
                node.addChild(subnode)
                self.setItemWidget(subnode, 0, widget)
                subnode.setFirstColumnSpanned(True)
            red = False 
            # recurse to children

   
            for key, data in childs.items():
                if key=='exception':
                    red = True
                else:
                    red = False 
                self.buildTree(data, node, str(key), path=path+(key,),red=red)

    def parse(self, data):
        """
        Given any python object, return:
          * type
          * a short string representation
          * a dict of sub-objects to be parsed
          * optional widget to display as sub-node
        """
        # defaults for all objects
        typeStr = type(data).__name__
        if typeStr == 'instance':
            typeStr += ": " + data.__class__.__name__
        widget = None
        desc = ""
        childs = {}
        
        # type-specific changes
        if isinstance(data, dict):
            desc = "length=%d" % len(data)
            if isinstance(data, OrderedDict):
                childs = data
            else:
                try:
                    childs = OrderedDict(sorted(data.items()))
                except TypeError: # if sorting falls
                    childs = OrderedDict(data.items())
        elif isinstance(data, (list, tuple)):
            desc = "length=%d" % len(data)
            childs = OrderedDict(enumerate(data))

        elif isinstance(data,torch.Tensor):
            data=data.detach().numpy()
            desc = "shape=%s dtype=%s" % (data.shape, data.dtype)


        elif isinstance(data, np.ndarray):
            desc = "shape=%s dtype=%s" % (data.shape, data.dtype)
            table =pg.TableWidget()
            table.setData(data)
            table.setMaximumHeight(200)
            widget = table
        elif isinstance(data, types.TracebackType):  ## convert traceback to a list of strings
            frames = list(map(str.strip, traceback.format_list(traceback.extract_tb(data))))
            #childs = OrderedDict([
                #(i, {'file': child[0], 'line': child[1], 'function': child[2], 'code': child[3]})
                #for i, child in enumerate(frames)])
            #childs = OrderedDict([(i, ch) for i,ch in enumerate(frames)])
            widget = QtWidgets.QPlainTextEdit('\n'.join(frames))
            widget.setMaximumHeight(200)
            widget.setReadOnly(True)
        else:
            desc = str(data)
        
        return typeStr, desc, childs, widget


class VizTreeWidget(QtWidgets.QTreeWidget):
    """
    Widget for displaying hierarchical python data structures
    (eg, nested dicts, lists, and arrays)
    """
    def __init__(self, parent=None, data=None):
        QtWidgets.QTreeWidget.__init__(self, parent)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setData(data)
        self.setColumnCount(3)
        self.setHeaderLabels(['key / index', 'type', 'value'])
        self.setAlternatingRowColors(True)

        
    def setData(self, data, hideRoot=False):
        """data should be a dictionary."""
        self.clear()
        self.widgets = []
        self.nodes = {}
        self.buildTree(data, self.invisibleRootItem(), hideRoot=hideRoot)
        self.expandToDepth(3)
        self.resizeColumnToContents(0)

        
    def buildTree(self, data, parent, name='', hideRoot=False, path=()):
        if hideRoot:
            node = parent
        else:
            node = QtWidgets.QTreeWidgetItem([name, "", ""])
            parent.addChild(node)
        
        # record the path to the node so it can be retrieved later
        # (this is used by DiffTreeWidget)
        self.nodes[path] = node

        typeStr, desc, childs, widget = self.parse(data)
        
        # Truncate description and add text box if needed
        if len(desc) > 100:
            desc = desc[:97] + '...'
            if widget is None:
                widget = QtWidgets.QPlainTextEdit(str(data))
                widget.setMaximumHeight(200)
                widget.setReadOnly(True)

        node.setText(1, typeStr)
        #node.setText(2, desc)
        label = QtWidgets.QLabel(desc)
        label.setWordWrap(True)
        self.setItemWidget(node, 2, label)
        # Add widget to new subnode
        if widget is not None:
            self.widgets.append(widget)
            subnode = QtWidgets.QTreeWidgetItem(["", "", ""])
            node.addChild(subnode)
            self.setItemWidget(subnode, 0, widget)
            subnode.setFirstColumnSpanned(True)
            
        # recurse to children
        for key, data in childs.items():
            self.buildTree(data, node, str(key), path=path+(key,))

    def parse(self, data):
        """
        Given any python object, return:
          * type
          * a short string representation
          * a dict of sub-objects to be parsed
          * optional widget to display as sub-node
        """
        # defaults for all objects
        typeStr = type(data).__name__
        if typeStr == 'instance':
            typeStr += ": " + data.__class__.__name__
        widget = None
        desc = ""
        childs = {}
        
        # type-specific changes
        if isinstance(data, dict):
            desc = "length=%d" % len(data)
            if isinstance(data, OrderedDict):
                childs = data
            else:
                try:
                    childs = OrderedDict(sorted(data.items()))
                except TypeError: # if sorting falls
                    childs = OrderedDict(data.items())
        elif isinstance(data, (list, tuple)):
            desc = "length=%d" % len(data)
            childs = OrderedDict(enumerate(data))

        elif isinstance(data,torch.Tensor):
            
            desc = "shape=%s dtype=%s" % (data.shape, data.dtype)

            if len(data.shape)>2:
                data = data.view(-1,data.shape[0])
            data=data.detach().numpy()
            table =MplCanvas(self, width=5, height=4, dpi=100)
            table.axes.imshow(data.T,interpolation='nearest',aspect='auto')
            table.setMaximumHeight(200)
            widget = table

        elif isinstance(data, np.ndarray):
            desc = "shape=%s dtype=%s" % (data.shape, data.dtype)
            table =pg.TableWidget()
            table.setData(data)
            table.setMaximumHeight(200)
            widget = table
        elif isinstance(data, types.TracebackType):  ## convert traceback to a list of strings
            frames = list(map(str.strip, traceback.format_list(traceback.extract_tb(data))))
            #childs = OrderedDict([
                #(i, {'file': child[0], 'line': child[1], 'function': child[2], 'code': child[3]})
                #for i, child in enumerate(frames)])
            #childs = OrderedDict([(i, ch) for i,ch in enumerate(frames)])
            widget = QtWidgets.QPlainTextEdit('\n'.join(frames))
            widget.setMaximumHeight(200)
            widget.setReadOnly(True)
        else:
            desc = str(data)
        
        return typeStr, desc, childs, widget
