from PySide import QtGui
from PySide import QtCore


import pyTools.videoProc.annotation as Annotation
import pyTools.misc.basic as bsc 
import pyTools.misc.config as cfg
import time
#from qimage2ndarray import *
# from PyQt4.uic.Compiler.qtproxies import QtCore

from collections import namedtuple


import json


KeyIdxPair = namedtuple('KeyIdxPair', ['key', 'idx', 'conf'])

class AnnoViewManager(QtCore.QObject):
    @cfg.logClassFunction
    def __init__(self, parent, vialNo=None, behaviourName=None, annotator=None,
                color=None):                
        self.AVs = []
        
        for i in range(2):
            self.AVs += [{"av": AnnoView(parent, vialNo=None, 
                                         behaviourName=None,
                                         annotator=None, color=None),
                          "tasks": []}]
            
            
            
           
    @cfg.logClassFunction
    def addAnnotation(self):
        cfg.log.warning("not coded")
        
    @cfg.logClassFunction
    def removeAnnotation(self):
        cfg.log.warning("not coded")
            
    @cfg.logClassFunction
    def setPosition(self):
        cfg.log.warning("not coded")
            
    @cfg.logClassFunction
    def addAnno(self):
        cfg.log.warning("not coded")
            
    @cfg.logClassFunction
    def escapeAnno(self):
        cfg.log.warning("not coded")         
        
    
    
class AnnoViewItem(QtGui.QGraphicsRectItem):
    def __init__(self, annoView, rect):
        super(AnnoViewItem, self).__init__(None)
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.annoView = annoView
    #
    # def hoverEnterEvent(self, event):
    #     pen = QtGui.QPen(QtCore.Qt.red)
    #     self.setPen(pen)
    #     self.annoView.centerAt(self)
    #     return QtGui.QGraphicsRectItem.hoverEnterEvent(self, event)
    #
    # def hoverLeaveEvent(self, event):
    #     pen = QtGui.QPen(QtGui.QColor(0,0,0,0))
    #     self.setPen(pen)
    #     self.annoView.centerAt(None)
    #     return QtGui.QGraphicsRectItem.hoverLeaveEvent(self, event)
    #
    # def mousePressEvent(self, event):
    #     self.annoView.alterAnnotation(self)
    #     return QtGui.QGraphicsRectItem.mousePressEvent(self, event)

    
    
class AnnoView(QtGui.QWidget):
    
    @cfg.logClassFunction
    def __init__(self, parent, parentWidget, vialNo=None, behaviourName=None,
                 annotator=None, color=None, geo=None):
        super(AnnoView, self).__init__(parentWidget)
        #QGraphicsView.__init__(parent)
        
        # draw center markers of graphics view
        
        self.parentVP = parent
        
        if geo is not None:
            self.setGeometry(geo)
            self.width = geo.width()
            
        amWidth = 10
        cMarkerExtra = 5
        
        topBuffer = (geo.height() - amWidth) / 2
        self.activeMarker = QtGui.QLabel(parentWidget)
        self.activeMarker.setGeometry(QtCore.QRect(geo.x(), 
                                                   geo.y() + topBuffer,
                                                   amWidth, amWidth))
        self.activeMarker.setStyleSheet("""
        QLabel {{ 
        background-color: {0}
        }}""".format(color.name())) 
        self.activeMarker.setVisible(False)
        
            
        self.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        self.gV = QtGui.QGraphicsView(parentWidget)
        self.gV.setGeometry(QtCore.QRect(amWidth + 15, cMarkerExtra, geo.width(),
                                         geo.height()))
        self.gV.setFrameStyle(QtGui.QFrame.NoFrame)
        self.gV.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        
        self.cMarker1 = QtGui.QLabel(parentWidget)
        gvGeo = self.gV.geometry()
        self.cMarker1.setGeometry(QtCore.QRect(gvGeo.x() + gvGeo.width() / 2,
                                       0, 1, gvGeo.height() + cMarkerExtra * 2))

        self.cMarker1.setFrameStyle(QtGui.QFrame.VLine)
        self.cMarker1.raise_()
        
        
        
        self.prevConnectHooks = []
        parPos = self.mapToGlobal(QtCore.QPoint(0,0))
        for i in range(100):
            self.prevConnectHooks += [[QtCore.QPoint(parPos.x(), parPos.y()), 
                                       QtCore.QPoint(parPos.x(), 
                                                     parPos.y() - 3)]]
            parPos.setX(parPos.x() + 10)
        
        
        # initialization of parameters
        self.annotationDict = dict()
        self.color = QtGui.QColor(0,255,0,150)
        self.zoomLevels = [10,10,10,10,10,10,10]#[0.5, 0.6, 0.8, 1, 2, 5, 10]
        self.zoom = 2
        self.lines = dict()
        self.frames = dict()
        self.absIdx = dict()
        self.chunks = dict()
        
        self.scene = None
        self.selKey = None
        self.idx = None
        
        self.boxHeight = self.geometry().height()
        
        #filters
        self.vialNo = None
        self.behaviourName=None
        self.annotator=None
        
        
        self.erasingAnno = False
        self.addingAnno = False
        self.tempAnno = dict()

        self.inEditMode = False

        
        # setting values
        self.scene = QtGui.QGraphicsScene(self.gV)
