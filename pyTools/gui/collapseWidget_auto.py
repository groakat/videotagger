# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'collapseWidget.ui'
#
# Created: Tue Mar  4 20:50:27 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_collapseWidget(object):
    def setupUi(self, collapseWidget):
        collapseWidget.setObjectName("collapseWidget")
        collapseWidget.resize(748, 662)
        self.horizontalLayout = QtGui.QHBoxLayout(collapseWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lay_main = QtGui.QHBoxLayout()
        self.lay_main.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.lay_main.setObjectName("lay_main")
        self.mainWidget = QtGui.QWidget(collapseWidget)
        self.mainWidget.setObjectName("mainWidget")
        self.lay_main.addWidget(self.mainWidget)
        self.vLine = QtGui.QFrame(collapseWidget)
        self.vLine.setFrameShape(QtGui.QFrame.VLine)
        self.vLine.setFrameShadow(QtGui.QFrame.Sunken)
        self.vLine.setObjectName("vLine")
        self.lay_main.addWidget(self.vLine)
        self.btn_swap = QtGui.QPushButton(collapseWidget)
        self.btn_swap.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../icon/upArrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_swap.setIcon(icon)
        self.btn_swap.setIconSize(QtCore.QSize(10, 10))
        self.btn_swap.setFlat(True)
        self.btn_swap.setObjectName("btn_swap")
        self.lay_main.addWidget(self.btn_swap)
        self.horizontalLayout.addLayout(self.lay_main)

        self.retranslateUi(collapseWidget)
        QtCore.QMetaObject.connectSlotsByName(collapseWidget)

    def retranslateUi(self, collapseWidget):
        collapseWidget.setWindowTitle(QtGui.QApplication.translate("collapseWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))

