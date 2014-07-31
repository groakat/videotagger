__author__ = 'peter'


from pyTools.gui.graphicsViewTest_auto import Ui_MainWindow
import pyTools.misc.FrameDataVisualization as FDV

import sys
import numpy as np

np.set_printoptions(threshold='nan')
import time
from PySide import QtCore, QtGui

import copy

class Test(QtGui.QMainWindow):

    def __init__(self):
        super(Test, self).__init__()
        # Usual setup stuff. Set up the user interface from Designer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.frameResolution = 5
        self.debugCnt = 0

        self.overviewScene = None
        self.sceneRect = None
        self.rects = {'days':[],
                      'hours':[],
                      'minutes':[],
                      'frames':[]}

        self.subPlot = {'days': None,
                      'hours': None,
                      'minutes': None,
                      'frames': None}

        self.clickRects = {'days':[],
                      'hours':[],
                      'minutes':[],
                      'frames':[]}

        self.clickSubPlot = {'days': None,
                      'hours': None,
                      'minutes': None,
                      'frames': None}

        self.subPlotScales = dict()


        self.polys = dict()
        self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
        self.fdvt.load('/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v0.npy')
        # self.fdvt.load('/media/peter/8e632f24-2998-4bd2-8881-232779708cd0/xav/data/clfrFDVT-burgos_rf_200k_weight-v3.npy')

        self.brushes = [QtGui.QBrush(QtGui.QColor(0, 255, 0)),
                        QtGui.QBrush(QtGui.QColor(0,  0, 255)),
                        QtGui.QBrush(QtGui.QColor(255, 0, 0)),
                        QtGui.QBrush(QtGui.QColor(0, 0, 0))]

        self.clickBrush = QtGui.QBrush(QtGui.QColor(0, 255, 0, 0))


        self.connectElements()
        self.setupGV()

        self.show()

    def connectElements(self):
        self.ui.pb_debug.clicked.connect(self.buttonClick)


    def setupGV(self):
        self.overviewScene = QtGui.QGraphicsScene(self)
        self.overviewScene.setSceneRect(0, -0.5, 1, 7)

        self.ui.gv_center.setScene(self.overviewScene)
        self.ui.gv_center.fitInView(0, -0.5, 1, 7)
        self.ui.gv_center.setMouseTracking(True)
        self.ui.gv_center.setRenderHint(QtGui.QPainter.Antialiasing)

        self.initPositionPointers()
        self.initSubPlots()
        self.ui.gv_center.fitInView(0, -0, 0.2, 0.4)

    def initSubPlots(self):
        self.subPlot = {'days': self.overviewScene.addRect(0, 0, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'hours': self.overviewScene.addRect(0, 0, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'minutes': self.overviewScene.addRect(0,0, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'frames': self.overviewScene.addRect(0, 0, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0)))}

        self.subPlot['days'].translate(0, 4.5)
        self.subPlot['hours'].translate(0, 3)
        self.subPlot['minutes'].translate(0, 1.5)

        self.clickSubPlot = {'days': self.overviewScene.addRect(0, 4.5, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'hours': self.overviewScene.addRect(0, 3, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'minutes': self.overviewScene.addRect(0, 1.5, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0))),
                      'frames': self.overviewScene.addRect(0, 0, 1, 1, QtGui.QPen(QtGui.QColor(0, 255, 0, 0)))}

        # self.clickSubPlot['days'].translate(0, 4.5)
        # self.clickSubPlot['hours'].translate(0, 3)
        # self.clickSubPlot['minutes'].translate(0, 1.5)


    def createPositionPointer(self, y):
        poly = QtGui.QPolygonF([QtCore.QPointF(0,-0.2 + y),
                                QtCore.QPointF(0.025,0 + y),
                                QtCore.QPointF(0.05,-0.2 + y)])


        penCol = QtGui.QColor(0, y * 30, 0)
        brushCol = QtGui.QColor(0, y * 30, 0)
        return self.overviewScene.addPolygon(poly, QtGui.QPen(penCol), QtGui.QBrush(brushCol))

    def initPositionPointers(self):
        self.polys['days'] = self.createPositionPointer(4.5)
        self.polys['hours'] = self.createPositionPointer(3)
        self.polys['minutes'] = self.createPositionPointer(1.5)
        self.polys['frames'] = self.createPositionPointer(0)


    def createClickBar(self, rectKey, instance):
        sp = self.clickSubPlot[rectKey]
        brush = self.clickBrush

        pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 0))
        rect = QtCore.QRectF(0, 0, 1, 1)
        rectItem = FDVBar(rect, sp)
        rectItem.setBarCoordinates(level=rectKey, instance=instance)
        rectItem.setCallback(self.focusOnBar)
        rectItem.setBrush(brush)
        rectItem.setPen(pen)
        rectItem.setZValue(1)

        return rectItem


    def createStackedBar(self, rectKey, instance):
        sp = self.subPlot[rectKey]
        rects = []
        bar = QtGui.QGraphicsRectItem(sp)
        for i, brush in enumerate(self.brushes):
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 0))
            rect = QtCore.QRectF(0, i, 1, np.random.rand(1))
            rectItem = FDVBar(rect, bar)
            rectItem.setBarCoordinates(level=rectKey, instance=instance)
            rectItem.setCallback(self.focusOnBar)
            # rectItem = QtGui.QGraphicsRectItem(rect, bar)
            rectItem.setBrush(brush)
            rectItem.setPen(pen)

        return bar


    def addElement(self, rectKey, y):
        rects = self.rects[rectKey]
        clickRects = self.clickRects[rectKey]

        rects += [self.createStackedBar(rectKey, len(rects))]
        clickRects += [self.createClickBar(rectKey, len(clickRects))]

        for i, bar in enumerate(rects):
            x = float(i) / len(rects)
            bar.setPos(x, y)

        for i, bar in enumerate(clickRects):
            x = float(i) / len(clickRects)
            r = bar.rect()
            r.setX(x)
            r.setY(y)
            r.setHeight(1)
            r.setWidth(1.0 / len(clickRects))
            bar.setRect(r)
            # bar.setPos(x, y)



    def normalizeBar(self, bar, accH, accW):
        """
        Args:
            accH (int):
                accumulated height of all stacked bars
        """
        space = 1#1.1
        # if accH != 0:
        #     height = 1.0 / accH
        # else:
        #     height = 0

        height = 1

        if accW != 0:
            width = 1.0 / (accW * space)
        else:
            width = 0

        trans = bar.transform()
        trans.setMatrix(width,          0, 0,
                        0, height, 0,
                        0,          0, 1)
        bar.setTransform(trans)


    def normalizeSubplot(self, subplotItem, accH, y):
        """
        Args:
            accH (int):
                accumulated height of all stacked bars
        """
        subplotItem.prepareGeometryChange()
        space = 1.1
        if accH != 0:
            height = 1.0 / accH
        else:
            height = 0

        trans = subplotItem.transform()
        trans.setMatrix(1,           trans.m12(), trans.m13(),
                        trans.m21(), height,      trans.m23(),
                        trans.m31(), -height * y + y, 1)
        subplotItem.setTransform(trans)


    def changeElements(self, data, rectKey, y):
        rects = self.rects[rectKey]
        maxHeight = 0

        maxCum = np.max(np.sum(data, axis=1))
        minBarHeight =  maxCum * 0.05
        for i, d in enumerate(data):
            if i >= len(rects):
                self.addElement(rectKey, y)

            r = rects[i]

            accH = 0
            for k, barLet in enumerate(r.childItems()):
                h = d[k]

                if h != 0 and h < minBarHeight:
                    h = minBarHeight

                geo = barLet.rect()
                geo.setY(accH)
                geo.setHeight(h)
                barLet.setRect(geo)
                accH += h

            if maxHeight < accH:
                maxHeight = accH

            self.normalizeBar(r, accH, len(rects))

        self.normalizeSubplot(self.subPlot[rectKey], maxHeight, y)

        self.overviewScene.update()
        self.ui.gv_center.update()


    def setPolyPosition(self, key, idx):
        l = float(len(self.rects[key]))
        pw = self.polys[key].boundingRect().width()
        if key == 'frames':
            idx /= float(self.frameResolution)

        self.polys[key].setPos(idx / l  - (pw / 2.0) + 1 / (2 *l), 0)


    def plotDays(self, fdvt, dayIdx):
        data = fdvt.plotData['days']['data']
        # print data
        # data = np.random.rand(2,4)
        # print data
        self.changeElements(data, 'days', 4.5)
        self.setPolyPosition('days', dayIdx)

    def plotHours(self,  fdvt, hourIdx):
        data = fdvt.plotData['hours']['data']
        # data = np.random.rand(24,4)
        self.changeElements(data, 'hours', 3)
        self.setPolyPosition('hours', hourIdx)

    def plotMinutes(self,  fdvt, minuteIdx):
        data = fdvt.plotData['minutes']['data']
        # data = np.random.rand(60,4)
        self.changeElements(data, 'minutes', 1.5)
        self.setPolyPosition('minutes', minuteIdx)

    def plotFrames(self, fdvt, frameIdx):
        data = fdvt.plotData['frames']['data']
        # data = np.random.rand(1764/self.frameResolution,4)
        self.changeElements(data,'frames', 0)
        self.setPolyPosition('frames', frameIdx)


    def plotData(self, day, hour, minute, frame):
        self.day = day
        self.hour = hour
        self.minute = minute
        self.frame = frame

        self.fdvt.generateConfidencePlotData(day, hour, minute, frame,
                                                self.frameResolution)
        dayIdx = sorted(self.fdvt.tree.keys()).index(day)
        self.plotDays(self.fdvt, dayIdx)

        hourIdx = sorted(self.fdvt.tree[day].keys()).index(hour)
        self.plotHours(self.fdvt, hourIdx)

        minuteIdx = sorted(self.fdvt.tree[day][hour].keys()).index(minute)
        self.plotMinutes(self.fdvt, minuteIdx)
        #
        self.plotFrames(self.fdvt, frame)

        if self.debugCnt < 1:
            self.ui.gv_center.scale(1, -1)
            pass
        else:

            # self.ui.gv_center.scale(10, 10)
            pass

        self.overviewScene.update()


    def focusOnBar(self, level, instance):
        if level == "frames":
            self.frame = instance * self.frameResolution
        else:
            self.frame = 0

        if level == "minutes":
            self.minute = sorted(self.fdvt.tree[self.day][self.hour].keys())[instance]

        if level == "hours":
            self.hour = sorted(self.fdvt.tree[self.day].keys())[instance]

        if level == "days":
            self.day = sorted(self.fdvt.tree.keys())[instance]

        t1 = time.time()
        self.plotData(self.day, self.hour, self.minute, self.frame)
        print time.time() - t1

    def buttonClick(self):
        t = time.time()
        a = ['00', '01', '02', '03', '04']
        self.plotData('2013-02-19', '00', '02', self.debugCnt)
        # self.plotData('2013-02-19', a[self.debugCnt], '00', 0)

        print time.time() - t
        self.debugCnt += 1
        print "button click"


class FDVBar(QtGui.QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super(FDVBar, self).__init__(*args, **kwargs)

    def setBarCoordinates(self, level, instance):
        self.level = level
        self.instance = instance

    def setCallback(self, func):
        self.callback = func

    def mousePressEvent(self, event):
        self.callback(self.level, self.instance)



if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    w = Test()

    sys.exit(app.exec_())
