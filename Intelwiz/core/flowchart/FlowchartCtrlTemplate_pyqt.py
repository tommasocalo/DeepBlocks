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

        self.ctrlList = TreeWidget(Form)
        self.ctrlList.setObjectName(_fromUtf8("ctrlList"))
        self.ctrlList.headerItem().setText(0, "Network")
        self.ctrlList.headerItem().setText(1, "")

        self.ctrlList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.ctrlList.header().setStretchLastSection(False)
        self.gridLayout.addWidget(self.ctrlList, 0, 0, 1, 4)

        self.loadBtn = QPushButton(Form)
        self.loadBtn.setObjectName(_fromUtf8("loadBtn"))
        self.gridLayout.addWidget(self.loadBtn, 3, 0, 1, 1)

        self.saveBtn = FeedbackButton(Form)
        self.saveBtn.setObjectName(_fromUtf8("saveBtn"))
        self.gridLayout.addWidget(self.saveBtn, 3, 1, 1, 2)

        self.saveAsBtn = FeedbackButton(Form)
        self.saveAsBtn.setObjectName(_fromUtf8("saveAsBtn"))
        self.gridLayout.addWidget(self.saveAsBtn, 3, 3, 1, 1)

        self.reloadBtn = FeedbackButton(Form)
        self.reloadBtn.setCheckable(False)
        self.reloadBtn.setFlat(False)
        self.reloadBtn.setObjectName(_fromUtf8("reloadBtn"))
        self.gridLayout.addWidget(self.reloadBtn, 4, 0, 1, 2)

        self.showChartBtn = QPushButton(Form)
        self.showChartBtn.setCheckable(True)
        self.showChartBtn.setObjectName(_fromUtf8("showChartBtn"))
        self.gridLayout.addWidget(self.showChartBtn, 4, 2, 1, 2)

        self.fileNameLabel = QLabel(Form)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setText(_fromUtf8("unsaved"))
        self.fileNameLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.fileNameLabel.setObjectName(_fromUtf8("fileNameLabel"))
        self.gridLayout.addWidget(self.fileNameLabel, 1, 0, 1, 3)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QApplication.translate("Form", "Form", None))
        self.loadBtn.setText(QApplication.translate("Form", "Load..", None))
        self.saveBtn.setText(QApplication.translate("Form", "Save", None))
        self.saveAsBtn.setText(QApplication.translate("Form", "As..", None))
        self.reloadBtn.setText(QApplication.translate("Form", "Reload Libs", None))
        self.showChartBtn.setText(QApplication.translate("Form", "Flowchart", None))

from pyqtgraph.widgets.FeedbackButton import FeedbackButton
from pyqtgraph.widgets.TreeWidget import TreeWidget