#         self.scene.setSceneRect(QRectF(-50000, -20, 100000, 20))
        self.gV.setScene(self.scene)
        
        self.gV.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gV.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.vialNo = vialNo
        self.behaviourName = behaviourName
        self.annotator = annotator
        
        
        if color == None:
            self.color = QtGui.QColor(0,255,0,150)
        else:
            self.color = color
            
        colI = QtGui.QColor(0,0,0,0)
                    
        self.penA = QtGui.QPen(colI)
        self.brushA = QtGui.QBrush(self.color)    
              
        self.penI = QtGui.QPen(colI)
        self.brushI = QtGui.QBrush(colI)
        
        self.addList = []  #{key: (string), range: slice}
        self.removeList = []  #{key: (string), range: slice}
        
        self.frameAmount = 101 ## odd number please
        
        self.confidenceList = []
        self.tempRng = dict()
        self.lines = []
        self.frames = []
        self.annoViewRects = []
        
        
        for i in range(self.frameAmount):
            self.lines += [(self.scene.addLine(i, 0, i, self.boxHeight,  
                                        QtGui.QPen(QtGui.QColor(100,100,100))))]
            
        for i in range(self.frameAmount):
            self.frames += [AnnoViewItem(self, 
                                        QtCore.QRectF(i, 0, 1, self.boxHeight))]#self, QRectF(i, 0, 1, self.boxHeight))]                
            self.scene.addItem(self.frames[-1])
        
        center = self.frameAmount / 2 + 1
        self.gV.centerOn(self.frames[center])
        self.setZoom(0)

        
        
        
    # def sizeHint(self):
    #     return QtCore.QSize(self.width, int(self.boxHeight))
    #
    # def minimumSizeHint(self):
    #     return self.sizeHint()
        
            
    def centerAt(self, avItem):
        cfg.log.info("centerAt")
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                mid = (self.frameAmount + 1) / 2                
                [key, idx, conf] = self.confidenceList[i]
                
                cfg.logGUI.debug(json.dumps({"selectedItem":True,
                                         "key":key, 
                                         "idx":idx,
                                         "annotator":self.annotator,
                                         "behaviour":self.behaviourName}))
                
                self.parentVP.showTempFrame(i-mid)
                self.setPosition(key, idx, tempPositionOnly=True)
                
        if avItem is None:                
            cfg.logGUI.debug(json.dumps({"selectedItem":False,
                                     "key":None, 
                                     "idx":None,
                                     "annotator":self.annotator,
                                     "behaviour":self.behaviourName}))
            self.parentVP.resetTempFrame()
            
    def alterAnnotation(self, avItem):        
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                if self.addingAnno:
                    self.parentVP.addAnno(annotator=self.annotator[0], 
                                          behaviour=self.behaviourName[0],
                                          confidence=1)
                elif self.erasingAnno:
                    self.parentVP.eraseAnno(annotator=self.annotator[0], 
                                          behaviour=self.behaviourName[0])
                else:                  
                    key = self.confidenceList[i].key
                    idx = self.confidenceList[i].idx  
                    if self.annotationDict[key].getFrame(idx) is not None:
                        self.parentVP.eraseAnno(annotator=self.annotator[0], 
                                              behaviour=self.behaviourName[0])
                    else: 
                        self.parentVP.addAnno(annotator=self.annotator[0], 
                                              behaviour=self.behaviourName[0],
                                              confidence=1)
