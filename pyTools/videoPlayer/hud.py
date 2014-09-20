__author__ = 'peter'

from PySide import QtCore
from PySide import QtGui

class HUD(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(HUD, self).__init__(*args, **kwargs)

        self.annotatorStr = None
        self.annotatorDisp = QtGui.QLabel(self)
        self.annotatorFont = QtGui.QFont('', 10)
        self.annotatorDisp.setFont(self.annotatorFont)
        self.behaviourStr = None
        self.behaviourDisp = QtGui.QLabel(self)
        self.behaviourFont = QtGui.QFont('', 10)
        self.behaviourDisp.setFont(self.behaviourFont)
        self.fileStr = None
        self.fileDisp = QtGui.QLabel(self)
        self.fileFont = QtGui.QFont('', 10)
        self.fileDisp.setFont(self.fileFont)
        self.frameStr = None
        self.frameDisp = QtGui.QLabel(self)
        self.frameFont = QtGui.QFont('', 10)
        self.frameDisp.setFont(self.frameFont)
        self.speedStr = None
        self.speedDisp = QtGui.QLabel(self)
        self.speedFont = QtGui.QFont('', 10)
        self.speedDisp.setFont(self.speedFont)
        self.modeStr = None
        self.modeDisp = QtGui.QLabel(self)
        self.modeFont = QtGui.QFont('', 10)
        self.modeDisp.setFont(self.modeFont)

        self.setAnnotator('')
        self.setBehaviour('')
        self.setFile('')
        self.setFrame('')


    def setAnnotator(self, annotatorStr, color=None):
        if color is not None:
            self.annotatorDisp.setStyleSheet("""
            QLabel {{
            color: {0}}}""".format(color.name()))
        else:
            self.annotatorDisp.setStyleSheet("""
            QLabel {
            color: #000000;}""")

        self.annotatorStr = annotatorStr
        self.annotatorDisp.setText(self.annotatorStr)
        self.annotatorDisp.adjustSize()
        self.updateElements()

    def setBehaviour(self, behaviourStr, color=None):
        if color is not None:
            self.behaviourDisp.setStyleSheet("""
            QLabel {{
            color: #000000;
            border-bottom-color: {0};
            border-top: transparent;
            border-left: transparent;
            border-right: transparent;
            border-width : 1.5px;
            border-style:solid; }}""".format(color.name()))
        else:
            self.behaviourDisp.setStyleSheet("""
            QLabel {{
            color: #000000;
            border-bottom-color: transparent;
            border-top: transparent;
            border-left: transparent;
            border-right: transparent;
            border-width : 1.5px;
            border-style:solid; }}""")


        self.behaviourStr = behaviourStr
        self.behaviourDisp.setText(self.behaviourStr)
        self.behaviourDisp.adjustSize()
        self.updateElements()

    def setFile(self, fileStr, color=None):
        if color is not None:
            self.fileDisp.setStyleSheet("""
            QLabel {{
            color: {0}}}""".format(color.name()))
        else:
            self.fileDisp.setStyleSheet("""
            QLabel {
            color: #000000;}""")

        self.fileStr = fileStr
        self.fileDisp.setText(self.fileStr)
        self.fileDisp.adjustSize()
        self.updateElements()

    def setFrame(self, frameStr, color=None):
        if color is not None:
            self.frameDisp.setStyleSheet("""
            QLabel {{
            color: {0}}}""".format(color.name()))
        else:
            self.frameDisp.setStyleSheet("""
            QLabel {
            color: #000000;}""")

        self.frameStr = frameStr
        self.frameDisp.setText(self.frameStr)
        self.frameDisp.adjustSize()
        self.updateElements()


    def setSpeed(self, speedStr, color=None):
        if color is not None:
            self.speedDisp.setStyleSheet("""
            QLabel {{
            color: {0}}}""".format(color.name()))
        else:
            self.speedDisp.setStyleSheet("""
            QLabel {
            color: #000000;}""")

        self.speedStr = "[{0}x]".format(speedStr)
        self.speedDisp.setText(self.speedStr)
        self.speedDisp.adjustSize()
        self.updateElements()
        

    def setMode(self, modeStr, color=None):
        if color is not None:
            self.modeDisp.setStyleSheet("""
            QLabel {{
            color: {0};
            border-bottom-color: {0};
            border-top: {0};
            border-left: {0};
            border-right: {0};
            border-width : 1.5px;
            border-style:solid; }}""".format(color.name()))
        else:
            self.modeDisp.setStyleSheet("""
            QLabel {{
            color: #000000;
            border-bottom-color: transparent;
            border-top: transparent;
            border-left: transparent;
            border-right: transparent;
            border-width : 1.5px;
            border-style:solid; }}""")

        self.modeStr = modeStr
        self.modeDisp.setText(self.modeStr)
        self.modeDisp.adjustSize()
        self.updateElements()


    def enterEvent(self, event):
        self.setVisible(False)
        super(HUD, self).enterEvent(event)

    def updateElements(self):
        tWidth = 10
        y = 10
        self.fileDisp.move(tWidth, y)
        y += 14

        w = tWidth
        self.modeDisp.move(w, y)
        w = 150
        self.frameDisp.move(w, y)
        w += tWidth + self.frameDisp.rect().width()
        self.speedDisp.move(w, y)
        y += 16

        self.annotatorDisp.move(tWidth, y)
        y += 12

        self.behaviourDisp.move(tWidth - 5, y)
        y += 14

        self.adjustSize()

    def setColor(self, color):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)