# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FrameViewWidget.ui'
#
# Created: Mon Feb  3 15:41:23 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

from time import time
import sys , copy
sys.path.append("/home/peter/phd/code")
from pyTools.misc.FrameDataVisualization import FrameDataView, \
                                FrameDataVisualizationTreeTrajectories
                                
from pyTools.gui.FrameViewWidget_auto import Ui_FrameViewWidget
from pyTools.gui.mplwidget import MplWidget

class FrameViewWidget(QtGui.QWidget, Ui_FrameViewWidget):
    """Widget defined in Qt Designer"""
    def __init__(self, parent = None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        # set the canvas to the Matplotlib widget
        self.setupUi(self)
        
        self.frameResolution = 15
        self.customCallbacks = []
        
        self.fdvTree = FrameDataVisualizationTreeTrajectories()
        self.initializeConfidenceStructure()
        self.connectElements()
        
        
    def draw(self):
        self.confWidget1.draw()
        self.confWidget2.draw()
        self.confWidget3.draw()
        self.confWidget4.draw()
        
            
    def connectElements(self):        
#         self.btn_generateData.clicked.connect(self.generateNewSequence)
#         self.btn_loadData.clicked.connect(self.loadSequence)
#         self.btn_redraw.clicked.connect(self.plotSequence)
        self.btn_set.clicked.connect(self.setDisplayRange)
        self.btn_clear.clicked.connect(self.resetDisplayRange)
        
    def initializeConfidenceStructure(self):        
        # first approach:
        # using existing matplotlib widgets and pass their figures to
        # the view
        figs = dict()
        figs['days'] = self.confWidget1.canvas.fig
        figs['hours'] = self.confWidget2.canvas.fig
        figs['minutes'] = self.confWidget3.canvas.fig
        figs['frames'] = self.confWidget4.canvas.fig
        figs['colourbar'] = self.w_colourbar.canvas.fig
        
        
        self.frameView = FrameDataView(figs=figs, fdvTree=self.fdvTree)

        self.frameView.registerMPLCallback('days', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('hours', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('minutes', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('frames', 'button_press_event', 
                                           self.printDatumLocation)
        
        tmpCallbacks = copy.copy(self.customCallbacks)
        self.customCallbacks = []
        
        for figType, callbackFunction in tmpCallbacks:
            self.registerButtonPressCallback(figType, callbackFunction)
        
        self.day = None#0
        self.hour = None #0
        self.minute = None #0
        self.frame = None 
        self.resetDisplayRange()
        
    def registerButtonPressCallback(self, figType, callbackFunction):
#         print "registerBuggerPressCallback"
        self.frameView.registerMPLCallback(figType, 'button_press_event', 
                                           callbackFunction)
        self.customCallbacks += [[figType, callbackFunction]]
        
    def printDatumLocation(self, day, hour, minute, frame, data):
        print "clicked on day {0}, hour {1}, minute {2}, frame {3}, data {4}".format(
                                                    day, hour, minute, frame, data)
        self.initLocations(day, hour, minute, frame)
        self.plotSequence()
        
        
    def initLocations(self, day, hour, minute, frame):
        if day == None:
            self.day = sorted(self.fdvTree.tree.keys())[0]
        else:
            self.day = day
            
        if hour == None:
            self.hour = sorted(self.fdvTree.tree[self.day].keys())[0]
        else:
            self.hour = hour#"{0:02d}".format(int(hour))
            
        if minute == None:
            self.minute = sorted(self.fdvTree.tree[self.day][self.hour].keys())[0]
        else:
            self.minute = minute#"{0:02d}".format(int(minute))
            
        if frame == None:
            self.frame = sorted(self.fdvTree.tree[self.day][self.hour][self.minute].keys())[0]
        else:
            self.frame = frame
        
#     @QtCore.Slot()
    def generateNewSequence(self):
        print "start generating sequence"
        dayRng = range(1)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        t1 = time()
        self.fdvTree.generateRandomSequence(dayRng, hourRng, 
                                                    minuteRng, frameRng)
#         self.frameView.fdvTree.load('/home/peter/phd/code/pyTools/notebooks/ECCV2014/annotation-vial0-peter-struggling.fdvt')
        print "finished generating sequence in {0} sec".format(time()-t1)
        
        self.initializeConfidenceStructure()
        
        
    def loadSequence(self, path='/home/peter/phd/code/pyTools/notebooks/ECCV2014/posTree-v3.fdvtp'):
        print "start loading sequence"
        dayRng = range(1)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        t1 = time()
        self.frameView.fdvTree.load(path)
        print "finished  loading sequence in {0} sec".format(time()-t1)
        
        self.initializeConfidenceStructure()
        self.draw()
        
    def plotSequence(self):        
        self.initLocations(self.day, self.hour, self.minute, self.frame)
        self.frameView.plotData(self.day, self.hour, self.minute, 
                                      self.frame, self.frameResolution)
        
        self.confWidget1.draw()
        self.confWidget2.draw()
        self.confWidget3.draw()
        self.confWidget4.draw()
        
    def setDisplayRange(self):
        dMin = float(self.le_min.text())
        dMax = float(self.le_max.text())
        self.frameView.setDisplayRange([dMin, dMax])
        self.plotSequence()
        
    def resetDisplayRange(self):
        self.frameView.resetDisplayRange()
        displayRange = self.frameView.getDisplayRange()
        self.le_min.setText("{0:.2f}".format(displayRange[0]))
        self.le_max.setText("{0:.2f}".format(displayRange[1]))
        
        
        
#         
#         
#         
#     def setupUi(self, FrameViewWidget):
#         FrameViewWidget.setObjectName("FrameViewWidget")
#         FrameViewWidget.resize(603, 221)
#         self.confWidget1 = MplWidget(FrameViewWidget)
#         self.confWidget1.setGeometry(QtCore.QRect(0, 10, 501, 51))
#         self.confWidget1.setObjectName("confWidget1")
#         self.confWidget3 = MplWidget(FrameViewWidget)
#         self.confWidget3.setGeometry(QtCore.QRect(0, 110, 501, 51))
#         self.confWidget3.setObjectName("confWidget3")
#         self.le_max = QtGui.QLineEdit(FrameViewWidget)
#         self.le_max.setGeometry(QtCore.QRect(530, 40, 61, 23))
#         self.le_max.setObjectName("le_max")
#         self.confWidget4 = MplWidget(FrameViewWidget)
#         self.confWidget4.setGeometry(QtCore.QRect(0, 160, 501, 51))
#         self.confWidget4.setObjectName("confWidget4")
#         self.btn_set = QtGui.QPushButton(FrameViewWidget)
#         self.btn_set.setGeometry(QtCore.QRect(540, 70, 41, 41))
#         self.btn_set.setObjectName("btn_set")
#         self.w_colourbar = MplWidget(FrameViewWidget)
#         self.w_colourbar.setGeometry(QtCore.QRect(500, 10, 31, 201))
#         self.w_colourbar.setObjectName("w_colourbar")
#         self.le_min = QtGui.QLineEdit(FrameViewWidget)
#         self.le_min.setGeometry(QtCore.QRect(530, 160, 61, 23))
#         self.le_min.setObjectName("le_min")
#         self.btn_clear = QtGui.QPushButton(FrameViewWidget)
#         self.btn_clear.setGeometry(QtCore.QRect(540, 110, 41, 41))
#         self.btn_clear.setObjectName("btn_clear")
#         self.confWidget2 = MplWidget(FrameViewWidget)
#         self.confWidget2.setGeometry(QtCore.QRect(0, 60, 501, 51))
#         self.confWidget2.setObjectName("confWidget2")
# 
#         self.retranslateUi(FrameViewWidget)
#         QtCore.QMetaObject.connectSlotsByName(FrameViewWidget)
# 
#     def retranslateUi(self, FrameViewWidget):
#         FrameViewWidget.setWindowTitle(QtGui.QApplication.translate("FrameViewWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
#         self.btn_set.setText(QtGui.QApplication.translate("FrameViewWidget", "set", None, QtGui.QApplication.UnicodeUTF8))
#         self.btn_clear.setText(QtGui.QApplication.translate("FrameViewWidget", "clear", None, QtGui.QApplication.UnicodeUTF8))



class TestClass(QtGui.QMainWindow):
    
    def __init__(self):        
        QtGui.QMainWindow.__init__(self)
        self.ui = FrameViewWidget()
        self.ui.setupUi(self)
        self.show()   
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    w = TestClass()
    
    sys.exit(app.exec_())