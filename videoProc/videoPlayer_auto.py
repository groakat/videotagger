# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'videoPlayer.ui'
#
# Created: Thu Sep 26 23:09:21 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1120, 758)
        self.pb_startVideo = QtGui.QPushButton(Form)
        self.pb_startVideo.setGeometry(QtCore.QRect(940, 580, 151, 23))
        self.pb_startVideo.setObjectName("pb_startVideo")
        self.label = QtGui.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(10, 10, 1000, 550))
        self.label.setObjectName("label")
        self.lbl_v0 = QtGui.QLabel(Form)
        self.lbl_v0.setGeometry(QtCore.QRect(70, 530, 841, 16))
        self.lbl_v0.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_v0.setLineWidth(1)
        self.lbl_v0.setObjectName("lbl_v0")
        self.lbl_v1 = QtGui.QLabel(Form)
        self.lbl_v1.setGeometry(QtCore.QRect(920, 530, 111, 16))
        self.lbl_v1.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_v1.setObjectName("lbl_v1")
        self.lv_paths = QtGui.QListView(Form)
        self.lv_paths.setGeometry(QtCore.QRect(60, 570, 721, 121))
        self.lv_paths.setObjectName("lv_paths")
        self.pb_stopVideo = QtGui.QPushButton(Form)
        self.pb_stopVideo.setGeometry(QtCore.QRect(940, 600, 151, 23))
        self.pb_stopVideo.setObjectName("pb_stopVideo")
        self.sldr_paths = QtGui.QSlider(Form)
        self.sldr_paths.setGeometry(QtCore.QRect(70, 690, 701, 23))
        self.sldr_paths.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_paths.setObjectName("sldr_paths")
        self.pb_jmp2frame = QtGui.QPushButton(Form)
        self.pb_jmp2frame.setGeometry(QtCore.QRect(940, 620, 151, 23))
        self.pb_jmp2frame.setObjectName("pb_jmp2frame")
        self.lv_frames = QtGui.QListView(Form)
        self.lv_frames.setGeometry(QtCore.QRect(780, 571, 61, 121))
        self.lv_frames.setObjectName("lv_frames")
        self.lv_jmp = QtGui.QListView(Form)
        self.lv_jmp.setGeometry(QtCore.QRect(840, 571, 61, 121))
        self.lv_jmp.setObjectName("lv_jmp")
        self.pb_compDist = QtGui.QPushButton(Form)
        self.pb_compDist.setGeometry(QtCore.QRect(940, 640, 151, 23))
        self.pb_compDist.setObjectName("pb_compDist")
        self.pb_test = QtGui.QPushButton(Form)
        self.pb_test.setGeometry(QtCore.QRect(940, 660, 151, 23))
        self.pb_test.setObjectName("pb_test")
        self.cb_trajectory = QtGui.QCheckBox(Form)
        self.cb_trajectory.setGeometry(QtCore.QRect(950, 560, 161, 21))
        self.cb_trajectory.setObjectName("cb_trajectory")
        self.pb_eraseAnno = QtGui.QPushButton(Form)
        self.pb_eraseAnno.setGeometry(QtCore.QRect(940, 700, 151, 23))
        self.pb_eraseAnno.setObjectName("pb_eraseAnno")
        self.pb_addAnno = QtGui.QPushButton(Form)
        self.pb_addAnno.setGeometry(QtCore.QRect(940, 680, 151, 23))
        self.pb_addAnno.setObjectName("pb_addAnno")
        self.speed_lbl = QtGui.QLabel(Form)
        self.speed_lbl.setGeometry(QtCore.QRect(1020, 530, 91, 16))
        self.speed_lbl.setObjectName("speed_lbl")
        self.lbl_eraser = QtGui.QLabel(Form)
        self.lbl_eraser.setGeometry(QtCore.QRect(10, 500, 51, 61))
        self.lbl_eraser.setText("")
        self.lbl_eraser.setPixmap(QtGui.QPixmap("Actions-draw-eraser-icon.png"))
        self.lbl_eraser.setScaledContents(True)
        self.lbl_eraser.setObjectName("lbl_eraser")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_startVideo.setText(QtGui.QApplication.translate("Form", "start video", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_v0.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_v1.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_stopVideo.setText(QtGui.QApplication.translate("Form", "stop video", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_jmp2frame.setText(QtGui.QApplication.translate("Form", "jump to frame", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_compDist.setText(QtGui.QApplication.translate("Form", "compute distances", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_test.setText(QtGui.QApplication.translate("Form", "test button", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_trajectory.setText(QtGui.QApplication.translate("Form", "Show Trajectory", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_eraseAnno.setText(QtGui.QApplication.translate("Form", "erase annotation", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_addAnno.setText(QtGui.QApplication.translate("Form", "add annotation", None, QtGui.QApplication.UnicodeUTF8))
        self.speed_lbl.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))

