# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FrameViewWidget.ui'
#
# Created: Mon Feb 17 08:32:34 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FrameViewWidget(object):
    def setupUi(self, FrameViewWidget):
        FrameViewWidget.setObjectName("FrameViewWidget")
        FrameViewWidget.resize(603, 221)
        self.confWidget1 = MplWidget(FrameViewWidget)
        self.confWidget1.setGeometry(QtCore.QRect(0, 10, 501, 51))
        self.confWidget1.setObjectName("confWidget1")
        self.confWidget3 = MplWidget(FrameViewWidget)
        self.confWidget3.setGeometry(QtCore.QRect(0, 110, 501, 51))
        self.confWidget3.setObjectName("confWidget3")
        self.le_max = QtGui.QLineEdit(FrameViewWidget)
        self.le_max.setGeometry(QtCore.QRect(530, 40, 61, 23))
        self.le_max.setObjectName("le_max")
        self.confWidget4 = MplWidget(FrameViewWidget)
        self.confWidget4.setGeometry(QtCore.QRect(0, 160, 501, 51))
        self.confWidget4.setObjectName("confWidget4")
        self.btn_set = QtGui.QPushButton(FrameViewWidget)
        self.btn_set.setGeometry(QtCore.QRect(540, 70, 41, 41))
        self.btn_set.setObjectName("btn_set")
        self.w_colourbar = MplWidget(FrameViewWidget)
        self.w_colourbar.setGeometry(QtCore.QRect(500, 10, 31, 201))
        self.w_colourbar.setObjectName("w_colourbar")
        self.le_min = QtGui.QLineEdit(FrameViewWidget)
        self.le_min.setGeometry(QtCore.QRect(530, 160, 61, 23))
        self.le_min.setObjectName("le_min")
        self.btn_clear = QtGui.QPushButton(FrameViewWidget)
        self.btn_clear.setGeometry(QtCore.QRect(540, 110, 41, 41))
        self.btn_clear.setObjectName("btn_clear")
        self.confWidget2 = MplWidget(FrameViewWidget)
        self.confWidget2.setGeometry(QtCore.QRect(0, 60, 501, 51))
        self.confWidget2.setObjectName("confWidget2")

        self.retranslateUi(FrameViewWidget)
        QtCore.QMetaObject.connectSlotsByName(FrameViewWidget)

    def retranslateUi(self, FrameViewWidget):
        FrameViewWidget.setWindowTitle(QtGui.QApplication.translate("FrameViewWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.btn_set.setText(QtGui.QApplication.translate("FrameViewWidget", "set", None, QtGui.QApplication.UnicodeUTF8))
        self.btn_clear.setText(QtGui.QApplication.translate("FrameViewWidget", "clear", None, QtGui.QApplication.UnicodeUTF8))

from mplwidget import MplWidget
