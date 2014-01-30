
from matplotlibDistplay import Ui_MainWindow

import sys
from PySide import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

sys.path.append("/home/peter/phd/code")

from pyTools.misc.FrameDataVisualization import FrameDataView
# from pyTools.system.videoExplorer import *


class TestClass(QtGui.QMainWindow):
    
    def __init__(self):        
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.connectElements()
        
        self.initializeConfidenceStructure()
        
        self.day = 0
        self.hour = 2
        self.minute = 10
        self.frame = 1 
        
        self.show()   
        
    def connectElements(self):        
        self.ui.btn_generateData.clicked.connect(self.generateNewSequence)
        self.ui.btn_redraw.clicked.connect(self.plotSequence)
        
    def initializeConfidenceStructure(self):        
        # first approach:
        # using existing matplotlib widgets and pass their figures to
        # the view
        figs = dict()
        figs['days'] = self.ui.confWidget1.canvas.fig
        figs['hours'] = self.ui.confWidget2.canvas.fig
        figs['minutes'] = self.ui.confWidget3.canvas.fig
        figs['frames'] = self.ui.confWidget4.canvas.fig
        
        self.frameView = FrameDataView(figs=figs)
        
#         # second approach:
#         # get existing figure handles and create new widgets from them
#         figs = self.frameView.getFigureHandles()         
#         
#         self.widget = FigureCanvas(figs['days'])
#         self.widget.setGeometry(QtCore.QRect(100, 350, 471, 31))
#         self.widget.setObjectName("widget")
#         self.widget_2 = FigureCanvas(figs['hours'])
#         self.widget_2.setGeometry(QtCore.QRect(100, 410, 471, 31))
#         self.widget_2.setObjectName("widget_2")
#         self.widget_3 = FigureCanvas(figs['minutes'])
#         self.widget_3.setGeometry(QtCore.QRect(100, 470, 471, 31))
#         self.widget_3.setObjectName("widget_3")
#         self.widget_4 = FigureCanvas(figs['frames'])
#         self.widget_4.setGeometry(QtCore.QRect(100, 530, 471, 31))
#         self.widget_4.setObjectName("widget_4")
#                 
#         l = self.ui.verticalLayout
#         
#         l.addWidget(self.widget)
#         l.addWidget(self.widget_2)
#         l.addWidget(self.widget_3)
#         l.addWidget(self.widget_4)

        self.frameView.registerMPLCallback('days', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('hours', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('minutes', 'button_press_event', 
                                           self.printDatumLocation)

        self.frameView.registerMPLCallback('frames', 'button_press_event', 
                                           self.printDatumLocation)
        
        
    def printDatumLocation(self, day, hour, minute, frame):
        print "clicked on day {0}, hour {1}, minute {2}, frame {3}".format(
                                                    day, hour, minute, frame)
        
        if day == None:
            self.day = 0
        else:
            self.day = day
            
        if hour == None:
            self.hour = 0
        else:
            self.hour = hour
            
        if minute == None:
            self.minute = 0
        else:
            self.minute = minute
            
        if frame == None:
            self.frame = 0
        else:
            self.frame = frame
            
        self.plotSequence()
        
#     @QtCore.Slot()
    def generateNewSequence(self):
        print "start"
        dayRng = range(4)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        self.frameView.fdvTree.generateRandomSequence(dayRng, hourRng, 
                                                      minuteRng, frameRng)
        print "finished"
        
    def plotSequence(self):        
        self.frameView.plotConfidence(self.day, self.hour, self.minute, 
                                      self.frame, 30)
        
#         self.widget.draw()
#         self.widget_2.draw()
#         self.widget_3.draw()
#         self.widget_4.draw()
        
        self.ui.confWidget1.draw()
        self.ui.confWidget2.draw()
        self.ui.confWidget3.draw()
        self.ui.confWidget4.draw()
        
        
if __name__ == "__main__":    
    app = QtGui.QApplication(sys.argv)
    
    w = TestClass()
    
    sys.exit(app.exec_())
    