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
from pyTools.misc.FrameDataVisualization import FrameDataView
import pyTools.misc.FrameDataVisualization as FDV
                                
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
        self.colors = None
        
        self.fdvTree = FDV.FrameDataVisualizationTreeBehaviour()
        self.initializeConfidenceStructure()
        self.connectElements()
        
        
    def draw(self):
        self.confWidget1.draw()
        self.confWidget2.draw()
        self.confWidget3.draw()
        self.confWidget4.draw()
        
            
    def connectElements(self):        
        self.btn_set.clicked.connect(self.setDisplayRange)
        self.btn_clear.clicked.connect(self.resetDisplayRange)
        self.pb_open.clicked.connect(self.openFDVT)
        
#     @QtCore.Slot()
    def openFDVT(self):
        print "ad2"
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                                               "Open Image", ".")#, "fdtv files (*.fdtv*)")# *.jpg *.bmp)"))
        
        self.loadSequence(fileName[0])
        
        
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
        
        
        self.frameView.setColors(self.colors)
        
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
            if self.frame == 'data':
                self.frame = 0
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
        self.setDisplayRange()
        
    def setSequence(self, fdvt):
        self.frameView.fdvTree = fdvt
        self.initializeConfidenceStructure()
        self.draw()
        self.setDisplayRange()
        
    def setSerializedSequence(self, fdvt):
        self.frameView.fdvTree.deserialize(fdvt)
        self.initializeConfidenceStructure()
        self.draw()
        self.setDisplayRange()
        
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
        
    def setColors(self, colors):
        self.colors = colors
        self.frameView.setColors(self.colors)


class TestClass(QtGui.QMainWindow):
    
    def __init__(self):        
        QtGui.QMainWindow.__init__(self)
        self.ui = FrameViewWidget(self)
#         self.ui.setupUi(self)
        self.show()   
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    w = TestClass()
    
    sys.exit(app.exec_())