#                 
                
        if avItem is None:
            self.parentVP.resetTempFrame()
        
    @cfg.logClassFunction
    def addAnnotation(self, annotation, key, addAllAtOnce=True):
        """
        adds an annotation to a scene
        """
        cfg.log.info("beginning")
        if self.vialNo is None:
            filt = Annotation.AnnotationFilter([0], self.annotator, 
                                                        self.behaviourName)
        else:
            filt = Annotation.AnnotationFilter(self.vialNo, self.annotator, 
                                                        self.behaviourName)

        self.annotationDict[key] = annotation.filterFrameList(filt, exactMatch=False)

        cfg.log.info("end")
        
        return
#         
    @cfg.logClassFunction
    def removeAnnotation(self, key, rng=None):
        if key in self.annotationDict.keys():
            del self.annotationDict[key]   
        
    @cfg.logClassFunction
    def setPosition(self, key=None, idx=None, tempPositionOnly=False, 
                    metadata = None):
        ts = time.time()
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
        if metadata is None:
            metadata = {"confidence":1}    
        
                    
        if not tempPositionOnly:
            self.selKey = key
            self.idx = idx

        self.addTempAnno(key, idx, metadata)

        # t0 = time.time()
        self.updateConfidenceList()
        # t1 = time.time()
        self.updateGraphicView()
        # t2 = time.time()

        # te = time.time()
        # cfg.log.info("setting AnnoView positions in \n t1: {0} sec\n t2: {1} sec\n total: {2} sec\n ex1: {3} sec".format(
        #     t1 - t0, t2 - t1, te-ts, 0))


    @cfg.logClassFunction
    def setFilter(self, vialNo=None, behaviourName=None, annotator=None):
        self.vialNo = vialNo
        self.behaviourName = behaviourName
        self.annotator = annotator
        
    @cfg.logClassFunction
    def setZoom(self, zoomLevel):
        #scale absolute
        scale = self.zoomLevels[self.zoom]
