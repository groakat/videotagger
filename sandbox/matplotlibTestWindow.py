
from matplotlibDisplay import Ui_MainWindow

import sys
from PySide import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


from time import time


sys.path.append("/home/peter/phd/code")

from pyTools.misc.FrameDataVisualization import FrameDataView, \
                                FrameDataVisualizationTreeTrajectories
# from pyTools.system.videoExplorer import *


class TestClass(QtGui.QMainWindow):
    
    def __init__(self):        
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.connectElements()
        
        self.initializeConfidenceStructure()
        
        self.day = None#0
        self.hour = None #0
        self.minute = None #0
        self.frame = None 
        
        self.frameResolution = 15
        
        self.ui.widget.loadSequence()
        
        self.show()   
        
        
    def connectElements(self):        
#         self.ui.btn_generateData.clicked.connect(self.generateNewSequence)
#         self.ui.btn_loadData.clicked.connect(self.loadSequence)
#         self.ui.btn_redraw.clicked.connect(self.plotSequence)
#         self.ui.btn_set.clicked.connect(self.setDisplayRange)
#         self.ui.btn_clear.clicked.connect(self.resetDisplayRange)
        
        
        self.ui.btn_generateData.clicked.connect(self.ui.widget.generateNewSequence)
        self.ui.btn_loadData.clicked.connect(self.ui.widget.loadSequence)
        self.ui.btn_redraw.clicked.connect(self.ui.widget.plotSequence)
        
    def initializeConfidenceStructure(self):        
        # first approach:
        # using existing matplotlib widgets and pass their figures to
        # the view
        figs = dict()
        figs['days'] = self.ui.confWidget1.canvas.fig
        figs['hours'] = self.ui.confWidget2.canvas.fig
        figs['minutes'] = self.ui.confWidget3.canvas.fig
        figs['frames'] = self.ui.confWidget4.canvas.fig
        figs['colourbar'] = self.ui.w_colourbar.canvas.fig
        
        fdvTree = FrameDataVisualizationTreeTrajectories()
        
        self.frameView = FrameDataView(figs=figs, fdvTree=fdvTree)

        self.frameView.registerMPLCallback('days', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('hours', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('minutes', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('frames', 'button_press_event', 
                                           self.printDatumLocation)
        
        
    def printDatumLocation(self, day, hour, minute, frame, data):
        print "clicked on day {0}, hour {1}, minute {2}, frame {3}, data {4}".format(
                                                    day, hour, minute, frame, data)
        self.initLocations(day, hour, minute, frame)
        self.plotSequence()
        
    def initLocations(self, day, hour, minute, frame):
        if day == None:
            self.day = sorted(self.frameView.fdvTree.tree.keys())[0]
        else:
            self.day = day
            
        if hour == None:
            self.hour = sorted(self.frameView.fdvTree.tree[self.day].keys())[0]
        else:
            self.hour = hour#"{0:02d}".format(int(hour))
            
        if minute == None:
            self.minute = sorted(self.frameView.fdvTree.tree[self.day][self.hour].keys())[0]
        else:
            self.minute = minute#"{0:02d}".format(int(minute))
            
        if frame == None:
            self.frame = sorted(self.frameView.fdvTree.tree[self.day][self.hour][self.minute].keys())[0]
        else:
            self.frame = frame
        
#     @QtCore.Slot()
    def generateNewSequence(self):
        print "start"
        dayRng = range(1)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        t1 = time()
        self.frameView.fdvTree.generateRandomSequence(dayRng, hourRng, 
                                                    minuteRng, frameRng)
#         self.frameView.fdvTree.load('/home/peter/phd/code/pyTools/notebooks/ECCV2014/annotation-vial0-peter-struggling.fdvt')
        print "finished in {0} sec".format(time()-t1)
        
        self.day = None#0
        self.hour = None #0
        self.minute = None #0
        self.frame = None 
        
        
    def loadSequence(self):
        print "start"
        dayRng = range(1)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        t1 = time()
#         self.frameView.fdvTree.generateRandomSequence(dayRng, hourRng, 
#                                                       minuteRng, frameRng)
#         self.frameView.fdvTree.load('/home/peter/phd/code/pyTools/notebooks/ECCV2014/annotation-vial0-peter-struggling.fdvt')
        self.frameView.fdvTree.load('/home/peter/phd/code/pyTools/notebooks/ECCV2014/posTree-v3.fdvtp')
        print "finished in {0} sec".format(time()-t1)
        
        self.day = None#0
        self.hour = None #0
        self.minute = None #0
        self.frame = None 
        
#         displayRange = self.frameView.getDisplayRange()
#         self.ui.le_min.setText(str(displayRange[0]))
#         self.ui.le_max.setText(str(displayRange[1]))
        self.resetDisplayRange()
        
    def plotSequence(self):        
        self.initLocations(self.day, self.hour, self.minute, self.frame)
        self.frameView.plotData(self.day, self.hour, self.minute, 
                                      self.frame, self.frameResolution)
        
#         self.widget.draw()
#         self.widget_2.draw()
#         self.widget_3.draw()
#         self.widget_4.draw()
        
        self.ui.confWidget1.draw()
        self.ui.confWidget2.draw()
        self.ui.confWidget3.draw()
        self.ui.confWidget4.draw()
        
    def setDisplayRange(self):
        dMin = float(self.ui.le_min.text())
        dMax = float(self.ui.le_max.text())
        self.frameView.setDisplayRange([dMin, dMax])
        self.plotSequence()
        
    def resetDisplayRange(self):
        self.frameView.resetDisplayRange()
        displayRange = self.frameView.getDisplayRange()
        self.ui.le_min.setText("{0:.2f}".format(displayRange[0]))
        self.ui.le_max.setText("{0:.2f}".format(displayRange[1]))
        
        
if __name__ == "__main__":    
    app = QtGui.QApplication(sys.argv)
    
    w = TestClass()
    
    sys.exit(app.exec_())
    