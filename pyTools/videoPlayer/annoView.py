from PySide import QtGui
from PySide import QtCore


import pyTools.videoProc.annotation as Annotation
import pyTools.misc.basic as bsc 
import pyTools.misc.config as cfg
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

    def hoverEnterEvent(self, event):
        pen = QtGui.QPen(QtCore.Qt.red)
        self.setPen(pen)
        self.annoView.centerAt(self)
        QtGui.QGraphicsRectItem.hoverEnterEvent(self, event)
    
    def hoverLeaveEvent(self, event):
        pen = QtGui.QPen(QtGui.QColor(0,0,0,0))
        self.setPen(pen)
        self.annoView.centerAt(None)
        QtGui.QGraphicsRectItem.hoverLeaveEvent(self, event)
        
    def mousePressEvent(self, event):
        self.annoView.alterAnnotation(self)
        QtGui.QGraphicsRectItem.mousePressEvent(self, event)

    
    
class AnnoView(QtGui.QWidget):
    
    @cfg.logClassFunction
    def __init__(self, parent, vialNo=None, behaviourName=None, annotator=None,
                color=None, geo=None):
        super(AnnoView, self).__init__(parent)
        #QGraphicsView.__init__(parent)
        
        # draw center markers of graphics view
        
        if geo is not None:
            self.setGeometry(geo)
            
        amWidth = 10
        topBuffer = (geo.height() - amWidth) / 2
        self.activeMarker = QtGui.QLabel(parent)
        self.activeMarker.setGeometry(QtCore.QRect(geo.x() - amWidth - 5, 
                                                   geo.y() + topBuffer,
                                                   amWidth, amWidth))
        self.activeMarker.setStyleSheet("""
        QLabel {{ 
        background-color: {0}
        }}""".format(color.name())) 
        self.activeMarker.setVisible(False)
        
            
        self.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        self.gV = QtGui.QGraphicsView(self)
        self.gV.setGeometry(QtCore.QRect(-5, 0, geo.width(), geo.height()))
        self.gV.setFrameStyle(QtGui.QFrame.NoFrame)
        self.gV.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        
        self.cMarker1 = QtGui.QLabel(parent)
        self.cMarker1.setGeometry(QtCore.QRect(geo.x() + geo.width() / 2, 
                                       geo.y() -15, 1, geo.height() + 30))
        self.cMarker1.setFrameStyle(QtGui.QFrame.VLine)
        self.cMarker1.raise_()
        
        
        
        self.prevConnectHooks = []
        parPos = self.mapToParent(QtCore.QPoint(0,0))
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
            
    def centerAt(self, avItem):
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                mid = (self.frameAmount + 1) / 2                
                [key, idx, conf] = self.confidenceList[i]
                
                cfg.logGUI.debug(json.dumps({"selectedItem":True,
                                         "key":key, 
                                         "idx":idx,
                                         "annotator":self.annotator,
                                         "behaviour":self.behaviourName}))
                
                self.parent().showTempFrame(i-mid)
                self.setPosition(key, idx, tempPositionOnly=True)
                
        if avItem is None:                
            cfg.logGUI.debug(json.dumps({"selectedItem":False,
                                     "key":None, 
                                     "idx":None,
                                     "annotator":self.annotator,
                                     "behaviour":self.behaviourName}))
            self.parent().resetTempFrame()
            
    def alterAnnotation(self, avItem):        
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                if self.addingAnno:
                    self.parent().addAnno(annotator=self.annotator[0], 
                                          behaviour=self.behaviourName[0],
                                          confidence=1)
                elif self.erasingAnno:
                    self.parent().eraseAnno(annotator=self.annotator[0], 
                                          behaviour=self.behaviourName[0])
                else:                  
                    key = self.confidenceList[i].key
                    idx = self.confidenceList[i].idx  
                    if self.annotationDict[key].frameList[idx] is not None:
                        self.parent().eraseAnno(annotator=self.annotator[0], 
                                              behaviour=self.behaviourName[0])
                    else: 
                        self.parent().addAnno(annotator=self.annotator[0], 
                                              behaviour=self.behaviourName[0],
                                              confidence=1)
#                 
                
        if avItem is None:
            self.parent().resetTempFrame()
        
    @cfg.logClassFunction
    def addAnnotation(self, annotation, key, addAllAtOnce=True):
        """
        adds an annotation to a scene
        """
        if self.vialNo is None:
            filt = Annotation.AnnotationFilter([0], self.annotator, 
                                                        self.behaviourName)
        else:
            filt = Annotation.AnnotationFilter(self.vialNo, self.annotator, 
                                                        self.behaviourName)

        self.annotationDict[key] = annotation.filterFrameList(filt)
        
        
        return
#         
    @cfg.logClassFunction
    def removeAnnotation(self, key, rng=None):
        if key in self.annotationDict.keys():
            del self.annotationDict[key]   
        
    @cfg.logClassFunction
    def setPosition(self, key=None, idx=None, tempPositionOnly=False, 
                    metadata = None):
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
        self.updateConfidenceList()#(key, idx)
        self.updateGraphicView()
        
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
                         len(self.annotationDict[keyList[curKeyPos]].frameList)
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
        
        for i in range(self.frameAmount - len(self.confidenceList)):
            if curIdx >= len(self.annotationDict[curKey].frameList):
                if (curKeyPos + 1) >= len(keyList):
                    # end of file list
                    self.confidenceList += [KeyIdxPair(None, None, [None])]
                    continue                  
                    
                curKeyPos += 1
                curKey = keyList[curKeyPos]
                curIdx = 0
                            
            if (self.addingAnno 
                            and (curKey in tempKeys) 
                            and (curIdx in self.tempRng[curKey])):
                conf = [self.tempValue[curKey][curIdx]["confidence"]]
            elif (self.erasingAnno 
                            and (curKey in tempKeys) 
                            and (curIdx in self.tempRng[curKey])):
                conf = [None]
            else:
#                 if type(self.annotationDict[curKey].frameList[curIdx]) == dict:
#                     conf = self.annotationDict[curKey].frameList[curIdx]['confidence']                    
#                 else:
#                     conf = self.annotationDict[curKey].frameList[curIdx]
                if self.annotationDict[curKey].frameList[curIdx] == [None]:
                    conf = [None]
                else:
                    if self.vialNo == None:
                        conf = Annotation.getPropertyFromFrameAnno(
                               self.annotationDict[curKey].frameList[curIdx][0],
                                "confidence")
                    else:                        
                        conf = Annotation.getPropertyFromFrameAnno(
                            self.annotationDict[curKey].frameList[curIdx][0],
                                "confidence")
                                  
            self.confidenceList += [KeyIdxPair(curKey, curIdx, conf)]            
            curIdx += 1     

    @cfg.logClassFunction
    def updateGraphicView(self):
        for i in range(len(self.confidenceList)):   
            conf = self.confidenceList[i].conf
            if [True for c in conf if c != None]:
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