#         else:
        for line in self.lines:
            line.setVisible(True)
        
        self.gV.setTransform(QtGui.QTransform().scale(scale, 1))
        
        self.zoom = zoomLevel
        self.updateGraphicView()
        
    @cfg.logClassFunction
    def setColor(self, color):
        self.color = color
        self.clearScene()
        self.populateScene()
        
    @cfg.logClassFunction
    def updateConfidenceList(self, key=None, idx=None):
        """
        Args:
            lst ([KeyIdxPair])
            
        """
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx

        # ts = time.time()

        cfg.log.debug("updateConfidenceList {0} \n [{1}]".format(key, idx))
        self.confidenceList = []
        # for first frame annotation within the range        
        dist2first = (self.frameAmount - 1) / 2
        remainingFrames = idx     
        keyList = sorted(self.annotationDict.keys())
        # find position of key in the annotationList
        # (expect each key to be present only once)
        keyPosList =  [i for i,x in enumerate(keyList) if x == key]
        if len(keyPosList):
            curKeyPos = keyPosList[0]
        else:
            # was not loaded yet, therefore set all frames to None
            for i in range(self.frameAmount):
                self.confidenceList += [KeyIdxPair(None, None, [None])]
            return

        # t0 = time.time()

        startIdx = None
        startKey = None
        while dist2first > 0:
            if (remainingFrames - dist2first) < 0:
                dist2first -= remainingFrames
                curKeyPos -= 1
                if curKeyPos < 0:
                    curKeyPos = 0
                    startIdx = 0
                    startKey = keyList[curKeyPos]
                    cfg.log.debug("dist2First {0}".format(dist2first))
                    for i in range(dist2first + 1):
                        self.confidenceList += [KeyIdxPair(None, None, [None])]
                    break
                else:
                    remainingFrames = \
                         self.annotationDict[keyList[curKeyPos]].getLength()
            else:
                startIdx = remainingFrames - (dist2first + 1) 
                startKey = keyList[curKeyPos]
                break

        # fill confidence list
        curIdx = startIdx
        curKey = startKey
        
        tempKeys = self.tempRng.keys()
        if self.addingAnno:
            cfg.log.info("{0}".format(self.tempRng))


        ex0 = 0
        ex1 = 0

        # t1 = time.time()

        # prebuffer lengths as queries would sum up immensely inside the loop
        annoLengths = dict()
        for k, anno in self.annotationDict.items():
            annoLengths[k] = anno.getLength()

        # prebuffer all needed key/index pairs so that they can be querried
        # in one go
        rng = {curKey: []}
        for i in range(self.frameAmount - len(self.confidenceList)):
            if curIdx >= annoLengths[curKey]:
                if (curKeyPos + 1) >= len(keyList):
                    # end of file list
                    # self.confidenceList += [KeyIdxPair(None, None, [None])]
                    continue

                curKeyPos += 1
                curKey = keyList[curKeyPos]
                curIdx = 0
                rng[curKey] = []

            rng[curKey].append(curIdx)
            curIdx += 1

        # t2 = time.time()
        # s0 = 0
        # s1 = 0
        # s2 = 0

        for curKey, indeces in sorted(rng.items()):
            slc = slice(min(indeces), max(indeces) + 1)
            # t11 = time.time()
            df = self.annotationDict[curKey].getFrame(slc)

            # t12 = time.time()

            if df is not None:
                labelledFrameIdces = df.index.levels[0]
            else:
                labelledFrameIdces = []

            # t13 = time.time()

            for curIdx in indeces:
                if (self.addingAnno
                                and (curKey in tempKeys)
                                and (curIdx in self.tempRng[curKey])):
                    conf = [self.tempValue[curKey][curIdx]["confidence"]]
                elif (self.erasingAnno
                                and (curKey in tempKeys)
                                and (curIdx in self.tempRng[curKey])):
                    conf = [None]
                else:
                    if curIdx in labelledFrameIdces:
                        conf = [1]
                    else:
                        conf = [None]

                self.confidenceList += [KeyIdxPair(curKey, curIdx, conf)]

            # t14 = time.time()
            # s0 += t12 - t11
            # s1 += t13 - t12
            # s2 += t14 - t13
        #
        # t3 = time.time()
        # cfg.log.info("setting AnnoView positions in \n t1: {0} sec\n t2: {1} sec\n ex0: {2} sec\n ex1: {3} sec\n ex2: {4} sec".format(
        #     t2 - ts, t3 - t2, s0, s1, s2))

