# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'videoPlayer.ui'
#
# Created: Sun Aug 11 21:03:19 2013
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
        self.lbl_v0.setGeometry(QtCore.QRect(160, 720, 57, 14))
        self.lbl_v0.setFrameShape(QtGui.QFrame.Box)
        self.lbl_v0.setLineWidth(1)
        self.lbl_v0.setObjectName(_fromUtf8("lbl_v0"))
        self.lbl_v1 = QtGui.QLabel(Form)
        self.lbl_v1.setGeometry(QtCore.QRect(500, 720, 57, 14))
        self.lbl_v1.setFrameShape(QtGui.QFrame.Box)
        self.lbl_v1.setObjectName(_fromUtf8("lbl_v1"))
        self.lbl_v2 = QtGui.QLabel(Form)
        self.lbl_v2.setGeometry(QtCore.QRect(340, 710, 57, 14))
        self.lbl_v2.setFrameShape(QtGui.QFrame.Box)
        self.lbl_v2.setObjectName(_fromUtf8("lbl_v2"))
        self.lbl_v3 = QtGui.QLabel(Form)
        self.lbl_v3.setGeometry(QtCore.QRect(640, 720, 57, 14))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 90, 148))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(239, 49, 116))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(149, 6, 56))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(239, 132, 169))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 90, 148))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(239, 49, 116))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(149, 6, 56))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(239, 132, 169))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 90, 148))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(239, 49, 116))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(149, 6, 56))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(111, 4, 42))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(223, 9, 84))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipText, brush)
        self.lbl_v3.setPalette(palette)
        self.lbl_v3.setFrameShape(QtGui.QFrame.Box)
        self.lbl_v3.setFrameShadow(QtGui.QFrame.Plain)
        self.lbl_v3.setObjectName(_fromUtf8("lbl_v3"))
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
        self.lbl_v0_full = QtGui.QLabel(Form)
        self.lbl_v0_full.setGeometry(QtCore.QRect(1040, 50, 64, 64))
        self.lbl_v0_full.setObjectName(_fromUtf8("lbl_v0_full"))
        self.lbl_v1_full = QtGui.QLabel(Form)
        self.lbl_v1_full.setGeometry(QtCore.QRect(1040, 120, 64, 64))
        self.lbl_v1_full.setObjectName(_fromUtf8("lbl_v1_full"))
        self.lbl_v2_full = QtGui.QLabel(Form)
        self.lbl_v2_full.setGeometry(QtCore.QRect(1040, 200, 64, 64))
        self.lbl_v2_full.setObjectName(_fromUtf8("lbl_v2_full"))
        self.lbl_v3_full = QtGui.QLabel(Form)
        self.lbl_v3_full.setGeometry(QtCore.QRect(1040, 270, 64, 64))
        self.lbl_v3_full.setObjectName(_fromUtf8("lbl_v3_full"))
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
        self.lbl_v2.setText(_translate("Form", "TextLabel", None))
        self.lbl_v3.setText(_translate("Form", "TextLabel", None))
        self.pb_stopVideo.setText(_translate("Form", "stop video", None))
        self.pb_jmp2frame.setText(_translate("Form", "jump to frame", None))
        self.pb_compDist.setText(_translate("Form", "compute distances", None))
        self.pb_test.setText(_translate("Form", "test button", None))
        self.lbl_v0_full.setText(_translate("Form", "TextLabel", None))
        self.lbl_v1_full.setText(_translate("Form", "TextLabel", None))
        self.lbl_v2_full.setText(_translate("Form", "TextLabel", None))
        self.lbl_v3_full.setText(_translate("Form", "TextLabel", None))
        self.cb_trajectory.setText(_translate("Form", "Show Trajectory", None))
        self.pb_eraseAnno.setText(_translate("Form", "erase annotation", None))
        self.pb_addAnno.setText(_translate("Form", "add annotation", None))

