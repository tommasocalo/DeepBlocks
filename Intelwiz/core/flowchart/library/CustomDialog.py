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

class CustomDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.text = QtGui.QTextEdit()
        self.text.setTabStopWidth(60)
        self.text.setPlainText("# Access inputs as args['input_name']\nreturn {'output': None} ## one key per output terminal")
        self.setMinimumSize(630, 300)
        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel("Something happened, is that OK?")
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
