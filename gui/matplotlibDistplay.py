# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'matplotlibDisplay.ui'
#
# Created: Fri Jan 31 16:09:35 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1056, 687)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.confWidget1 = MplWidget(self.centralwidget)
        self.confWidget1.setGeometry(QtCore.QRect(10, 30, 501, 51))
        self.confWidget1.setObjectName("confWidget1")
        self.btn_redraw = QtGui.QPushButton(self.centralwidget)
        self.btn_redraw.setGeometry(QtCore.QRect(740, 390, 94, 24))
        self.btn_redraw.setObjectName("btn_redraw")
        self.confWidget2 = MplWidget(self.centralwidget)
        self.confWidget2.setGeometry(QtCore.QRect(10, 90, 501, 51))
        self.confWidget2.setObjectName("confWidget2")
        self.confWidget3 = MplWidget(self.centralwidget)
        self.confWidget3.setGeometry(QtCore.QRect(10, 150, 501, 51))
        self.confWidget3.setObjectName("confWidget3")
        self.confWidget4 = MplWidget(self.centralwidget)
        self.confWidget4.setGeometry(QtCore.QRect(10, 210, 501, 51))
        self.confWidget4.setObjectName("confWidget4")
        self.verticalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(110, 330, 521, 171))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.btn_generateData = QtGui.QPushButton(self.centralwidget)
        self.btn_generateData.setGeometry(QtCore.QRect(740, 320, 94, 24))
        self.btn_generateData.setObjectName("btn_generateData")
        self.btn_loadData = QtGui.QPushButton(self.centralwidget)
        self.btn_loadData.setGeometry(QtCore.QRect(740, 360, 94, 24))
        self.btn_loadData.setObjectName("btn_loadData")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1056, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btn_redraw.setText(QtGui.QApplication.translate("MainWindow", "redraw", None, QtGui.QApplication.UnicodeUTF8))
        self.btn_generateData.setText(QtGui.QApplication.translate("MainWindow", "generate data", None, QtGui.QApplication.UnicodeUTF8))
        self.btn_loadData.setText(QtGui.QApplication.translate("MainWindow", "load data", None, QtGui.QApplication.UnicodeUTF8))

from mplwidget import MplWidget
