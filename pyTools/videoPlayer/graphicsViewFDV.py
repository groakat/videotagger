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
        self.setupUi()
        self.connectElements()
        self.debugCnt = 0

        self.gvFDV.registerButtonPressCallback('days', self.exampleCallbackFunction)
        self.gvFDV.registerButtonPressCallback('hours', self.exampleCallbackFunction)
        self.gvFDV.registerButtonPressCallback('minutes', self.exampleCallbackFunction)
        self.gvFDV.registerButtonPressCallback('frames', self.exampleCallbackFunction)

        self.gvFDV.loadSequence('/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v0.npy')

        self.show()

    def setupUi(self):
        self.resize(800, 600)
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.layout = QtGui.QVBoxLayout(self)

        self.gvFDV = GraphicsViewFDV(self)#.centralwidget)

        self.layout.addWidget(self.gvFDV)

        self.pb_debug = QtGui.QPushButton(self)
        self.pb_debug.setGeometry(QtCore.QRect(540, 500, 94, 24))
        self.pb_debug.setObjectName("pb_debug")
        self.pb_debug.setText("push me")
        self.layout.addWidget(self.pb_debug)

        self.centralwidget.setLayout(self.layout)

        self.setCentralWidget(self.centralwidget)

    def connectElements(self):
        self.pb_debug.clicked.connect(self.buttonClick)

    def buttonClick(self):
        # self.gvFDV.loadSequence('/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v0.npy')
        c = [QtGui.QColor(0, 255, 0), QtGui.QColor(0, 0, 0), QtGui.QColor(255, 0, 0), QtGui.QColor(255, 255, 0)]
        self.gvFDV.setColors(c)


    def exampleCallbackFunction(self, day, hour, minute, frame):
        print(day, hour, minute, frame)

