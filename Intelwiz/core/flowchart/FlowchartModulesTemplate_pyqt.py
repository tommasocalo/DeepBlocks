# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './flowchart/FlowchartCtrlTemplate.ui'
#
# Created: Sun Sep  9 14:41:30 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui,QtWidgets
from PyQt5.QtWidgets import (QApplication,QLabel,QWidget, QGridLayout,QPushButton, QApplication)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(217, 499)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setMargin(0)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))


        self.moduleList = TreeWidget(Form)
        self.moduleList.setObjectName(_fromUtf8("ctrlList"))
        self.moduleList.headerItem().setText(0, _fromUtf8("1"))
        self.moduleList.header().setVisible(False)
        self.moduleList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.moduleList.header().setStretchLastSection(False)
        self.gridLayout.addWidget(self.moduleList, 0, 0, 1, 4)


        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QApplication.translate("Form", "Form", None))
 

from pyqtgraph.widgets.FeedbackButton import FeedbackButton
from pyqtgraph.widgets.TreeWidget import TreeWidget
