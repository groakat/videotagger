# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'videoPlayer.ui'
#
# Created: Sat Feb 22 01:24:43 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1312, 826)
        self.pb_startVideo = QtGui.QPushButton(Form)
        self.pb_startVideo.setGeometry(QtCore.QRect(1120, 570, 151, 23))
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
        self.lbl_v1.setGeometry(QtCore.QRect(1100, 520, 111, 16))
        self.lbl_v1.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_v1.setObjectName("lbl_v1")
        self.pb_stopVideo = QtGui.QPushButton(Form)
        self.pb_stopVideo.setGeometry(QtCore.QRect(1120, 590, 151, 23))
        self.pb_stopVideo.setObjectName("pb_stopVideo")
        self.pb_connect2server = QtGui.QPushButton(Form)
        self.pb_connect2server.setGeometry(QtCore.QRect(1120, 610, 151, 23))
        self.pb_connect2server.setObjectName("pb_connect2server")
        self.pb_compDist = QtGui.QPushButton(Form)
        self.pb_compDist.setGeometry(QtCore.QRect(1120, 630, 151, 23))
        self.pb_compDist.setObjectName("pb_compDist")
        self.pb_test = QtGui.QPushButton(Form)
        self.pb_test.setGeometry(QtCore.QRect(1120, 650, 151, 23))
        self.pb_test.setObjectName("pb_test")
        self.cb_trajectory = QtGui.QCheckBox(Form)
        self.cb_trajectory.setGeometry(QtCore.QRect(1130, 550, 161, 21))
        self.cb_trajectory.setObjectName("cb_trajectory")
        self.pb_eraseAnno = QtGui.QPushButton(Form)
        self.pb_eraseAnno.setGeometry(QtCore.QRect(1120, 690, 151, 23))
        self.pb_eraseAnno.setObjectName("pb_eraseAnno")
        self.pb_addAnno = QtGui.QPushButton(Form)
        self.pb_addAnno.setGeometry(QtCore.QRect(1120, 670, 151, 23))
        self.pb_addAnno.setObjectName("pb_addAnno")
        self.speed_lbl = QtGui.QLabel(Form)
        self.speed_lbl.setGeometry(QtCore.QRect(1200, 520, 91, 16))
        self.speed_lbl.setObjectName("speed_lbl")
        self.lbl_eraser = QtGui.QLabel(Form)
        self.lbl_eraser.setGeometry(QtCore.QRect(10, 500, 51, 61))
        self.lbl_eraser.setText("")
        self.lbl_eraser.setPixmap(QtGui.QPixmap("Actions-draw-eraser-icon.png"))
        self.lbl_eraser.setScaledContents(True)
        self.lbl_eraser.setObjectName("lbl_eraser")
        self.lbl_vial = QtGui.QLabel(Form)
        self.lbl_vial.setGeometry(QtCore.QRect(980, 520, 57, 14))
        self.lbl_vial.setObjectName("lbl_vial")
        self.progBar = QtGui.QProgressBar(Form)
        self.progBar.setGeometry(QtCore.QRect(250, 400, 571, 20))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(225, 225, 225))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(130, 130, 130))
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
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(232, 69, 48))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(225, 225, 225))
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
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(225, 225, 225))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(130, 130, 130))
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
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(232, 69, 48))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(225, 225, 225))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(225, 225, 225))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(130, 130, 130))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(97, 97, 97))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(205, 200, 198))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(195, 195, 195))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipText, brush)
        self.progBar.setPalette(palette)
        self.progBar.setProperty("value", 24)
        self.progBar.setObjectName("progBar")
        self.tabWidget = QtGui.QTabWidget(Form)
        self.tabWidget.setGeometry(QtCore.QRect(30, 560, 1071, 251))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtGui.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.sldr_paths = QtGui.QSlider(self.tab_1)
        self.sldr_paths.setGeometry(QtCore.QRect(20, 130, 871, 23))
        self.sldr_paths.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_paths.setObjectName("sldr_paths")
        self.lv_frames = QtGui.QListView(self.tab_1)
        self.lv_frames.setGeometry(QtCore.QRect(910, 10, 61, 121))
        self.lv_frames.setObjectName("lv_frames")
        self.lv_jmp = QtGui.QListView(self.tab_1)
        self.lv_jmp.setGeometry(QtCore.QRect(980, 10, 61, 121))
        self.lv_jmp.setObjectName("lv_jmp")
        self.lv_paths = QtGui.QListView(self.tab_1)
        self.lv_paths.setGeometry(QtCore.QRect(10, 10, 891, 121))
        self.lv_paths.setObjectName("lv_paths")
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.frameView = FrameViewWidget(self.tab_2)
        self.frameView.setGeometry(QtCore.QRect(10, -10, 941, 221))
        self.frameView.setObjectName("frameView")
        self.tabWidget.addTab(self.tab_2, "")

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_startVideo.setText(QtGui.QApplication.translate("Form", "start video", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_v0.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_v1.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_stopVideo.setText(QtGui.QApplication.translate("Form", "stop video", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_connect2server.setText(QtGui.QApplication.translate("Form", "connect to server", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_compDist.setText(QtGui.QApplication.translate("Form", "compute distances", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_test.setText(QtGui.QApplication.translate("Form", "test button", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_trajectory.setText(QtGui.QApplication.translate("Form", "Show Trajectory", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_eraseAnno.setText(QtGui.QApplication.translate("Form", "erase annotation", None, QtGui.QApplication.UnicodeUTF8))
        self.pb_addAnno.setText(QtGui.QApplication.translate("Form", "add annotation", None, QtGui.QApplication.UnicodeUTF8))
        self.speed_lbl.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_vial.setText(QtGui.QApplication.translate("Form", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.progBar.setFormat(QtGui.QApplication.translate("Form", "%p%", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), QtGui.QApplication.translate("Form", "Filenames", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("Form", "Frame View", None, QtGui.QApplication.UnicodeUTF8))

from FrameViewWidget import FrameViewWidget