class GraphicsViewFDV(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(GraphicsViewFDV, self).__init__(*args, **kwargs)

        self.setupUi()

        self.frameResolution = 5
        self.debugCnt = 0

        self.overviewScene = None
        self.sceneRect = None

        self.fdvt = None

        self.day = None
        self.hour = None
        self.minute = None
        self.frame = None

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

        self.axes = {'days': None,
                      'hours': None,
                      'minutes': None,
                      'frames': None}

        self.axisSpacing = {'days': 1,
                          'hours': 1,
                          'minutes': 5,
                          'frames': 100}

        self.axisY = {'days': 4.5,
                          'hours': 3,
                          'minutes': 1.5,
                          'frames': 0}

        self.subPlotScales = dict()

        self.mouseReleaseCallbacks = {'days':[],
                                      'hours':[],
                                      'minutes':[],
                                      'frames':[]}

        self.rangeTemplate =  {'days': None,
                               'hours':['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'],
                               'minutes':['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59'],
                               'frames': list(np.arange(np.floor(1800 / self.frameResolution), dtype=float))}

        self.missingValueBrush = QtGui.QBrush(QtGui.QColor(150, 150, 150))

        self.polys = dict()
        # self.fdvt.load('/media/peter/8e632f24-2998-4bd2-8881-232779708cd0/xav/data/clfrFDVT-burgos_rf_200k_weight-v3.npy')



        self.brushes = None
        self.clickBrush = QtGui.QBrush(QtGui.QColor(0, 255, 0, 0))
        self.setupGV()

        self.show()
        self.gv_center.fitInView(-0.1, -0.1, 1.1, 7,QtCore.Qt.IgnoreAspectRatio)
        # self.initFirstView()

    def registerButtonPressCallback(self, figKey, callbackFunction):
        """
        figKey (String):
                    'days', 'hours', 'minutes' or 'frames'

        callbackFunction (function pointer):
            function to be called by the callback
            function should take four arguments which are
                callbackFunction(day, hour, minute, frame)
        """
        self.mouseReleaseCallbacks[figKey] += [callbackFunction]

    def setColors(self, colors=None, reload=True):
        """

        :param colors: list of QColors
        :return:
        """
        if colors is None:
            self.brushes = [QtGui.QBrush(QtGui.QColor(0, 255, 0)),
                            QtGui.QBrush(QtGui.QColor(0,  0, 255)),
                            QtGui.QBrush(QtGui.QColor(255, 0, 0)),
                            QtGui.QBrush(QtGui.QColor(0, 0, 0))]
            # self.colors  = ['r', 'y', 'b', 'g', 'orange', 'black']
        else:
            # self.colors = colors
            self.brushes = []
            for c in colors:
                print c, '-------------------------------------------'
                clr = QtGui.QColor(c)
                self.brushes += [QtGui.QBrush(clr)]

        for k, i in self.rects.items():
            for r in i:
                self.overviewScene.removeItem(r)

            self.rects[k] = []

        if reload:
            self.updateDisplay(useCurrentPos=True)


    def loadSequence(self, fdvtPath):
        self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
        self.fdvt.load(fdvtPath)
        self.updateDisplay()

    def setupUi(self):
        self.layout = QtGui.QVBoxLayout()
        self.gv_center = QtGui.QGraphicsView(self)
        # self.gv_center.setGeometry(QtCore.QRect(100, 60, 561, 150))
        self.gv_center.setObjectName("gv_center")
        self.layout.addWidget(self.gv_center)
        self.gv_center.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gv_center.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setLayout(self.layout)


    def resizeEvent(self, event):
        super(GraphicsViewFDV, self).resizeEvent(event)
        self.gv_center.fitInView(-0.1, -1, 1.1, 6,QtCore.Qt.IgnoreAspectRatio)

    def showEvent(self, event):
        super(GraphicsViewFDV, self).showEvent(event)
        self.gv_center.fitInView(-0.1, -1, 1.1, 6,QtCore.Qt.IgnoreAspectRatio)


    def setupGV(self):
        self.overviewScene = QtGui.QGraphicsScene(self)
        # self.overviewScene.setSceneRect(0, -0.5, 1, 7)

        self.gv_center.setScene(self.overviewScene)
        # self.gv_center.fitInView(0, -0.5, 1, 7)
        self.gv_center.setMouseTracking(True)
        self.gv_center.setRenderHint(QtGui.QPainter.Antialiasing)

        self.initPositionPointers()
        self.initSubPlots()

        self.setColors(reload=False)

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

        self.createAxis('days')#, 4.5)#, range(1, 3))
        self.createAxis('hours')#, 3)#, range(1, 25))
        self.createAxis('minutes')#, 1.5)#, range(1, 66, 5))
        self.createAxis('frames')#, 0)#, range(1, 1800 / self.frameResolution + 1, self.frameResolution))

        self.createTitle(4.5, "days")
        self.createTitle(3, "hours")
        self.createTitle(1.5, "minutes")
        self.createTitle(0, "frames")



    def createPositionPointer(self, y):
        poly = QtGui.QPolygonF([QtCore.QPointF(0,-0.2 + y),
                                QtCore.QPointF(0.01,-0.15 + y),
                                QtCore.QPointF(0.02,-0.2 + y)])

        penCol = QtGui.QColor(0, y * 30, 0)
        brushCol = QtGui.QColor(0, y * 30, 0)
        return self.overviewScene.addPolygon(poly, QtGui.QPen(penCol), QtGui.QBrush(brushCol))

    def initPositionPointers(self):
        self.polys['days'] = self.createPositionPointer(4.5)
        self.polys['hours'] = self.createPositionPointer(3)
        self.polys['minutes'] = self.createPositionPointer(1.5)
        self.polys['frames'] = self.createPositionPointer(0)


    def createAxisTicks(self, i, t, l, spacing, rectKey, pen):
        x = i * spacing / l + 1 / (2 * l)
        line = QtGui.QGraphicsLineItem(x, -0.01, x, -0.05,  self.axes[rectKey])
        line.setPen(pen)

        font = QtGui.QFont()
        font.setPointSize(5)
        text = QtGui.QGraphicsTextItem(str(t), self.axes[rectKey])
        text.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        text.setFont(font)
        # text.scale(0.002, -0.005)
        pw = text.boundingRect().width() * 0.002


        x = i * spacing / l  - (pw / 2.0) + 1 / (2 *l)
        text.setPos(x, -0.05)

    def getFdvtLabel(self, level, instance):
        if level == "frames":
            return self.fdvt.tree[self.day][self.hour][self.minute]['data'][instance] \
                                * self.frameResolution

        if level == "minutes":
            return sorted([x for x in \
                                self.fdvt.tree[self.day][self.hour].keys()\
                                    if x != 'meta'])[instance]

        if level == "hours":
            return sorted([x for x in self.fdvt.tree[self.day].keys()\
                                    if x != 'meta'])[instance]

        if level == "days":
            return sorted([x for x in self.fdvt.tree.keys()\
                                    if x != 'meta'])[instance]

    def getTemplateLabel(self, level, instance):
        if self.rangeTemplate[level] is None:
            return self.getFdvtLabel(level, instance)
        else:
            return self.rangeTemplate[level][instance]

    def createAxis(self, rectKey):
        spacing = self.axisSpacing[rectKey]

        if self.axes[rectKey]:
            self.overviewScene.removeItem(self.axes[rectKey])

        self.axes[rectKey] = QtGui.QGraphicsRectItem()

        line = QtGui.QGraphicsLineItem(0, -0.01, 1, -0.01, self.axes[rectKey])
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        line.setPen(pen)

        l = float(len(self.rects[rectKey]))
        if l:
            for i, t in enumerate(range(0, int(l), spacing)):
                lbl = self.getTemplateLabel(rectKey, t)
                self.createAxisTicks(i, lbl, l, spacing, rectKey, pen)

        self.overviewScene.addItem(self.axes[rectKey])
        self.axes[rectKey].setPos(0, self.axisY[rectKey])

    def createTitle(self, y, title):
        font = QtGui.QFont()
        text = self.overviewScene.addText(str(title), font)
        text.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        # text.scale(0.002, -0.005)
        pw = text.boundingRect().width() * 0.002
        ph = text.boundingRect().height() * 0.015

        x = 0.5 - (pw / 2.0)
        text.setPos(x, y + 1 + ph)


    def createClickBar(self, rectKey, instance):
        sp = self.clickSubPlot[rectKey]
        brush = self.clickBrush

        pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 0))
        rect = QtCore.QRectF(0, 0, 1, 1)
        rectItem = FDVBar(rect, sp)
        rectItem.setBarCoordinates(level=rectKey, instance=instance)
        rectItem.setCallback(self.mouseClickOnBar)
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
            rectItem.setCallback(self.mouseClickOnBar)
            # rectItem = QtGui.QGraphicsRectItem(rect, bar)
            rectItem.setBrush(brush)
            rectItem.setPen(pen)

        return bar


    def addElement(self, rectKey, y):
        rects = self.rects[rectKey]

        rects += [self.createStackedBar(rectKey, len(rects))]

        for i, bar in enumerate(rects):
            x = float(i) / len(rects)
            bar.setPos(x, y)

        clickRects = self.clickRects[rectKey]
        if len(clickRects) < len(rects):

            clickRects += [self.createClickBar(rectKey, len(clickRects))]

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

    def getKeyIndexInFDVT(self, level, idx):
        if level != 'frames':
            return self.rangeTemplate[level].index(
                                    self.getFdvtLabel(level, idx))
        else:
            return idx #self.rangeTemplate[level].index(
            #                         self.getFdvtLabel(level, idx)) \
            #         / self.frameResolution


    def changeElements(self, data, rectKey, y):
        for clickRect in self.clickRects[rectKey]:
            clickRect.setBrush(self.clickBrush)

        rects = self.rects[rectKey]
        maxHeight = 0

        maxCum = np.max(np.sum(data, axis=1))
        minBarHeight =  maxCum * 0.05
        for i, d in enumerate(data):
            if self.rangeTemplate[rectKey] is not None:
                idx = self.getKeyIndexInFDVT(rectKey, i)
            else:
                idx = i

            while idx >= len(rects):
                self.addElement(rectKey, y)

            r = rects[idx]

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


        if self.rangeTemplate[rectKey] is not None\
        and rectKey != 'frames':
            missingValues = set(self.rangeTemplate[rectKey]).difference(self.getFdvtLabel(rectKey, slice(None, None)))
            for val in missingValues:
                idx = self.rangeTemplate[rectKey].index(val)

                while idx >= len(rects):
                    self.addElement(rectKey, y)
                self.clickRects[rectKey][idx].setBrush(self.missingValueBrush)
                r = rects[idx]

                accH = 0
                for k, barLet in enumerate(r.childItems()):
                    h = 0

                    geo = barLet.rect()
                    geo.setY(accH)
                    geo.setHeight(h)
                    barLet.setRect(geo)


        self.normalizeSubplot(self.subPlot[rectKey], maxHeight, y)

        self.overviewScene.update()
        self.gv_center.update()


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
        self.createAxis('days')

    def plotHours(self,  fdvt, hourIdx):
        data = fdvt.plotData['hours']['data']
        # data = np.random.rand(24,4)
        self.changeElements(data, 'hours', 3)
        self.setPolyPosition('hours', hourIdx)
        self.createAxis('hours')

    def plotMinutes(self,  fdvt, minuteIdx):
        data = fdvt.plotData['minutes']['data']
        # data = np.random.rand(60,4)
        self.changeElements(data, 'minutes', 1.5)
        self.setPolyPosition('minutes', minuteIdx)
        self.createAxis('minutes')

    def plotFrames(self, fdvt, frameIdx):
        data = fdvt.plotData['frames']['data']
        # data = np.random.rand(1764/self.frameResolution,4)
        self.changeElements(data,'frames', 0)
        self.setPolyPosition('frames', frameIdx)
        self.createAxis('frames')


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
            self.gv_center.scale(1, -1)
            pass
        else:

            # self.gv_center.scale(10, 10)
            pass

        self.debugCnt += 1
        self.overviewScene.update()


    def mouseClickOnBar(self, level, instance):
        if level == "frames":
            self.frame = instance * self.frameResolution
        else:
            self.frame = 0

        if level == "minutes":
            self.minute = sorted([x for x in self.fdvt.tree[self.day][self.hour].keys()\
                                    if x != 'meta'])[instance]

        if level == "hours":
            self.hour = sorted([x for x in self.fdvt.tree[self.day].keys()\
                                    if x != 'meta'])[instance]

        if level == "days":
            self.day = sorted([x for x in self.fdvt.tree.keys()\
                                    if x != 'meta'])[instance]

        t1 = time.time()
        self.plotData(self.day, self.hour, self.minute, self.frame)

        for func in self.mouseReleaseCallbacks[level]:
            func(self.day, self.hour, self.minute, self.frame)

        print time.time() - t1

    def updateDisplay(self, useCurrentPos=False):
        if self.fdvt is None:
            return

        if not useCurrentPos:
            self.day = self.getFdvtLabel('days', 0)
            self.hour = self.getFdvtLabel('hours', 0)
            self.minute = self.getFdvtLabel('minutes', 0)
            self.frame = self.getFdvtLabel('frames', 0)
        self.plotData(self.day, self.hour, self.minute, self.frame)
        self.plotData(self.day, self.hour, self.minute, self.frame)



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
