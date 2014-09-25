# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'videoTagger.ui'
#
# Created: Thu May  9 19:29:35 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(1120, 723)
        self.pb_startVideo = QtGui.QPushButton(Form)
        self.pb_startVideo.setGeometry(QtCore.QRect(950, 630, 151, 23))
        self.pb_startVideo.setObjectName(_fromUtf8("pb_startVideo"))
        self.label = QtGui.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(10, 10, 1000, 550))
        self.label.setObjectName(_fromUtf8("label"))
        self.lbl_v0 = QtGui.QLabel(Form)
        self.lbl_v0.setGeometry(QtCore.QRect(180, 500, 57, 14))
        self.lbl_v0.setObjectName(_fromUtf8("lbl_v0"))
        self.lbl_v1 = QtGui.QLabel(Form)
        self.lbl_v1.setGeometry(QtCore.QRect(520, 500, 57, 14))
        self.lbl_v1.setObjectName(_fromUtf8("lbl_v1"))
        self.lbl_v2 = QtGui.QLabel(Form)
        self.lbl_v2.setGeometry(QtCore.QRect(360, 490, 57, 14))
        self.lbl_v2.setObjectName(_fromUtf8("lbl_v2"))
        self.lbl_v3 = QtGui.QLabel(Form)
        self.lbl_v3.setGeometry(QtCore.QRect(660, 500, 57, 14))
        self.lbl_v3.setObjectName(_fromUtf8("lbl_v3"))
        self.lv_paths = QtGui.QListView(Form)
        self.lv_paths.setGeometry(QtCore.QRect(180, 580, 721, 121))
        self.lv_paths.setObjectName(_fromUtf8("lv_paths"))
        self.pb_stopVideo = QtGui.QPushButton(Form)
        self.pb_stopVideo.setGeometry(QtCore.QRect(950, 660, 151, 23))
        self.pb_stopVideo.setObjectName(_fromUtf8("pb_stopVideo"))
        self.sldr_paths = QtGui.QSlider(Form)
        self.sldr_paths.setGeometry(QtCore.QRect(190, 700, 701, 23))
        self.sldr_paths.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_paths.setObjectName(_fromUtf8("sldr_paths"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.pb_startVideo.setText(_translate("Form", "start video", None))
        self.label.setText(_translate("Form", "TextLabel", None))
        self.lbl_v0.setText(_translate("Form", "TextLabel", None))
        self.lbl_v1.setText(_translate("Form", "TextLabel", None))
        self.lbl_v2.setText(_translate("Form", "TextLabel", None))
        self.lbl_v3.setText(_translate("Form", "TextLabel", None))
        self.pb_stopVideo.setText(_translate("Form", "stop video", None))