#
#         for i in range(self.frameAmount - len(self.confidenceList)):
#             t0 = time.time()
#             length = annoLengths[curKey]
#             # length = self.annotationDict[curKey].getLength()
#             et1 = time.time()
#             if curIdx >= length:
#                 if (curKeyPos + 1) >= len(keyList):
#                     # end of file list
#                     self.confidenceList += [KeyIdxPair(None, None, [None])]
#                     continue
#
#                 curKeyPos += 1
#                 curKey = keyList[curKeyPos]
#                 curIdx = 0
#
#             t1 = time.time()
#             if (self.addingAnno
#                             and (curKey in tempKeys)
#                             and (curIdx in self.tempRng[curKey])):
#                 conf = [self.tempValue[curKey][curIdx]["confidence"]]
#             elif (self.erasingAnno
#                             and (curKey in tempKeys)
#                             and (curIdx in self.tempRng[curKey])):
#                 conf = [None]
#             else:
#                 1/0
# #                 if type(self.annotationDict[curKey].frameList[curIdx]) == dict:
# #                     conf = self.annotationDict[curKey].frameList[curIdx]['confidence']
# #                 else:
# #                     conf = self.annotationDict[curKey].frameList[curIdx]
#                 et2 = time.time()
#                 df = self.annotationDict[curKey].getFrame(curIdx)
#                 et3 = time.time()
#                 if df is None:
#                     conf = [None]
#                 else:
#                     # if self.vialNo == None:
#                     conf = Annotation.getPropertyFromFrameAnno(
#                            df,
#                             "confidence")
#                     # else:
#                     #     conf = [Annotation.getPropertyFromFrameAnno(
#                     #         self.annotationDict[curKey].getFrame(curIdx),
#                     #             "confidence")]
#                     #
#             t2 = time.time()
#
#             s0 += t1 - t0
#             s1 += t2 - t1
#
#             ex0 += et1 - t0
#             # ex1 += et3 - et2
#
#             self.confidenceList += [KeyIdxPair(curKey, curIdx, conf)]
#             curIdx += 1
#
#
#
#         t3 = time.time()
#         cfg.log.info("setting AnnoView positions in \n t1: {0} sec\n t2: {1} sec\n ex0: {2} sec\n ex1: {3} sec".format(
#             s0, s1, ex0, ex1))

    @cfg.logClassFunction
    def updateGraphicView(self):
        for i in range(len(self.confidenceList)):
            conf = self.confidenceList[i].conf
            tmp = (not None) in conf
            if tmp:
                self.frames[i].setBrush(self.brushA)
                self.frames[i].setPen(self.penA)
            else:
                self.frames[i].setBrush(self.brushI)
                self.frames[i].setPen(self.penI)

            self.frames[i].update()

        self.activeMarker.setVisible(self.addingAnno or self.erasingAnno)
        
    @cfg.logClassFunction
    def addAnno(self, key=None, idx=None, metadata=None):
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
        if metadata is None:
            metadata = {"confidence":1}
            

        self.tempRng = dict()
        self.tempAnno = dict()
        self.tempValue = dict()
        
        if not self.addingAnno:            
            self.addingAnno = True
            #self.tempStart = [self.selKey, self.idx]
            self.tempStart = bsc.FramePosition(self.annotationDict, key, idx)
            self.setPosition(key, idx, tempPositionOnly=True, metadata=metadata)
        else:
            self.addingAnno = False  
            self.activeMarker.setVisible(False)

             
    @cfg.logClassFunction
    def eraseAnno(self, key=None, idx=None):
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
            
        if not self.erasingAnno:
            self.erasingAnno = True
            self.tempStart = bsc.FramePosition(self.annotationDict, key, idx)
            self.tempAnno = dict()
            self.setPosition(key, idx, tempPositionOnly=True)
        else:
            self.erasingAnno = False
            self.tempRng = dict()
            self.tempAnno = dict()
            self.activeMarker.setVisible(False)

            
    @cfg.logClassFunction
    def resetAnno(self):
        if self.addingAnno:
            for key in self.tempAnno:
                for idx in  self.tempAnno[key]:
                    self.scene.removeItem(self.tempAnno[key][idx])            
                     
        if self.erasingAnno:            
            for key in self.tempAnno:
                for idx in self.tempAnno[key]:
                    self.frames[key][idx].setVisible(True)  
     
    @cfg.logClassFunction
    def escapeAnno(self):
        self.resetAnno()
        self.erasingAnno = False
        self.addingAnno = False
             
             
    @cfg.logClassFunction
    def addTempAnno(self, key=None, idx=None, metadata=None):
        if self.inEditMode:
            return

        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
            
        if metadata == None:
            metadata = {"confidence": 1}
            
        self.resetAnno()
        
        if self.addingAnno: 
            if not key in self.tempValue.keys():
                self.tempValue[key] = dict()
            
            self.tempValue[key][idx] = metadata
        
        if self.addingAnno or self.erasingAnno:
            tempEnd = bsc.FramePosition(self.annotationDict, key, idx)            
            self.tempRng = bsc.generateRangeValuesFromKeys(self.tempStart, tempEnd) 