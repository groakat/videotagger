# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'videoPlayer.ui'
#
# Created: Mon Aug 12 00:28:34 2013
#      by: PyQt4 UI code generator 4.10.1
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
        Form.resize(1120, 758)
        self.pb_startVideo = QtGui.QPushButton(Form)
        self.pb_startVideo.setGeometry(QtCore.QRect(940, 580, 151, 23))
        self.pb_startVideo.setObjectName(_fromUtf8("pb_startVideo"))
        self.label = QtGui.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(10, 10, 1000, 550))
        self.label.setObjectName(_fromUtf8("label"))
        self.lbl_v0 = QtGui.QLabel(Form)
        self.lbl_v0.setGeometry(QtCore.QRect(70, 530, 841, 16))
        self.lbl_v0.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_v0.setLineWidth(1)
        self.lbl_v0.setObjectName(_fromUtf8("lbl_v0"))
        self.lbl_v1 = QtGui.QLabel(Form)
        self.lbl_v1.setGeometry(QtCore.QRect(920, 530, 111, 16))
        self.lbl_v1.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_v1.setObjectName(_fromUtf8("lbl_v1"))
        self.lv_paths = QtGui.QListView(Form)
        self.lv_paths.setGeometry(QtCore.QRect(60, 570, 721, 121))
        self.lv_paths.setObjectName(_fromUtf8("lv_paths"))
        self.pb_stopVideo = QtGui.QPushButton(Form)
        self.pb_stopVideo.setGeometry(QtCore.QRect(940, 600, 151, 23))
        self.pb_stopVideo.setObjectName(_fromUtf8("pb_stopVideo"))
        self.sldr_paths = QtGui.QSlider(Form)
        self.sldr_paths.setGeometry(QtCore.QRect(70, 690, 701, 23))
        self.sldr_paths.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_paths.setObjectName(_fromUtf8("sldr_paths"))
        self.pb_jmp2frame = QtGui.QPushButton(Form)
        self.pb_jmp2frame.setGeometry(QtCore.QRect(940, 620, 151, 23))
        self.pb_jmp2frame.setObjectName(_fromUtf8("pb_jmp2frame"))
        self.lv_frames = QtGui.QListView(Form)
        self.lv_frames.setGeometry(QtCore.QRect(780, 571, 61, 121))
        self.lv_frames.setObjectName(_fromUtf8("lv_frames"))
        self.lv_jmp = QtGui.QListView(Form)
        self.lv_jmp.setGeometry(QtCore.QRect(840, 571, 61, 121))
        self.lv_jmp.setObjectName(_fromUtf8("lv_jmp"))
        self.pb_compDist = QtGui.QPushButton(Form)
        self.pb_compDist.setGeometry(QtCore.QRect(940, 640, 151, 23))
        self.pb_compDist.setObjectName(_fromUtf8("pb_compDist"))
        self.pb_test = QtGui.QPushButton(Form)
        self.pb_test.setGeometry(QtCore.QRect(940, 660, 151, 23))
        self.pb_test.setObjectName(_fromUtf8("pb_test"))
        self.cb_trajectory = QtGui.QCheckBox(Form)
        self.cb_trajectory.setGeometry(QtCore.QRect(950, 560, 161, 21))
        self.cb_trajectory.setObjectName(_fromUtf8("cb_trajectory"))
        self.pb_eraseAnno = QtGui.QPushButton(Form)
        self.pb_eraseAnno.setGeometry(QtCore.QRect(940, 700, 151, 23))
        self.pb_eraseAnno.setObjectName(_fromUtf8("pb_eraseAnno"))
        self.pb_addAnno = QtGui.QPushButton(Form)
        self.pb_addAnno.setGeometry(QtCore.QRect(940, 680, 151, 23))
        self.pb_addAnno.setObjectName(_fromUtf8("pb_addAnno"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.pb_startVideo.setText(_translate("Form", "start video", None))
        self.label.setText(_translate("Form", "TextLabel", None))
        self.lbl_v0.setText(_translate("Form", "TextLabel", None))
        self.lbl_v1.setText(_translate("Form", "TextLabel", None))
        self.pb_stopVideo.setText(_translate("Form", "stop video", None))
        self.pb_jmp2frame.setText(_translate("Form", "jump to frame", None))
        self.pb_compDist.setText(_translate("Form", "compute distances", None))
        self.pb_test.setText(_translate("Form", "test button", None))
        self.cb_trajectory.setText(_translate("Form", "Show Trajectory", None))
        self.pb_eraseAnno.setText(_translate("Form", "erase annotation", None))
        self.pb_addAnno.setText(_translate("Form", "add annotation", None))

