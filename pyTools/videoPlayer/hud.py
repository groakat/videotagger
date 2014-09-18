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

        self.setAnnotator('')
        self.setBehaviour('')
        self.setFile('')
        self.setFrame('')


    def setAnnotator(self, annotatorStr, color=None):
        if color is None:
            color = QtGui.QColor(0,0,0)
        self.annotatorStr = annotatorStr
        self.annotatorDisp.setText(self.annotatorStr)
        self.annotatorDisp.adjustSize()
        self.updateElements()

    def setBehaviour(self, behaviourStr, color=None):
        if color is None:
            color = QtGui.QColor(0,0,0)

        self.behaviourStr = behaviourStr
        self.behaviourDisp.setText(self.behaviourStr)
        self.behaviourDisp.adjustSize()
        self.updateElements()

    def setFile(self, fileStr, color=None):
        if color is None:
            color = QtGui.QColor(0,0,0)

        self.fileStr = fileStr
        self.fileDisp.setText(self.fileStr)
        self.fileDisp.adjustSize()
        self.updateElements()

    def setFrame(self, frameStr, color=None):
        if color is None:
            color = QtGui.QColor(0,0,0)

        self.frameStr = frameStr
        self.frameDisp.setText(self.frameStr)
        self.frameDisp.adjustSize()
        self.updateElements()

    def enterEvent(self, event):
        self.setVisible(False)
        super(HUD, self).enterEvent(event)

    def updateElements(self):
        tWidth = 10
        y = 10
        self.fileDisp.move(tWidth, y)
        y += 12

        self.frameDisp.move(tWidth, y)
        y += 12

        self.annotatorDisp.move(tWidth, y)
        y += 12

        self.behaviourDisp.move(tWidth, y)
        y += 12

        self.adjustSize()

    def setColor(self, color):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)



        pass
        # self.setPen(QtGui.QPen(color))