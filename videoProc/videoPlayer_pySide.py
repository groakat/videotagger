import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from PySide.QtGui import *
from PySide.QtCore import * 
from PySide.QtOpenGL import * 


from videoPlayer_auto import Ui_Form

from pyTools.system.videoExplorer import *
from pyTools.imgProc.imgViewer import *
from pyTools.videoProc.annotation import *
import pyTools.misc.basic as bsc 
import pyTools.misc.config as cfg
import copy

import numpy as np
import scipy.misc as scim
#import matplotlib as mpl
import pylab as plt
import time
import copy

from qimage2ndarray import *



#from qimage2ndarray import *
# from PyQt4.uic.Compiler.qtproxies import QtCore

from collections import namedtuple


import json
import logging, logging.handlers
import os, sys


            
#################################################################### 

KeyIdxPair = namedtuple('KeyIdxPair', ['key', 'idx', 'conf'])

####################################################################

# def np2qimage(a):
#     import numpy as np  
#     a = a.astype(np.uint32, order='C', copy=True)  
# #     qi = (255 << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
# #     return QImage(qi, a.shape[1], a.shape[0], 
# #                   QImage.Format_ARGB32)
# #     import Image
# #     im = Image.fromarray(a.astype(np.uint8))
# #     data = im.convert("RGBA").tostring("raw", "RGBA")
#     
# #     data = (np.uint8(255) << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
#     data = (255 << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
#     image = QImage(data.data, a.shape[1], a.shape[0], QImage.Format_ARGB32)
#     
#     return image

def np2qimage(a):
    import numpy as np  
    a = a.astype(np.uint32)  
#     qi = (255 << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
#     return QImage(qi, a.shape[1], a.shape[0], 
#                   QImage.Format_ARGB32)
#     import Image
#     im = Image.fromarray(a.astype(np.uint8))
#     data = im.convert("RGBA").tostring("raw", "RGBA")
    
    data = (np.uint32(255) << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
#     data = (np.uint8(255) << 24 | np.bitwise_or(np.bitwise_or(a[:,:,0] << 16, a[:,:,1] << 8), a[:,:,2])).flatten()
    image = QImage(data.data, a.shape[1], a.shape[0], QImage.Format_ARGB32)
    
    return image

def maxOfSelectedVials(selectedVials):
    if selectedVials is None:
        return 0
    else:
        return max(selectedVials)


#################################################################### 
class MyListModel(QAbstractListModel): 
    def __init__(self, datain, parent=None, *args): 
        """ datain: a list where each item is a row
        """
#         QAbstractListModel.__init__(self, parent, *args)
        super(MyListModel, self).__init__(parent) 
        self.listdata = datain
 
    def rowCount(self, parent=QModelIndex()): 
        return len(self.listdata) 
 
    def data(self, index, role): 
        if index.isValid() and role == Qt.DisplayRole:
            return self.listdata[index.row()]
        else: 
            return None
    
    
class MouseFilterObj(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.increment = 0
        
    @cfg.logClassFunction
    def eventFilter(self, obj, event):
        cfg.log.debug("mouse event!!!!!!!!!!!!!! {0}".format(event.type()))
        if (event.type() == QEvent.GraphicsSceneMouseMove):
            self.parent.setCropCenter(int(event.scenePos().x()), 
                                      int( event.scenePos().y()),
                                      increment = self.increment)
#             QApplication.setOverrideCursor(QCursor(Qt.BlankCursor ))
#             QWSServer.setCursorVisible( False )
            
        if (event.type() == QEvent.Leave):
            self.parent.setCropCenter(None, None, increment=self.increment)
#             QWSServer.setCursorVisible( True )
            
        if (event.type() == QEvent.GraphicsSceneWheel):
            self.increment -= event.delta()
            
        return False
            

class filterObj(QObject):
    def __init__(self, parent, keyMap=None, stepSize=None, oneClickAnnotation=None):
        QObject.__init__(self)
        self.parent = parent
        
        if keyMap is None:
            self.keyMap = { "stop": Qt.Key_F,
                            "step-f": Qt.Key_G,
                            "step-b": Qt.Key_D,
                            "fwd-1": Qt.Key_T,
                            "fwd-2": Qt.Key_V,
                            "fwd-3": Qt.Key_B,
                            "fwd-4": Qt.Key_N,
                            "fwd-5": Qt.Key_H,
                            "fwd-6": Qt.Key_J,
                            "bwd-1": Qt.Key_E,
                            "bwd-2": Qt.Key_X,
                            "bwd-3": Qt.Key_Z,
                            "bwd-4": Qt.Key_Backslash,
                            "bwd-5": Qt.Key_S,
                            "bwd-6": Qt.Key_A,
                            "escape": Qt.Key_Escape,
                            "anno-1": Qt.Key_1,
                            "anno-2": Qt.Key_2,
                            "anno-3": Qt.Key_3,
                            "anno-4": Qt.Key_3,
                            "quit-anno": Qt.Key_Q,
                            "info": Qt.Key_I}
        else:
            self.keyMap = keyMap
                        
        if stepSize is None:
            self.stepSize = { "stop": 0,
                            "step-f": 1,
                            "step-b": -1,
                            "allow-steps": True,
                            "fwd-1": 1,
                            "fwd-2": 3,
                            "fwd-3": 10,
                            "fwd-4": 20,
                            "fwd-5": 40,
                            "fwd-6": 60,
                            "bwd-1": -1,
                            "bwd-2": -3,
                            "bwd-3": -10,
                            "bwd-4": -20,
                            "bwd-5": -40,
                            "bwd-6": -60}
        else:
            self.stepSize = stepSize
                    
        if oneClickAnnotation is None:
            self.oneClickAnnotation = [False] * 4            
        else:
            self.oneClickAnnotation = [oneClickAnnotation] * 4  
            
        self.inConstantSpeed = False
        self.orignalStepSize = self.stepSize
            
    def swapToConstantSpeed(self, speed):
        
        if self.inConstantSpeed:
            return
        
        self.orignalStepSize = self.stepSize
        
        self.stepSize = { "stop": speed,
                        "step-f": speed,
                        "step-b": speed,
                        "allow-steps": False,
                        "fwd-1": speed,
                        "fwd-2": speed,
                        "fwd-3": speed,
                        "fwd-4": speed,
                        "fwd-5": speed,
                        "fwd-6": speed,
                        "bwd-1": speed,
                        "bwd-2": speed,
                        "bwd-3": speed,
                        "bwd-4": speed,
                        "bwd-5": speed,
                        "bwd-6": speed}
        
    def swapFromConstantSpeed(self):
        if not self.inConstantSpeed:
            self.stepSize = self.orignalStepSize
        
            
    @cfg.logClassFunction
    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress):
            key = event.key()
                    
            if(event.modifiers() == Qt.ControlModifier):
                if(key == Qt.Key_S):
                    cfg.log.info('saving all annotations')
                    self.parent.saveAll()
                    event.setAccepted(True)
            
            else:
                self.parent.showTrajectTemp = True
                    
                        
                if key == self.keyMap["stop"]:
                    # stop playback
                    if self.stepSize["allow-steps"] == "true":
                        self.parent.play = False
                    else:
                        self.parent.play = True
                        
                    self.parent.increment = self.stepSize["stop"]
                    
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["step-f"]:
                    # step-wise forward
                    if self.stepSize["allow-steps"]:
                        self.parent.play = False
                        self.parent.showNextFrame(self.stepSize["step-f"])
                    else:
                        self.parent.play = True
                        
                    self.parent.increment = self.stepSize["step-f"]
    #                 self.parent.showNextFrame(self.increment)
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                
                if key == self.keyMap["step-b"]:
                    # step-wise backward
                    if self.stepSize["allow-steps"]:
                        self.parent.play = False
                        self.parent.showNextFrame(self.stepSize["step-b"])
                    else:
                        self.parent.play = True
                        
                    self.increment = self.stepSize["step-b"]
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-1"]:
                    # real-time playback
                    self.parent.increment = self.stepSize["fwd-1"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                        
                if key == self.keyMap["bwd-1"]:
                    # real-time playback
                    self.parent.increment = self.stepSize["bwd-1"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-2"]:
                    # 
                    self.parent.increment = self.stepSize["fwd-2"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-3"]:
                    self.parent.increment = self.stepSize["fwd-3"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-4"]:
                    self.parent.increment = self.stepSize["fwd-4"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-5"]:
                    self.parent.increment = self.stepSize["fwd-5"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-6"]:
                    self.parent.increment = self.stepSize["fwd-6"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
    #                     self.tempTrajSwap = True
    #                     self.showTrajectories(False)
                    
                    
                if key == self.keyMap["bwd-2"]:
                    self.parent.increment = self.stepSize["bwd-2"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-3"]:
                    self.parent.increment = self.stepSize["bwd-3"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-4"]:
                    self.parent.increment = self.stepSize["bwd-4"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-5"]:
                    self.parent.increment = self.stepSize["bwd-5"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-6"]:
                    self.parent.increment = self.stepSize["bwd-6"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
    #                     self.tempTrajSwap = True
    #                     self.showTrajectories(False)
                    
                        
                if key == self.keyMap["info"]:
                    cfg.log.debug("position length: {0}".format(self.parent.vh.getCurrentPositionLength()))
                    cfg.log.debug("video length: {0}".format(self.parent.vh.getCurrentVideoLength()))
                    
                if key == self.keyMap["escape"]:
                    self.parent.escapeAnnotationAlteration()
                    
                if key == self.keyMap["anno-1"]:
                    self.parent.alterAnnotation(self.parent.annotations[0]["annot"], 
                                        self.parent.annotations[0]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[0])
                    
                if key == self.keyMap["anno-2"]:
                    self.parent.alterAnnotation(self.parent.annotations[1]["annot"], 
                                        self.parent.annotations[1]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[1])
                    
                if key == self.keyMap["anno-3"]:
                    self.parent.alterAnnotation(self.parent.annotations[2]["annot"], 
                                        self.parent.annotations[2]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[2])
                    
                if key == self.keyMap["anno-4"]:
                    self.parent.alterAnnotation(self.parent.annotations[3]["annot"], 
                                        self.parent.annotations[3]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[3])
                    
                if key == self.keyMap["quit-anno"]:
                    self.parent.addingAnnotations = not self.parent.addingAnnotations
                    if not self.parent.addingAnnotations:
                        cfg.log.info("changed to erasing mode")
                        self.parent.ui.lbl_eraser.setVisible(True)                      
                                
                    else:
                        cfg.log.info("changed to adding mode")                    
                        self.parent.ui.lbl_eraser.setVisible(False)
                    
                    logGUI.info(json.dumps({"addingAnnotations": 
                                            self.parent.addingAnnotations}))
                    
                self.parent.ui.speed_lbl.setText("Speed: {0}x".format(self.parent.increment)) 
            
        
        return False

                  
#########################################################################

class videoPlayer(QMainWindow):      
    quit = Signal()
     
    def __init__(self, path, 
                        annotations,
                        backgroundPath,
                        selectedVial,
                        vialROI,
                        videoFormat='avi',
                        filterObjArgs=None,
                        startVideoName=None,
                        rewindOnClick=False,
                        videoOnly=True,
                        videoEnding='.avi', #'.v0.avi'
                        ):
        """
        
        args:
            path (string):
                                root path to patches
            videoFormat (string):
                                postfix for video format *(without dot)*
        """
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.cb_trajectory.setChecked(True)
        
        
        if filterObjArgs is None:
            filterObjArgs = {"keyMap":None, "stepSize":None,
                             "oneClickAnnotation":None}
        
        self.eventFilter = filterObj(self, **filterObjArgs)
        self.installEventFilter(self.eventFilter)
        self.connectSignals()       
        
        self.mouseEventFilter = MouseFilterObj(self)
        
        
        self.fileList = self.providePosList(path, ending=videoEnding)    
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.fileList))
        
        self.videoFormat = videoFormat
        self.idx = 0       
        self.play = False
        self.frameIdx = -1
        self.showTraject = False
        self.tempTrajSwap = True
        self.trajNo = 0
        self.trajLabels = []
        self.frames = []
        self.increment = 0
        self.tempIncrement = 0
        self.stop = False
        self.addingAnnotations = True
        self.ui.lbl_eraser.setVisible(False)        
        self.prevSize = 100
        
        
        self.rewindOnClick = rewindOnClick
        self.rewindStepSize = 500
        self.rewinding = False
        self.rewindCnt = 0
        
        if self.rewindOnClick:
            self.eventFilter.oneClickAnnotation = [True, True, True, True]
        
        self.annotations = annotations 
#                             [{"annot": "peter",
#                              "behav": "falling"},
#                             {"annot": "peter",
#                              "behav": "dropping"},
#                             {"annot": "peter",
#                              "behav": "struggling"},
#                             ]
        self.tmpAnnotation = Annotation(0, [''])
        self.annotationRoiLabels = []
        self.annoIsOpen = False
        self.metadata = []
        self.confidence = 0
        
        
        self.vialRoi = vialROI#[[350, 660], [661, 960], [971, 1260], [1290, 1590]]
        
        if type(selectedVial) == int:
            self.selectedVial = [selectedVial]
        else:
            self.selectedVial = selectedVial#3
        self.ui.lbl_vial.setText("vial: {0}".format(self.selectedVial))
                
                
        self.videoOnly = videoOnly
#         self.vh.changedFile.connect(self.changeVideo)
        
        
        self.filterList = []
        
        
        #self.setVideo(0)
        if startVideoName == None:
            startIdx = 0
        else:            
            startIdx = [i for i in range(len(self.fileList)) 
                            if self.fileList[i].find(startVideoName) != -1]
            if not startIdx:
                raise ValueError("startVideo not found in videoPath")
            elif  len(startIdx) > 1:
                raise ValueError("startVideo not unique")
            
            startIdx = startIdx[0]
        
        self.vh = VideoHandler(self.fileList, self.changeVideo, 
                               self.selectedVial, startIdx=startIdx)
        
        
        self.updateFrameList(range(2000))
        
        self.configureUI()
        
        if not self.videoOnly:
            self.setBackground(backgroundPath)#"/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        else:
            self.setBackground()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showNextFrame)
        self.timerID = None
        
        
        self.ui.cb_trajectory.setChecked(self.showTraject)
        self.showTrajectories(self.showTraject)
        self.show()        
        logGUI.info(json.dumps(
                            {"message":'"--------- opened GUI ------------"'})) 
#         logGUI.info(json.dumps({"args":
#                                     {"selectedVial":self.selectedVial,
#                                      "annotations":self.annotations
#                                     }\
#                                 }))
        
        self.setCropCenter(None, None)
        
        self.selectVideo(startIdx)
        
#         self.exec_()
        
        
        
        #glMatrixMode(GL_PROJECTION)
        
        
    @cfg.logClassFunction
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.pb_compDist.clicked.connect(self.compDistances)
        self.ui.pb_test.clicked.connect(self.testFunction)
        self.ui.pb_addAnno.clicked.connect(self.addAnno)
        self.ui.pb_eraseAnno.clicked.connect(self.eraseAnno)
        self.ui.pb_jmp2frame.clicked.connect(self.jump2selectedVideo)
        
        self.ui.sldr_paths.valueChanged.connect(self.selectVideo)
        self.ui.lv_frames.activated.connect(self.selectFrame)
        self.ui.lv_jmp.activated.connect(self.selectFrameJump)
        self.ui.lv_paths.activated.connect(self.selectVideoLV)
        
        self.ui.cb_trajectory.stateChanged.connect(self.showTrajectories)
        
        
        
        #~ self.ui.pb_startVideo.installEventFilter(self.eventFilter)
        self.ui.pb_stopVideo.installEventFilter(self.eventFilter)
        self.ui.pb_compDist.installEventFilter(self.eventFilter)
        self.ui.pb_test.installEventFilter(self.eventFilter)
        self.ui.pb_addAnno.installEventFilter(self.eventFilter)
        self.ui.pb_eraseAnno.installEventFilter(self.eventFilter)
        self.ui.sldr_paths.installEventFilter(self.eventFilter)
        self.ui.lv_frames.installEventFilter(self.eventFilter)
        self.ui.lv_jmp.installEventFilter(self.eventFilter)
        self.ui.lv_paths.installEventFilter(self.eventFilter)
        self.ui.cb_trajectory.installEventFilter(self.eventFilter)
        
    @cfg.logClassFunction
    def configureUI(self):
        
        self.xFactor = 1 # self.ui.label.width() / 1920.0
        self.yFactor = 1 #self.ui.label.height() / 1080.0
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        
        self.ui.lbl_v0.setStyleSheet("background-color: rgba(255, 255, 255, 10);")
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
        self.createAnnoViews()
        
    def createAnnoView(self, xPos, yPos, width, height, idx):
        self.annoViewList += [AnnoView(self, vialNo=self.selectedVial, 
                                       annotator=[self.annotations[idx]["annot"]], 
                                       behaviourName=[self.annotations[idx]["behav"]], 
                                       color = self.annotations[idx]["color"], 
                                       geo=QRect(xPos, yPos, width, height))]
#         self.annoViewList[-1].setGeometry(QRect(xPos, yPos, width, height))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])     
        self.annoViewLabel += [QLabel(self)]
        self.annoViewLabel[-1].setText("{0}: {1}".format(\
                                            self.annotations[idx]["annot"],
                                            self.annotations[idx]["behav"]))
        self.annoViewLabel[-1].move(xPos + width + 10, yPos)          
        self.annoViewLabel[-1].adjustSize() 
        
        
    @cfg.logClassFunction
    def createAnnoViews(self):
        self.annoViewList = []
        self.annoViewLabel = []
        
        yPos = 430 #+ self.prevSize
        xPos = 60 
        height = 20
        width = 1000
        
        self.annotations[0]["color"] = QColor(0,0,255,150)
        self.annotations[1]["color"] = QColor(0,0,255,150)
        self.annotations[2]["color"] = QColor(0,255,0,150)
        self.annotations[3]["color"] = QColor(0,255,0,150)
        

#         self.createPrevFrames(xPos - 15, yPos - (self.prevSize + 20))
        self.createPrevFrames(xPos + 135, yPos - (self.prevSize + 20))
        
#         self.annoViewList += [AnnoView(self, vialNo=self.selectedVial, 
#                                        annotator=[self.annotations[0]["annot"]], 
#                                        behaviourName=[self.annotations[0]["behav"]], 
#                                        color = self.annotations[0]["color"],
#                                        geo=QRect(xPos, yPos, width, height))]
# #         self.annoViewList[-1].setGeometry(QRect(xPos, yPos, width, height))
#         self.annoViewList[-1].show()
#         self.vh.addAnnoView(self.annoViewList[-1]) 
#         self.annoViewLabel += [QLabel(self)]
#         self.annoViewLabel[-1].setText("{0}: {1}".format(\
#                                             self.annotations[0]["annot"],
#                                             self.annotations[0]["behav"]))
#         self.annoViewLabel[-1].move(xPos + width + 10, yPos)        
#         self.annoViewLabel[-1].adjustSize()       
#         yPos += height + 5
#         
#         self.annoViewList += [AnnoView(self, vialNo=self.selectedVial, 
#                                        annotator=[self.annotations[1]["annot"]], 
#                                        behaviourName=[self.annotations[1]["behav"]], 
#                                        color = self.annotations[1]["color"], 
#                                        geo=QRect(xPos, yPos, width, height))]
# #         self.annoViewList[-1].setGeometry()
#         self.annoViewList[-1].show()
#         self.vh.addAnnoView(self.annoViewList[-1])       
#         self.annoViewLabel += [QLabel(self)]
#         self.annoViewLabel[-1].setText("{0}: {1}".format(\
#                                             self.annotations[1]["annot"],
#                                             self.annotations[1]["behav"]))
#         self.annoViewLabel[-1].move(xPos + width + 10, yPos)         
#         self.annoViewLabel[-1].adjustSize()       
#         yPos += height + 5 
#         
#         self.annoViewList += [AnnoView(self, vialNo=self.selectedVial, 
#                                        annotator=[self.annotations[2]["annot"]], 
#                                        behaviourName=[self.annotations[2]["behav"]], 
#                                        color = self.annotations[2]["color"], 
#                                        geo=QRect(xPos, yPos, width, height))]
# #         self.annoViewList[-1].setGeometry(QRect(xPos, yPos, width, height))
#         self.annoViewList[-1].show()
#         self.vh.addAnnoView(self.annoViewList[-1])     
#         self.annoViewLabel += [QLabel(self)]
#         self.annoViewLabel[-1].setText("{0}: {1}".format(\
#                                             self.annotations[2]["annot"],
#                                             self.annotations[2]["behav"]))
#         self.annoViewLabel[-1].move(xPos + width + 10, yPos)          
#         self.annoViewLabel[-1].adjustSize()    
#                
#         yPos += height + 5  
        
        self.createAnnoView(xPos, yPos, width, height, 0)
        yPos += height + 5  
        self.createAnnoView(xPos, yPos, width, height, 1)
        yPos += height + 5  
        self.createAnnoView(xPos, yPos, width, height, 2)
        yPos += height + 5  
        self.createAnnoView(xPos, yPos, width, height, 3)
        yPos += height + 5  
        
        for aV in self.annoViewList:
            cfg.log.debug("av: {aV}".format(aV=aV))
            
            
        #~ width = 
        self.ui.progBar.setVisible(False)        
        self.ui.progBar.move(xPos + 220, yPos + 3)
            
            
    def createPrevFrames(self, xPos, yPos):
        size = self.prevSize
        
        self.noPrevFrames = 7
        self.prevFrameLbls = []
        self.prevConnectHooks = []
        
        for i in range(self.noPrevFrames):
            self.prevFrameLbls += [QLabel(self)]
            self.prevFrameLbls[-1].setGeometry(QRect(xPos, yPos, size, size))
            
            self.prevConnectHooks += [[QPoint(xPos + size / 2, yPos + size), 
                                      QPoint(xPos + size / 2, yPos + size + 2)]]
            
            if i == (self.noPrevFrames - 1) / 2:
                self.prevFrameLbls[-1].setLineWidth(3)
                self.prevFrameLbls[-1].setFrameShape(QFrame.Box)
            xPos += size + 5
        
    
        
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self) 
        painter.resetTransform() 
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(100,100,100))
        pen.setWidth(0.2)
        
        painter.setPen(pen)
        
        avHooks = self.annoViewList[0].prevConnectHooks
        midAVHook = len(avHooks) / 2
        startAVHook = midAVHook - (len(self.prevConnectHooks) - 1) / 2 + \
                        self.tempIncrement
                                    
        for i in range(0,len(self.prevConnectHooks),2):            
            aVi = startAVHook + i
            try:
                painter.drawLine(self.prevConnectHooks[i][0], self.prevConnectHooks[i][1])   
                painter.drawLine(self.prevConnectHooks[i][1], avHooks[aVi][1])            
                
                painter.drawLine(avHooks[aVi][0], avHooks[aVi][1])  
            except:
                pass
        painter.end()
        
        
    @cfg.logClassFunctionInfo
    def setCropCenter(self, x, y, width=None, increment=None):        
        if width != None and increment != None:
            raise ValueError("width and increment cannot be both specified")
        cfg.log.debug("width: {0}, increment {1}".format(width, increment))
        if width == None: 
            width = 64
            
        if increment != None:
            width += (increment / 10) 
        if x == None:        
            self.prevXCrop = slice(None, None)
        else:
            self.prevXCrop = slice(x-width/2, x+width/2)
            
        if y == None:
            self.prevYCrop = slice(None, None)
        else:
            self.prevYCrop = slice(y-width/2, y+width/2)
            
        if x == None or y == None:
            self.cropRect.setPos(-1000, -1000)            
            return
            
        x -= width / 2 
        y -= width / 2
            
        self.cropRect.setRect(0,0, width, width)
        self.cropRect.setPos(x, y)
        r = self.cropRect.rect()
            
        cfg.log.debug("after width: {0}, increment {1}, rect {2}".format(width, increment, r))
        
        
            
        
        
    @cfg.logClassFunction
    def updateFrameList(self, intList):
        self.frameList = MyListModel(intList, self) 
        self.ui.lv_frames.setModel(self.frameList)
        
    @cfg.logClassFunction
    def updateJumpList(self, intList):
        self.jmpIdx = intList
        
        strList = [str(x) for x in intList]
        self.jumpList = MyListModel(strList, self) 
        self.ui.lv_jmp.setModel(self.jumpList)
        
    @cfg.logClassFunction
    def updateVial(self, vE, lbl, p):    
        frame = vE.vs.next()
        
        img = frame.ndarray()# * 255
        
        qi = np2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lblOrigin = self.ui.label.pos()
        
        newX = lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
                    
        lbl.move(newX,newY)
        
        lbl.setScaledContents(True)
        lbl.setPixmap(px)
        
        lbl.update()
        
        return img
        
    @cfg.logClassFunction
    def loadImageIntoLabel(self, lbl, img):
        if img is not None:
            qi = array2qimage(img)
#             a = np.ones(img.shape, dtype=np.float64) * 254
#               
#             s1 = a.strides
#             s2 = img.astype(np.uint32).flatten().strides
#             
#             cfg.log.info("strides {0} {1}".format(s1, s2))
# 
#             qi = np2qimage(img)#.astype(np.float64, order='F', copy=True))
            cfg.log.debug("copy image to pixmap")
#             1/0
#             qi = QImage(500,350, QImage.Format_ARGB32)
            px = QPixmap().fromImage(qi)        
            #lbl.setScaledContents(True)
            cfg.log.debug("set pixmap")
            lbl.setPixmap(px)
        
    @cfg.logClassFunction
    def updateLabel(self, lbl, p, img):
        self.loadImageIntoLabel(lbl, img)
#         if img is not None:
# #             qi = array2qimage(img)
#             qi = np2qimage(img)
#             pixmap = QPixmap()
#             px = QPixmap.fromImage(qi)        
#             #lbl.setScaledContents(True)
#             lbl.setPixmap(px)
#         else:
#             pixmap = QPixmap()
#             lbl.setPixmap(pixmap)
            
                
        newX = p[0] - 32#lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        if self.selectedVial is None:
            newY = self.vialRoi[0][1] - p[1] - 32
        else:
            newY = self.vialRoi[self.selectedVial][1] - p[1] - 32 #lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
        
        
        lbl.setPos(newX,newY)
        #lbl.setStyleSheet("border: 1px dotted rgba(255, 0, 0, 75%);");
        #lbl.raise_()
        #lbl.update()
        
    @cfg.logClassFunction
    def updateOriginalLabel(self, lbl, data):
        img = data[0]
        qi = array2qimage(scim.imresize(img[self.prevYCrop, self.prevXCrop], 
                                        (self.prevSize,self.prevSize)))

        cfg.log.debug("converting img to QImage")
#         qi = np2qimage(img)
        
        def millis():
            import datetime as dt
            dt = dt.datetime.now() - dt.datetime(1970, 1,1)
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            return ms
        
        from scipy.misc import imsave
        
#         imsave('/tmp/ol/' + str(millis()) + '.png', img)
        
        cfg.log.debug("creating pixmap")
        pixmap = QPixmap()
        
        cfg.log.debug("copy image to pixmap")
        px = QPixmap.fromImage(qi)
                
        cfg.log.debug("configure label")
        lbl.setScaledContents(False)
        lbl.setPixmap(px)
                
        cfg.log.debug("update label")
        lbl.update()
        
        
    @cfg.logClassFunctionInfo
    def updateMainLabel(self, lbl, data):
        img = data[0][0]
        anno = data[1]
        h = img.shape[0]
        w = img.shape[1]
        if self.sceneRect != QRectF(0, 0, w,h):
            cfg.log.info("changing background")
            self.videoView.setGeometry(QRect(380, 10, w, h))#1920/2, 1080/2))
            self.videoScene.setSceneRect(QRectF(0, 0, w,h))            
            self.videoScene.setBackgroundBrush(QBrush(Qt.black))
            lbl.setPos(0,0)
            self.sceneRect = QRectF(0, 0, w,h)
                    
        self.loadImageIntoLabel(lbl, img)
        
        # place annotation roi
        self.tmpAnnotation.setFrameList([[anno]])
        
        rois = []
        for i in range(len(self.annotations)):
            filt = AnnotationFilter(None, [self.annotations[i]["annot"]],
                                            [self.annotations[i]["behav"]])
            tmpAnno  = self.tmpAnnotation.filterFrameList(filt)      
            
            if tmpAnno.frameList[0] == [None]:
                continue
                         
            bb = getPropertyFromFrameAnno(tmpAnno.frameList[0], "boundingBox")
            
            for b in bb:
                rois += [[b, self.annotations[i]["color"]]]
                
        self.positionAnnotationRoi(rois)
        
        
    @cfg.logClassFunction
    def positionAnnotationRoi(self, rois):
        while len(self.annotationRoiLabels) < len(rois):
            rect = QRectF(0, 0, 64, 64)
            self.annotationRoiLabels += [self.videoScene.addRect(rect)]
            
        usedRoi = 0
        
        cfg.log.info("Rois: {0}".format(rois))
        for i in range(len(rois)):        
            x1, y1, x2, y2 = rois[i][0]
            color = rois[i][1]
            
            width = x2 - x1
            height = y2 - y1
            
            cfg.log.info("setting rect to: {0} {1} {2} {3}".format(x1/2, 
                                                                   y1/2,
                                                                   width /2,
                                                                   height / 2))
            self.annotationRoiLabels[i].setRect(0,0, width / 2, height / 2)
            self.annotationRoiLabels[i].setPos(x1/2, y1/2)
            self.annotationRoiLabels[i].setPen(QPen(color))
#             self.annotationRoiLabels[i].setBrush(QPen(color))
#             self.annotationRoiLabels[i].setVisible(True)
             
            cfg.log.info("set rect to: {0}".format(self.annotationRoiLabels[i].rect()))
            usedRoi = i + 1
            
            
        # move unused rects out of sight
        for k in range(usedRoi, len(self.annotationRoiLabels)):
            self.annotationRoiLabels[k].setRect(0,0, 0, 0)
            self.annotationRoiLabels[k].setPos(-10, -10)
            
        
    
    @cfg.logClassFunction
    def showTempFrame(self, increment):
        self.tempIncrement = increment
        self.showNextFrame(self.tempIncrement, checkBuffer=False)
        self.update()
        
        
    @cfg.logClassFunction
    def resetTempFrame(self):
        self.showNextFrame(-self.tempIncrement, checkBuffer=False)
        self.tempIncrement = 0
        self.update()
    
    @cfg.logClassFunction
    def showNextFrame(self, increment=None, checkBuffer=True):
        #~ logGUI.debug(json.dumps({"increment":increment, 
                                 #~ "checkBuffer":checkBuffer}))
                
        
        
        if increment is None:
            increment = self.increment
            
        self.rewindIncrement()
        
        #if self.frames != []:
        #    self.frames.pop(0)
        self.frames = []    
        
        if self.selectedVial is None:
            sv = 0            
        else:
            sv = self.selectedVial
        
        offset = 5  
        
        cfg.log.debug("increment: {0}, checkBuffer: {1}".format(increment, checkBuffer))
        
        if increment > 0:
            self.frames += [self.vh.getNextFrame(increment, doBufferCheck=False, 
                                                 unbuffered=True)]
        elif increment < 0:
            self.frames += [self.vh.getPrevFrame(-increment, doBufferCheck=False,
                                                 unbuffered=True)]
        else:
            self.frames += [self.vh.getCurrentFrame()]
            increment = 8
            offset = (self.trajNo / 2) 
        
        frame = self.frames[0]
        if self.videoOnly:
            self.updateMainLabel(self.lbl_v0, frame[1][sv])
        else:
            self.updateLabel(self.lbl_v0, frame[0][sv], frame[1][sv][0])
        
        
        # showing trajectory #
#         self.frames = []
#         for i in range(self.trajNo):
#             self.frames += [self.vh.getTempFrame(increment * (i - offset))] 
#         
#         for i in range(len(self.frames)-1, -1, -1):
#             frame = self.frames[i]
#             self.updateLabel(self.trajLabels[i][0], frame[0][sv], None)


        # showing previews #
#         offset = (len(self.prevFrameLbls) - 1) / 2
#         self.prevFrames = []
#                 
#         for i in range(len(self.prevFrameLbls)):
#             self.prevFrames += [self.vh.getTempFrame(i - offset)]
#             self.updateOriginalLabel(self.prevFrameLbls[i], self.prevFrames[i][1][sv][0])
#             
        
        self.vh.updateAnnotationProperties(self.getMetadata())

        
    @cfg.logClassFunction
    def jumpToFrame(self, vE, lbl, p, frameNo):    
        
        frame = vE.vs.get_frame_no(frameNo)
        
        img = frame.ndarray() #* 255
        
        qi = np2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lblOrigin = self.ui.label.pos()
        
        newX = lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
                    
        lbl.move(newX,newY)
        
        lbl.setScaledContents(True)
        lbl.setPixmap(px)
        
        lbl.update()
        
        return img
        
    @cfg.logClassFunction
    def setBackground(self, path=None):
        
        if path:        
            a = plt.imread(path) * 255
            
            # crop and rotate background image to show only one vial
            rng = slice(*self.vialRoi[self.selectedVial])
            a = np.rot90(a[:, rng]).astype(np.uint32)
            
            h = a.shape[0]
            w = a.shape[1]
            
    #         a *= 255
            # grey conversion
            b = a[:,:,0] * 0.2126 + a[:,:,1] * 0.7152 + a[:,:,2] * 0.0722
            a[:,:,0] = b
            a[:,:,1] = b
            a[:,:,2] = b
            
            im = np2qimage(a).convertToFormat(QImage.Format_RGB32, Qt.MonoOnly)
            
            pixmap = QPixmap()
            px = QPixmap.fromImage(im)
            
        else:
            h = 0
            w = 0            
            
        #~ 
        #~ self.ui.label.setScaledContents(True)
        #~ self.ui.label.setPixmap(px)
        
        self.sceneRect = QRectF(0, 0, w,h)
        
        self.videoView = QGraphicsView(self)        
        self.videoView.setFrameStyle(QFrame.NoFrame)
#         self.videoView.setGeometry(QRect(10, 10, w, h))#1920/2, 1080/2))
#         self.videoView.setGeometry(QRect(150, 10, w, h))#1920/2, 1080/2))
        self.videoScene = QGraphicsScene(self)
        self.videoScene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.videoScene.setSceneRect(self.sceneRect)#1920, 1080))
        self.videoScene.setBackgroundBrush(QBrush(Qt.black))
        
        self.videoView.setScene(self.videoScene)
        #self.videoView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.videoView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            
        if path:
            self.bgImg = QGraphicsPixmapItem(px)
        else:
            self.bgImg = QGraphicsPixmapItem()
              
              
        self.videoScene.addItem(self.bgImg)   
        self.bgImg.setPos(0,0)     
        
        
        self.lbl_v0 = QGraphicsPixmapItem()
        self.lbl_v1 = QGraphicsPixmapItem()
        self.lbl_v2 = QGraphicsPixmapItem()
        self.lbl_v3 = QGraphicsPixmapItem()   
         
        self.videoScene.addItem(self.lbl_v0)   
        self.videoScene.addItem(self.lbl_v1)   
        self.videoScene.addItem(self.lbl_v2)   
        self.videoScene.addItem(self.lbl_v3)   
        
        fmt = QGLFormat()
        fmt.setAlpha(True)
        fmt.setOverlay(True)
        fmt.setDoubleBuffer(True);                 
        fmt.setDirectRendering(True);
         
        glw = QGLWidget(fmt)
#         glw.setMouseTracking(True)
        
        self.videoView.setViewport(glw)
        self.videoView.viewport().setCursor(Qt.BlankCursor)
#         self.videoView.setGeometry(QRect(250, 10, w, h))#1920/2, 1080/2))
        self.videoView.show()
        self.videoView.fitInView(self.bgImg, Qt.KeepAspectRatio)
        
#         self.videoView.installEventFilter(self.mouseEventFilter)
        self.videoView.setMouseTracking(True)
#         self.lbl_v0.setAcceptHoverEvents(True)
#         self.videoScene.setAcceptHoverEvents(True)
        self.videoScene.installEventFilter(self.mouseEventFilter)
        
        
        
        geo = QRectF(0, 0, 64, 64)
        penCol = QColor()
        penCol.setHsv(50, 255, 255, 255)
        self.cropRect = self.videoScene.addRect(geo, QPen(penCol))
#         self.videoView.setCursor(QCursor(Qt.CrossCursor))
        
        
        
    def startVideo(self):
        self.play = True
        #self.setBackground("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        
        cfg.log.debug("start Video")
        self.showNextFrame(0)
        self.vh.loadProgressive = True
        
        self.stop = False
        skipCnt = 0 # counts how often process events were skipped
        
        
        logGUI.info('"--------- start mainloop ------------"')
         
        while not self.stop:
            #cfg.log.info("begin   --------------------------------------- main loop")
            self.vh.loadProgressive = True
             
            dieTime = QTime.currentTime().addMSecs(33)
                         
            if self.play:            
                self.showNextFrame(self.increment)
                 
                if self.increment == 0:
                    self.play = False
                    
            if not(QTime.currentTime() < dieTime):
                cfg.log.warning("no realtime display!!! " + 
                                cfg.Back.BLUE + 
                                "mainloop overflow before processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QTime.currentTime())))
                
            elif(QTime.currentTime() < dieTime.addMSecs(15)):
                frameNo = self.vh.getCurrentFrameNo()
                self.ui.lbl_v1.setText("no: {0}".format(frameNo))
#                 self.ui.lv_frames.setCurrentIndex(self.frameList.index(frameNo,0))
             
#             cfg.log.debug("---------------------------------------- while loop() - begin")

            if not (QTime.currentTime() < dieTime):                
                skipCnt += 1
            else:
                skipCnt = 0
                
            while(QTime.currentTime() < dieTime) or (skipCnt > 10):
                skipCnt = 0
#                 cfg.log.debug("processEvents() - begin")
                QApplication.processEvents(QEventLoop.AllEvents, QTime.currentTime().msecsTo(dieTime))
#                 cfg.log.debug("processEvents() - end")
                 
            if not(QTime.currentTime() < (dieTime.addMSecs(1))):
                cfg.log.warning("no realtime display!!! " + 
                                cfg.Back.YELLOW + 
                                "mainloop overflow after processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QTime.currentTime())))
#             cfg.log.debug("---------------------------------------  while loop() - end")
             
#             cfg.log.debug("end   ------------------------------------------ main loop")
         
        self.vh.loadProgressive = False
        logGUI.info('"--------- stopped mainloop ------------"')
        
    @cfg.logClassFunction
    def providePosList(self, path, ending=None):
        if not ending:
            ending = '.pos.npy'
        
        fileList  = []
        posList = []
        cfg.log.debug("scaning files...")
        for root,  dirs,  files in os.walk(path):
            for f in files:
                if f.endswith(ending):
                    path = root + '/' + f
                    fileList.append(path)
                    
        self.fileList = sorted(fileList)
        cfg.log.debug("scaning files done")
        return self.fileList
        
        
    @cfg.logClassFunction
    def close(self):
        self.stop = True
        self.exit()  
            
    def exit(self):
        print "-----------------exit---------------"
        self.stopVideo()
        self.vh.aboutToQuit()
        
    @cfg.logClassFunction
    def closeEvent(self, event):
        self.close()      
        event.accept()   
        self.quit.emit()
        
    def stopVideo(self):
        cfg.log.debug("stop video")
        self.timer.stop()
        self.timerID = None
        self.stop = True
        self.vh.loadProgressive = False
        
    @cfg.logClassFunction
    def generatePatchVideoPath(self, posPath, vialNo):
        """
        strips pos path off its postfix and appends it with the vial + video
        format postfix
        """
        return posPath.split('.pos')[0] + '.v{0}.{1}'.format(vialNo, 
                                                            self.videoFormat)
                                                            
    @cfg.logClassFunction
    def setVideo(self, idx):
        self.ui.lv_paths.setCurrentIndex(self.lm.index(idx,0))
        self.ui.sldr_paths.setSliderPosition(idx)
#         for i in range(len(self.vEs)):
#             f = self.generatePatchVideoPath(self.fileList[idx], i)
#             self.vEs[i].setVideoStream(f, info=False, frameMode='RGB')
            
        self.pos = self.posList[idx]
        
        if self.filterList != []:
            lst = self.filterList[0][idx]
            for i in range(1, len(self.filterList)):
                lst = np.logical_or(lst, [self.filterList[i][idx]])
                
            lst = np.arange(len(lst.flatten()))[lst.flatten()]
            self.updateJumpList(list(lst))
        
    @cfg.logClassFunction
    def setFrame(self, idx):
        self.frameIdx = idx
        #~ if not self.play:
            #~ i = self.frameIdx
            #~ img = self.jumpToFrame(self.vEs[0], self.ui.lbl_v0, self.pos[i][0],i)
            #~ img = self.jumpToFrame(self.vEs[1], self.ui.lbl_v1, self.pos[i][1],i)
            #~ img = self.jumpToFrame(self.vEs[2], self.ui.lbl_v2, self.pos[i][2],i)
            #~ img = self.jumpToFrame(self.vEs[3], self.ui.lbl_v3, self.pos[i][3],i)
        self.vh.setFrameIdx(idx)
        self.showNextFrame(1)
        self.ui.lv_frames.setCurrentIndex(self.frameList.index(idx,0))
            

    @cfg.logClassFunction
    def selectVideo(self, idx):
        self.idx = idx
        #self.setVideo(self.idx)
        self.vh.getFrame(sorted(self.fileList)[idx], 0)
        self.ui.lbl_v0.setText("current file: {0}".format( \
                                                    sorted(self.fileList)[idx]))
        
#     @cfg.logClassFunction
    def selectVideoLV(self, mdl):
        self.idx = mdl.row()   
        self.selectVideo(self.idx)
        
    def jump2selectedVideo(self):
        self.selectVideoLV(self.ui.lv_paths.selectionModel().currentIndex())
        
#     @cfg.logClassFunction
    def selectFrame(self, mdl):
        idx = mdl.row()       
        cfg.log.debug("select frame {0}".format(idx))
        self.setFrame(idx)
        
#     @cfg.logClassFunction
    def selectFrameJump(self, mdl):
        idx = mdl.row()       
        cfg.log.debug("select frame idx {0}. {1}".format( idx, self.jmpIdx[idx]))
        self.setFrame(self.jmpIdx[idx])
        
    @cfg.logClassFunction
    def compDistances(self):
        posList, idx = self.vh.getCurrentPosList()
        cfg.log.debug("start computing the distances...")
        self.dists = computeDistancesFromPosList(posList, self.fileList)
        cfg.log.debug("finished computing distances")
        
        cfg.log.debug("start computing the jumps...")
        self.filterList = filterJumps(posList, self.dists, 25)
        cfg.log.debug("finished computing jumps")
        
        #idx = 0
        lst = self.filterList[0][idx]
        for i in range(1, len(self.filterList)):
            lst = np.logical_or(lst, [self.filterList[i][idx]])
            
        lst = np.arange(len(lst.flatten()))[lst.flatten()]
        self.updateJumpList(list(lst))
        
    @cfg.logClassFunction
    def loadNewVideo(self):
        self.videoList[self.fileList[0]] = VideoLoader(self.fileList[0])
        #self.prefetchVideo(self.fileList[0])
        
    @cfg.logClassFunctionInfo
    def showTrajectories(self, state):
        self.showTraject = bool(state)        
        
        if self.showTraject:
            self.trajNo = 50
        else:
            self.trajNo = 0
            
        if self.trajLabels != []:
            for i in range(len(self.trajLabels)):
                for k in range(len(self.trajLabels[i])):
                    #self.trajLabels[i].pop().setVisible(False)
                    self.videoScene.removeItem(self.trajLabels[i].pop())
                    
        self.ui.label.update()
        self.trajLabels = []
        for i in range(self.trajNo):
            lbl = []
            for k in range(1):
                #l = QLabel(self)
                geo = QRectF(0, 0, 64, 64)
                penCol = QColor()
                penCol.setHsv(i / 50.0 * 255, 255, 150, 50)
                lbl += [self.videoScene.addRect(geo, QPen(penCol))]
                #l.setLineWidth(1)
                #l.setStyleSheet("border: 1px solid hsva({0}, 200, 150, 15%);".format(i / 50.0 * 255));
                #l.show()
                #lbl += [l]
            self.trajLabels += [lbl]
    
    @cfg.logClassFunction
    @Slot(list)
    def addVideo(self, videoList):
        cfg.log.debug("slot")
        self.videoList += videoList
        
        cfg.log.debug("{0}".format(self.videoList))
        
    @cfg.logClassFunction
    @Slot(str)
    def changeVideo(self, filePath):
        cfg.log.debug("Change video to {0}".format(filePath))
        
        self.ui.lbl_v0.setText("current file: {0}".format(filePath))
#         posInLst = self.fileList.index(filePath)
                
#         self.ui.lv_paths.setCurrentIndex(self.lm.index(posInLst,0))
        #self.updateFrameList(range(self.vh.getCurrentVideoLength()))
        
        cfg.log.debug("end")
        
    @cfg.logClassFunction
    def saveAll(self):
        logGUI.info('""')
        self.vh.saveAll()
        
#     @cfg.logClassFunction
#     def prefetchVideo(self, posPath):        
#         self.vl = VideoLoader()
#         self.vl.loadedVideos.connect(self.addVideo)
#         self.vl.loadVideos(posPath)
        
    def testFunction(self):
        cfg.log.debug("testFunction")
#         self.vh.saveAll()
        #self.showNextFrame(0)
        #self.vh.loadProgressive = True
        self.increment = 40
        
    def initRewind(self):        
        self.rewinding = True
        ## set filterObj to normal playback
        self.eventFilter.swapToConstantSpeed(1)
        ## rewind
        self.rewindCnt = 0
        self.increment = 1
        self.ui.progBar.setMaximum(self.rewindStepSize)
        self.ui.progBar.setValue(0)
        self.ui.progBar.setVisible(True)        
        self.showNextFrame(-self.rewindStepSize)
        self.startVideo()    
        
    def stopRewind(self):        
        self.rewinding = False               
        ## set filterObj to normal playback
        self.eventFilter.swapFromConstantSpeed()
        self.ui.progBar.setVisible(False)
    
    def rewindIncrement(self):        
        if self.rewinding:
            if self.rewindCnt >= self.rewindStepSize: 
                self.stopRewind()
            else:                
                self.rewindCnt += 1
                self.ui.progBar.setValue(self.rewindCnt)
                
        
    def alterAnnotation(self, annotator="peter", behaviour="just testing", 
                        confidence=1, oneClickAnnotation=False):
        if self.addingAnnotations:
            self.addAnno(annotator, behaviour, confidence, oneClickAnnotation)
        else:
            self.eraseAnno(annotator, behaviour)           
            
    def getMetadata(self):        
        if self.prevXCrop.start is not None:
            xStart = self.prevXCrop.start * 2
        else:
            xStart= None
            
        if self.prevYCrop.start is not None:
            yStart = self.prevYCrop.start * 2
        else:
            yStart = None
            
        if self.prevXCrop.stop is not None:
            xStop = self.prevXCrop.stop * 2
        else:
            xStop = None
        
        if self.prevYCrop.stop is not None:
            yStop = self.prevYCrop.stop * 2
        else:
            yStop = None
            
        metadata =           {"confidence": self.confidence,
                              "boundingBox":[xStart, 
                                             yStart,
                                             xStop,
                                             yStop]}
        
        return metadata
        
#     @cfg.logClassFunction
    def addAnno(self, annotator="peter", behaviour="just testing", 
                confidence=1, oneClickAnnotation=False):        
        logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour,
                                "confidence": confidence}))
        
        if not self.annoIsOpen:
            self.confidence = confidence            
#             self.metadata = []
#             self.addMetadata()
                                
        if self.rewindOnClick:
            if not self.rewinding:
                self.initRewind()
                
                ##
            else:
                self.vh.addAnnotation(self.selectedVial, annotator, 
                                      behaviour, metadata=self.getMetadata())
                
                if oneClickAnnotation:                
                    self.vh.addAnnotation(self.selectedVial, annotator, 
                                      behaviour, metadata=self.getMetadata())
                
                self.stopRewind()
                    
        
        else:    
            self.vh.addAnnotation(self.selectedVial, annotator, 
                                  behaviour, metadata=self.getMetadata())
                
            if oneClickAnnotation:                
                self.vh.addAnnotation(self.selectedVial, annotator, 
                                  behaviour, metadata=self.getMetadata())
                
        self.annoIsOpen = not self.annoIsOpen
#     @cfg.logClassFunction

        
#     @cfg.logClassFunction
    def eraseAnno(self, annotator="peter", behaviour="just testing"):      
        logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour}))
        self.vh.eraseAnnotation(self.selectedVial, annotator, behaviour)
        
#     @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        cfg.log.info("escape annotation")    
        logGUI.info('"------escape annotation--------"')
        self.vh.escapeAnnotationAlteration()
        
        
        
    
    def aboutToQuit(self):
        self.exit()
        
        
class AnnoViewManager(QObject):
    @cfg.logClassFunction
    def __init__(self, parent, vialNo=None, behaviourName=None, annotator=None,
                color=None):        
        self.worker = Worker()
        
        self.AVs = []
        
        for i in range(2):
            self.AVs += [{"av": AnnoView(parent, vialNo=None, 
                                         behaviourName=None,
                                         annotator=None, color=None),
                          "tasks": []}]
            
            
            
           
    @cfg.logClassFunction
    def addAnnotation(self):
        cfg.warning("not coded")
        
    @cfg.logClassFunction
    def removeAnnotation(self):
        cfg.warning("not coded")
            
    @cfg.logClassFunction
    def setPosition(self):
        cfg.warning("not coded")
            
    @cfg.logClassFunction
    def addAnno(self):
        cfg.warning("not coded")
            
    @cfg.logClassFunction
    def escapeAnno(self):
        cfg.warning("not coded")         
        
    
    
class AnnoViewItem(QGraphicsRectItem):
    def __init__(self, annoView, rect):
        super(AnnoViewItem, self).__init__(None)
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.annoView = annoView

    def hoverEnterEvent(self, event):
        pen = QPen(Qt.red)
        self.setPen(pen)
        self.annoView.centerAt(self)
        QGraphicsRectItem.hoverEnterEvent(self, event)
    
    def hoverLeaveEvent(self, event):
        pen = QPen(QColor(0,0,0,0))
        self.setPen(pen)
        self.annoView.centerAt(None)
        QGraphicsRectItem.hoverLeaveEvent(self, event)
        
    def mousePressEvent(self, event):
        self.annoView.alterAnnotation(self)
        QGraphicsRectItem.mousePressEvent(self, event)

    
    
class AnnoView(QWidget):
    
    @cfg.logClassFunction
    def __init__(self, parent, vialNo=None, behaviourName=None, annotator=None,
                color=None, geo=None):
        super(AnnoView, self).__init__(parent)
        #QGraphicsView.__init__(parent)
        
        # draw center markers of graphics view
        
        if geo is not None:
            self.setGeometry(geo)
            
        self.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        self.gV = QGraphicsView(self)
        self.gV.setGeometry(QRect(-5, 0, geo.width(), geo.height()))
        self.gV.setFrameStyle(QFrame.NoFrame)
        self.gV.setStyleSheet("* {margin: 0px; border-width: 0px; padding: 0px}")
        
        self.cMarker1 = QLabel(parent)
        self.cMarker1.setGeometry(QRect(geo.x() + geo.width() / 2, 
                                       geo.y() -15, 1, geo.height() + 30))
        self.cMarker1.setFrameStyle(QFrame.VLine)
        self.cMarker1.raise_()
        
        self.prevConnectHooks = []
        parPos = self.mapToParent(QPoint(0,0))
        for i in range(100):
            self.prevConnectHooks += [[QPoint(parPos.x(), parPos.y()), 
                                       QPoint(parPos.x(), parPos.y() - 3)]]
            parPos.setX(parPos.x() + 10)
            
        
#         self.cMarker2 = QLabel(parent)
#         self.cMarker2.setGeometry(QRect(geo.x() + geo.width() / 2 + 6, 
#                                        geo.y() -15, 1, geo.height() + 30))
#         self.cMarker2.setFrameShape(QFrame.Box)
#         self.cMarker.setFrameStyle(QFrame.Plain)
#         self.cMarker.setLineWidth(1)
#         self.cMarker.setObjectName(fromUtf8("cMarker"))
#         self.ui.addLine(linePosX, yPos -5, linePosX, yPos + height + 5,  QPen(QColor(100,100,100)))
        
        
        # initialization of parameters
        self.annotationDict = dict()
        self.color = QColor(0,255,0,150)
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
        
#         geo = self.geometry()
#         geo.setHeight(self.boxHeight + 6)
#         self.setGeometry(geo)
        
        # setting values
        self.scene = QGraphicsScene(self.gV)
#         self.scene.setSceneRect(QRectF(-50000, -20, 100000, 20))
        self.gV.setScene(self.scene)
        
        self.gV.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gV.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.vialNo = vialNo
        self.behaviourName = behaviourName
        self.annotator = annotator
        
#         self.gV.setViewport(QGLWidget(parent))
        
        if color == None:
            self.color = QColor(0,255,0,150)
        else:
            self.color = color
            
        colI = QColor(0,0,0,0)
                    
        self.penA = QPen(colI)
        self.brushA = QBrush(self.color)    
              
        self.penI = QPen(colI)
        self.brushI = QBrush(colI)
        
        self.addList = []  #{key: (string), range: slice}
        self.removeList = []  #{key: (string), range: slice}
        
        self.frameAmount = 101 ## odd number please
        
        self.confidenceList = []
        self.tempRng = dict()
        self.lines = []
        self.frames = []
        self.annoViewRects = []
        
        
        for i in range(self.frameAmount):
            self.lines += [(self.scene.addLine(i, 0, i, self.boxHeight,  QPen(QColor(100,100,100))))]
            
        for i in range(self.frameAmount):
            self.frames += [AnnoViewItem(self, QRectF(i, 0, 1, self.boxHeight))]#self, QRectF(i, 0, 1, self.boxHeight))]                
            self.scene.addItem(self.frames[-1])
        
        center = self.frameAmount / 2 + 1
        self.gV.centerOn(self.frames[center])
        self.setZoom(0)
#         self.centerOn(self.frames[0])
            
    def centerAt(self, avItem):
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                mid = (self.frameAmount + 1) / 2                
                [key, idx, conf] = self.confidenceList[i]
                
                logGUI.debug(json.dumps({"selectedItem":True,
                                         "key":key, 
                                         "idx":idx,
                                         "annotator":self.annotator,
                                         "behaviour":self.behaviourName}))
                
                self.parent().showTempFrame(i-mid)
                self.setPosition(key, idx, tempPositionOnly=True)
                
        if avItem is None:                
            logGUI.debug(json.dumps({"selectedItem":False,
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
#                 self.addAnno(self.confidenceList[i].key, 
#                                  self.confidenceList[i].idx)
                
        if avItem is None:
            self.parent().resetTempFrame()
        
    @cfg.logClassFunction
    def addAnnotation(self, annotation, key, addAllAtOnce=True):
        """
        adds an annotation to a scene
        """
        if self.vialNo is None:
            filt = AnnotationFilter([0], self.annotator, 
                                                        self.behaviourName)
        else:
            filt = AnnotationFilter([self.vialNo], self.annotator, 
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
#         if self.zoom < 4:
#             for line in self.lines:
#                 line.setVisible(False)
#         else:
        for line in self.lines:
            line.setVisible(True)
        
        self.gV.setTransform(QTransform().scale(scale, 1))
        
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
                    conf = getPropertyFromFrameAnno(
                                self.annotationDict[curKey].frameList[curIdx],
                                "confidence")
                                  
            self.confidenceList += [KeyIdxPair(curKey, curIdx, conf)]            
            curIdx += 1     

    @cfg.logClassFunction
    def updateGraphicView(self):
        for i in range(len(self.confidenceList)):   
            conf = self.confidenceList[i].conf
#             if kip == None:
#                 conf = None
#             elif kip == 1:
#                 conf = 1
#             else:
#                 conf = self.annotationDict[kip.key].frameList[kip.idx]
#             cfg.log.warning("{0}".format(conf))
            if [True for c in conf if c != None]:
                self.frames[i].setBrush(self.brushA)
                self.frames[i].setPen(self.penA)
            else:              
                self.frames[i].setBrush(self.brushI)
                self.frames[i].setPen(self.penI)
                
            self.frames[i].update()
        
    @cfg.logClassFunction
    def addAnno(self, key=None, idx=None, metadata=None):
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
        if metadata is None:
            metadata = {"confidence":1}
            
#         if self.erasingAnno:
#             self.eraseAnno(key, idx)
#             return
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
# 
#         if self.erasingAnno:                         
#             tempEnd = bsc.FramePosition(self.annotationDict, self.selKey, self.idx)            
#             self.tempRng = bsc.generateRangeValuesFromKeys(self.tempStart, tempEnd)      
                          
        
class BaseThread(QThread):
    @cfg.logClassFunction
    def __init__(self, name):
        super(BaseThread, self).__init__()
        self.setObjectName(name)
        self.exiting = False

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
        
    def run(self):
#         print "RUN", QThread.currentThread().objectName(), QApplication.instance().thread().objectName()
        self.exec_()
        
    @cfg.logClassFunction
    def delay(self, secs):
        dieTime = QTime.currentTime().addSecs(secs)
        while(QTime.currentTime() < dieTime ):
            self.processEvents(QEventLoop.AllEvents, 100)
        
from IPython.parallel import Client, dependent
# Subclassing QObject and using moveToThread
# http://labs.qt.nokia.com/2007/07/05/qthreads-no-longer-abstract/
class VideoLoader(QObject):        
    loadedVideos = Signal(list) 
    loadedAnnotation = Signal(list)
    eof = Signal(int)
    finished = Signal()   
    startLoading = Signal()

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
    
    @cfg.logClassFunction
    def __init__(self, posPath, idxSlice, videoHandler, selectedVials=[1], 
                 thread=None, eofCallback=None):
        super(VideoLoader, self).__init__(None)        
        self.init(posPath, idxSlice, videoHandler, selectedVials, thread)
        
    def init(self, posPath, idxSlice, videoHandler, selectedVials=[1], 
             thread=None):
        self.loading = False
        
        self.videoLength = -1
        self.frameList = []
        
#         self.annotation = None # annotation object
        
        self.posPath = copy.copy(posPath)      
        
        self.selectedVials = selectedVials
        
        self.videoHandler = videoHandler
        
        self.thread = thread
        
        self.videoEnding = '.mp4'
        
        self.imTransform = lambda x: x
        
        self.endOfFile = [] 
        self.idxSlice

    def maxOfSelectedVials(self):
        return maxOfSelectedVials(self.selectedVials)

    @Slot()
    def loadVideos(self):
        self.exiting = False
        self.loading = True
        
        #####################################################################   TODO: fix properly!!
        # quick-fix of file extension dilemma
#         self.posPath = self.posPath.split(self.videoEnding)[0] + '.pos.npy'

        cfg.log.info("loadVideos: {0} @ {1}".format(self.posPath, QThread.currentThread().objectName()))
        #         print "RUN", QThread.currentThread().objectName(), QApplication.instance().thread().objectName(), '\n'
        rc = Client()
        cfg.log.debug("rc.ids : {0}".format(rc.ids))
        
        dview = rc[:]        
        dview['np2qimage'] = np2qimage
        dview['QImage'] = QImage
        dview['pth'] = sys.path
#         dview['np'] = np
        lbview = rc.load_balanced_view()   
        
        #@lbview.parallel(block=True)
        def loadVideo(f, idxSlice, vialNo, imTransform=None):    
#             from qimage2ndarray import array2qimage
            import sys
            from pyTools.system.videoExplorer import videoExplorer
            import numpy as np    
            from PySide.QtGui import QImage
            from scipy.misc import imresize 
            
            
            vE = videoExplorer()        
            
            if imTransform is None:
                imTransform = lambda x: imresize(x, [64, 64])
#             else:
#                 imTransform = lambda x: imresize(x)
                
            
            im = []#np2qimage(np.rot90(vE.getFrame(f, info=False, 
            #                              frameMode='RGB')) * 255)]
            endOfFile = None
            try:
                frame = vE.getFrame(f, idxSlice.start, info=False, 
                                    frameMode='RGB')
                im += [[frame, imTransform(frame)]]
            except StopIteration:
                endOfFile = idxSlice.start
                           
            
            for idx in range(idxSlice.start+1, idxSlice.stop):
                if endOfFile is not None:
                    break
#                 im += [np2qimage(np.rot90(frame) * 255)]
#                 im += [[imresize(frame, 0.5), imresize(frame, [64,64])]]
                try:
                    frame = vE.next()
                    im += [[frame, imTransform(frame)]]
                except StopIteration:
                    endOfFile = idx
                        
            ret = dict()
            
            ret["vialNo"] = vialNo
            ret["qi"] = im
            ret['endOfFile'] = endOfFile
            return ret     
            
            
        results = []
        
        if self.selectedVials is None:
            f = self.posPath# self.posPath.split(self.videoEnding)[0] + self.videoEnding#.v{0}.{1}'.format(i, 'avi')
            results += [lbview.apply_async(loadVideo, f, self.idxSlice, 0,
                                           self.imTransform)]
        else:        
            for i in self.selectedVials:
                f = self.posPath.split(self.videoEnding)[0] + \
                    '.v{0}.{1}'.format(i, self.videoEnding)
                results += [lbview.apply_async(loadVideo, f, i, 
                                               self.imTransform)]
        
        cfg.log.debug("videoLoader: waiting for process...")
        allReady = False
        while not allReady:
            if False:#self.exiting:
                for i in range(len(results)):
                    results[i].abort()
                    # delete data from cluster
                    msgId = results[i].msg_id
                    #~ del lbview.results[msgId]
                    del rc.results[msgId]
                    del rc.metadata[msgId]
                
                return   
            
            allReady = True
            for ar in results:
                allReady = allReady and ar.ready()
                
            if self.thread is None:
                import time
                time.sleep(0.01)
            else:
                self.thread.msleep(10)
        
        cfg.log.debug("videoLoader: copy results")
        self.frameList = [[] for i in range(self.maxOfSelectedVials() + 1)]
        for i in range(len(results)):
            # copy data
            ar = results[i].get()
            # TODO: make it dynamic again for later
            self.frameList[ar["vialNo"]] = copy.copy(ar["qi"]) 
            self.endOfFile += copy.copy(ar['endOfFile'])
#             self.frameList[0] = ar["qi"]
            # delete data from cluster
            msgId = results[i].msg_id
            #~ del lbview.results[msgId]
            del rc.results[msgId]
            del rc.metadata[msgId]
        
        # close client to close socket connections
        cfg.log.debug("videoLoader: close client to close socket connections")
        rc.close()
        
        if True:#not self.exiting:
            # using max(self.selectedVials) to make sure that the list entry
            # has actually some frames and is no dummy
            self.videoLength = len(self.frameList[self.maxOfSelectedVials()])
            
            cfg.log.debug("videoLoader: load positions")
            try:
                self.pos = np.load(self.posPath.split(self.videoEnding)[0] + 
                                   '.pos.npy')
            except IOError:
                # create dummy positions to keep stuff internally going
                self.pos = np.zeros((self.videoLength, 
                                     self.maxOfSelectedVials() + 1,
                                     2))
        
#         if True:#not self.exiting:
#             cfg.log.debug("videoLoader: load annotations")
#             self.annotation = loadAnnotation(self.posPath, self.videoLength)
        
        cfg.log.debug("finished loading, emiting signal {0}".format(self.videoLength))
# 
#         if self.videoHandler is not None:
#             self.videoHandler.updateNewAnnotation([self.annotation, self.posPath])
        
        
        lastFrameNo = None
        for eof in self.endOfFile:
            if eof is not None:
                if lastFrameNo is None:
                    lastFrameNo = eof
                elif lastFrameNo is not eof:
                    raise ValueError("two video files in the same minute have different lengths!")
        
        if lastFrameNo is not None:
            self.eof.emit(lastFrameNo)
                
        self.loading = False
#         self.finished.emit()  
#         self.loadedAnnotation.emit([self.annotation, self.posPath])
        
        cfg.log.info("finsihed loadVideos: {0} @ {1}".format(self.posPath, QThread.currentThread().objectName()))
        
        
    @cfg.logClassFunction
    def getVideoLength(self):        
        while self.loading:
            cfg.log.warning("(getVideoLength)------------------- waiting for frame because its not buffered yet")
            time.sleep(0.5)
            
        if not self.loading:
            return self.videoLength
        else:
            raise RuntimeError("calling length, before video finished")
        
    @cfg.logClassFunction
    def getPositionLength(self):
        if not self.loading:
            return len(self.pos)
        else:
            raise RuntimeError("calling length, before video finished loading")
            
    @cfg.logClassFunction
    def getFrame(self, idx):
        if self.loading:
            cfg.log.warning("------------------- waiting for frame because its not buffered yet")
            return False
            

#         if self.exiting:
#             return
        
        if idx < self.videoLength:
            out = []
            for i in range(len(self.frameList)):
                if not idx >= len(self.frameList[i]):
                    out += [[self.frameList[i][idx] ,  
                             self.annotation.frameList[idx][i]]]
                else:
                    out += [[]]
                
            return [self.pos[idx], out]
        else:
            cfg.log.error("error in fetching key {0}, idx {1}".format(self.posPath, idx))
            raise RuntimeError("Video frame was not available (index out of range (requested {0} of {1} @ {2})".format(idx, len(self.frameList), self.posPath))
            
    @cfg.logClassFunction
    def getPosList(self):
        if not self.loading2:
            return self.pos
        else:
            raise RuntimeError("calling posList, before video finished loading")
            
    @cfg.logClassFunction
    def addAnnotation(self, vialNo, frames, behaviour, annotator):
        cfg.log.debug("(VideoLoader) - begin")
        if not self.loading:
            self.annotation.addAnnotation(vialNo, frames, behaviour, annotator)
        cfg.log.debug("(VideoLoader) - end")

class VideoHandler(QObject):       
    newVideoLoader = Signal(list)
    deleteVideoLoader = Signal(list)
    
    newAnnotationLoader = Signal(list)
    deleteAnnotationLoader = Signal(list)
    
    changedFile = Signal(str)
    
    @cfg.logClassFunction
    def __init__(self, posList, fileChangeCb, selectedVials=[0], startIdx=0):
        super(VideoHandler, self).__init__()        
        
        self.videoDict = dict()
        self.annoDict = dict()
        self.posList = []
        self.annoViewList = []
        self.posPath = ''
        self.idx = 0
        self.pathIdx = 0
        
        ### old stuff ?
        self.dictLength = 5         # should be odd, otherwise fix checkBuffers()!
        self.delBuffer = 5
        ### old stuff ?
        
        self.bufferWidth  = 100     # width of each buffer
        self.bufferLength = 3       # number of buffers on EITHER SIDE
        self.bufferJut = 1          # number of buffers outside of the core 
                                    # buffer area on EITHER SIDEthat are not 
                                    # deleted immediately
        self.videoLengths = dict()  # lengths of each video chunk
        
        
        self.posList = sorted(posList)
        self.posPath = posList[startIdx]
        
        self.annoAltStart = None
        
        ## video loading
        self.vLL = VideoLoaderLuncher(eofCallback=self.endOfFileNotice)

        self.videoLoaderLuncherThread = MyThread("videoLuncher")
        self.vLL.moveToThread(self.videoLoaderLuncherThread)
        
        self.videoLoaderLuncherThread.start()
        self.videoLoaderLuncherThread.wrapUp.connect(self.vLL.aboutToQuit)

        self.vLL.createdVideoLoader.connect(self.linkToAnnoview)
        self.newVideoLoader.connect(self.vLL.lunchVideoLoader)
        self.deleteVideoLoader.connect(self.vLL.deleteVideoLoader)
        
        ## annotation loading
        self.aLL = AnnotationLoaderLuncher(self.updateNewAnnotation)

        self.annotationLoaderLuncherThread = MyThread("annotationLuncher")
        self.aLL.moveToThread(self.annotationLoaderLuncherThread)
        
        self.annotationLoaderLuncherThread.start()
        self.annotationLoaderLuncherThread.wrapUp.connect(self.aLL.aboutToQuit)

#         self.aLL.createdAnnotationLoader.connect(self.linkToAnnoview)
        self.newAnnotationLoader.connect(self.aLL.lunchAnnotationLoader)
        self.deleteAnnotationLoader.connect(self.aLL.deleteAnnotationLoader)
        
        
        self.bufferEndingQueue = []         # queue of videos that need to
                                            # be prefetched (i.e. bufferEnding
                                            # has to be called with this
                                            # values)
        
        self.loadProgressive = False
        
        self.loadingFinished = False
        self.annotationBundle = []
        
        self.fileChangeCB = fileChangeCb
        
        self.selectedVials = selectedVials
        
        self.curMetadata = None
        self.tempValue = dict()
        
        # always do that at the end
#         self.checkBuffer()
        
        self.vE = videoExplorer()
        
        

    def maxOfSelectedVials(self):
        return maxOfSelectedVials(self.selectedVials)
    
    def aboutToQuit(self):
        self.videoLoaderLuncherThread.quit()
    
    @cfg.logClassFunction
    def setFrameIdx(self, idx):
        self.idx = idx
    
    @cfg.logClassFunction
    def getCurrentPosList(self):
        pos = []
        i = 0
        for key in sorted(self.videoDict):
            try:
                pos += [self.videoDict[key].getPosList()]
            except RuntimeError:
                pass
            i += 1
            if key == self.posPath:
                idx = i
            
        return pos, idx
    
    @cfg.logClassFunction
    def getCurrentVideoLength(self):
        return self.videoDict[self.posPath].getVideoLength()
        
    @cfg.logClassFunction
    def getCurrentPositionLength(self):
        return self.videoDict[self.posPath].getPositionLength()
        
    @cfg.logClassFunction
    def getCurrentFrameNo(self):
        return self.idx
    
    @cfg.logClassFunction
    def getFrame(self, posPath, idx):        
        self.idx = idx
        self.posPath = posPath
        self.checkBuffer(False)
        return self.getCurrentFrame()
        
        
    @cfg.logClassFunction
    def getTempFrame(self, increment):      
        idx = self.idx
        path = self.posPath
        
        try:
            if increment > 0:
                frame = self.getNextFrame(increment, doBufferCheck=False, emitFileChange=False)
            else:
                frame = self.getPrevFrame(-increment, doBufferCheck=False, emitFileChange=False)
        except KeyError:
            pass
        except RuntimeError:
            cfg.log.debug("something went wrong during the fetching procedure")
                
        self.idx = idx
        self.posPath = path
        
        return frame
        
    @cfg.logClassFunction
    def getCurrentFrame(self, doBufferCheck=True, updateAnnotationViews=True):
        while self.videoDict[self.posPath] is None:
            cfg.log.info("waiting for videopath")   
            QApplication.processEvents()
            time.sleep(0.05)
                         
        try:
            frame = self.videoDict[self.posPath].getFrame(self.idx)
            if not frame:
                frame = [[[0,0] 
                                for i in range(self.maxOfSelectedVials() + 1)], 
                         [[np.zeros((64,64,3)), {'confidence': 0}] 
                                for i in range(self.maxOfSelectedVials() + 1)]]
                #[[[0,0]] * (max(self.selectedVials) + 1), np.zeros((64,64,3))]
                    
        except KeyError:
            cfg.log.exception("accessing video out of scope, fetching...")
            self.fetchVideo(self.posPath)
            #self.getFrame(self.posPath, idx)
            self.getCurrentFrame()
        except RuntimeError as e:
            cfg.log.error("something went wrong during the fetching procedure: error message {0}".format(e.message))
            frame = [[[0,0]] * (self.maxOfSelectedVials() + 1), 
                     [np.zeros((64,64,3))] * (self.maxOfSelectedVials() + 1)]
            
        if doBufferCheck:
            self.checkBuffer(updateAnnotationViews)            
        
            if updateAnnotationViews:
                self.updateAnnoViewPositions()
            
            logGUI.debug(json.dumps({"key":self.posPath, 
                                     "idx":self.idx}))
                
#         else:
#             frame = self.videoDict[self.posPath]
            
        return frame
    
    
    @cfg.logClassFunction
    def getCurrentFrameUnbuffered(self, doBufferCheck=False, 
                                  updateAnnotationViews=False):
        
        
        img = self.vE.getFrame(self.posPath, frameNo=self.idx, frameMode='RGB')
        frame = [[[0,0] 
                        for i in range(self.maxOfSelectedVials() + 1)], 
                 [[[img], {'confidence': 0}]  * \
                             (self.maxOfSelectedVials() + 1)]]
        
        if doBufferCheck:
            self.checkBuffer(updateAnnotationViews)            
        
            if updateAnnotationViews:
                self.updateAnnoViewPositions()
            
        return frame
    
        
    @cfg.logClassFunction
    def getBufferFrame(self, posPath, idx):    
        frame = []  
        try:
            frame = self.videoDict[posPath].getFrame(idx)
            
        except KeyError:
            pass
            
        return frame
                
    @cfg.logClassFunction
    def getNextFrame(self, increment=1, doBufferCheck=True, emitFileChange=True,
                     unbuffered=False):
        self.idx += increment

        if self.idx >= self.videoLengths[self.posPath]:
            keys = sorted(self.videoDict.keys())
            pos = [i for i,k in enumerate(keys) if k==self.posPath][0]
            changedFile = False
            while self.idx >= \
                    self.videoLengths[self.posPath]: 
                if pos != len(keys) - 1:
                    self.idx -= self.videoLengths[self.posPath]                                         
                    self.posPath = keys[pos+1]
                    pos += 1 
                    changedFile = True
                else:
                    self.idx = self.videoLengths[self.posPath] -1
                    if doBufferCheck:
                        cfg.log.warning("This is the very last frame, cannot advance further")
                    break
                
                # TODO make better fix
                if self.posPath is None:
                    break
                        
            if changedFile and emitFileChange:
                self.fileChangeCB(self.posPath)  
                        
        if not unbuffered:
            return self.getCurrentFrame(doBufferCheck=doBufferCheck)
        else:
            return self.getCurrentFrameUnbuffered(doBufferCheck=doBufferCheck)
        
    @cfg.logClassFunction
    def getPrevFrame(self, decrement=1, doBufferCheck=True, emitFileChange=True,
                     unbuffered=False):
        self.idx -= decrement
        
        if self.idx < 0:
            keys = sorted(self.videoDict.keys())
            pos = [i for i,k in enumerate(keys) if k==self.posPath][0]
            changedFile = False
            while self.idx < 0:
                if pos != 0:
                    self.idx += self.videoLengths[self.posPath]
                    self.posPath = keys[pos-1] 
                    pos -= 1              
                    changedFile = True
                else:
                    self.idx = 0
                    if doBufferCheck:
                        cfg.log.warning("This is the very first frame, cannot go back further")
                    break    
            
            if changedFile and emitFileChange:
                self.fileChangeCB(self.posPath)   
                
                        
        if not unbuffered:
            return self.getCurrentFrame(doBufferCheck=doBufferCheck)
        else:
            return self.getCurrentFrameUnbuffered(doBufferCheck=doBufferCheck)
    
                
    @cfg.logClassFunction
    def checkBuffer(self, updateAnnoViewPositions=True):        
#         hS = ((self.dictLength + 1) / 2.0)
#         currIdx = self.posList.index(self.posPath)
#         
#         s = int(currIdx - hS)
#         e = int(currIdx + hS +1)
#         if s < 0:
#             s = 0
#         if e > len(self.posList):
#             e = len(self.posList)            
#         fetchRng = slice(s, e) 
#         
#         s -= self.delBuffer
#         e += self.delBuffer
#         if s < 0:
#             s = 0
#         if e > len(self.posList):
#             e = len(self.posList)   
#           
#         delRng = slice(s, e)
#         
#         # delete all videos that are out of scope
#         for vidPath in self.videoDict.keys():
#             try:
#                 self.posList[fetchRng].index(vidPath)
#             except ValueError:
#                 ################################################################ TODO: remove only if annotation is not open                
#                 cfg.log.info("delete {0}".format(vidPath))
#                 if updateAnnoViewPositions:
#                     for aV in self.annoViewList:
#                         aV.removeAnnotation(vidPath)
#                                                             
#                 cfg.log.debug("delete video dict")
# #                 self.dump = self.videoDict[vidPath]
#                 self.deleteVideoLoader.emit([self.videoDict[vidPath], vidPath])
#                 
#                 # first make sure to not refer anymore to VL
#                 self.videoDict[vidPath] = None
# #                 delete key/value pair
#                 del self.videoDict[vidPath]
#                                 
#                 cfg.log.debug("delete finish")
#                 
#         
#         # prefetch all videos that are not prefetched yet
#         for vidPath in self.posList[fetchRng]:
#             try:
#                 self.videoDict[vidPath]
#             except KeyError:
#                 self.fetchVideo(vidPath, idxRange)


               
        bufferedKeysR = self.checkBuffersRight()
        bufferedKeysL = self.checkBuffersLeft()
        self.deleteOldBuffers(bufferedKeysR, bufferedKeysL, 
                              updateAnnoViewPositions)
        

    def deleteOldBuffers(self, bkR, bkL, updateAnnoViewPositions):
        # extend right buffer to account for jut
        curKey = sorted(bkR.keys())[-1]
        curIdx = sorted(bkR[curKey])[-1]
        for i in range(self.bufferJut):    
            curKey, curIdx = self.parseBuffersRight(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bkR.keys():
                bkR[curKey] = [] 
                
            bkR[curKey] += [curIdx]
                    
        # extend left buffer to account for jut
        curKey = sorted(bkL.keys())[-1]
        curIdx = sorted(bkL[curKey])[-1]
        for i in range(self.bufferJut):    
            curKey, curIdx = self.parseBuffersLeft(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bkL.keys():
                bkL[curKey] = [] 
                
            bkL[curKey] += [curIdx]
            
        # advance and behind buffer key
        advKeyIdx = self.posList.index(sorted(bkR.keys())[-1]) + 1
        if advKeyIdx > len(self.posList):
            advKeyIdx = None
                    
        behKeyIdx = self.posList.index(sorted(bkL.keys())[0]) - 1
        if behKeyIdx < 0:
            behKeyIdx = None
            
        # check all buffers if lying within jut, unbuffer otherwise
        for key in self.videoDict.keys():
            if key in bkR.keys() or key in bkL.keys():
                for idx in self.videoDict[key].keys():
                    if idx in bkR[key].keys() or idx in bkL[key].keys():
                        continue
                    else:
                        self.unbuffer(key, idx, updateAnnoViewPositions)
            else:
                for idx in sorted(self.videoDict[key].keys()):
                    if idx == 0 and key == advKeyIdx:
                        # ahead buffered first buffer
                        continue
                    if key == behKeyIdx \
                    and len(self.videoDict[key].keys()) == 1:
                        # behing (left hand side) buffered last buffer
                        continue
                    
                    self.unbuffer(key, idx, updateAnnoViewPositions)
                    
                self.deleteAnnotationLoader.emit([self.annoDict[key]])
            
            
    def unbuffer(self, key, idx, updateAnnoViewPositions):        
        cfg.log.debug("delete video dict")
        self.deleteVideoLoader.emit([self.videoDict[key][idx]])
        
        # first make sure to not refer anymore to VL
        self.videoDict[key][idx] = None
        # delete key/value pair
        del self.videoDict[key][idx]

        cfg.log.debug("delete finish")
        
        if key not in self.videoDict[key].keys():
            if updateAnnoViewPositions:
                for aV in self.annoViewList:
                    aV.removeAnnotation(key)
        
        
        
    def checkBuffersRight(self):        
        # index of current frame in videoDict
        curIdx = np.mod(self.idx, self.bufferWidth)
        curKey = self.posPath
        
        bufferedKeys = dict()
        bufferedKeys[curKey] = []
        
        for i in range(self.bufferWidth):
            curKey, curIdx = self.parseBuffersRight(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            self.ensureBuffering(curKey, curIdx)
            bufferedKeys[curKey] += [curIdx]
        
        return bufferedKeys
            
    def parseBuffersRight(self, curKey, curIdx):        
        curIdx += 1
        if  curKey in self.videoLengths.keys():
            if self.videoLengths[curKey] is not None \
            and (curIdx * self.bufferWidth) >= self.videoLengths[curKey]:
                curIdx = 0
                newKeyIdx = self.posList.keys().index(curKey) + 1
                if newKeyIdx < len(self.posList):
                    curKey = self.posList[newKeyIdx]
                else:
                    curKey = None
                    curIdx = None
                    
        return curKey, curIdx
                
        
    def checkBuffersLeft(self):
        curIdx = np.mod(self.idx, self.bufferWidth)
        curKey = self.posPath
        
        bufferedKeys = dict()
        bufferedKeys[curKey] = []
        
        for i in range(self.bufferWidth):
            curKey, curIdx = self.parseBuffersLeft(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            self.ensureBuffering(curKey, curIdx)
            bufferedKeys[curKey] += [curIdx]
                
        return bufferedKeys
                
    def parseBuffersLeft(self, curKey, curIdx):
        curIdx -= 1
        
        if curIdx < 0:
            newKeyIdx = self.posList.keys().index(curKey) - 1
            if newKeyIdx >= 0:
                curKey = self.posList[newKeyIdx]  
                if  curKey in self.videoLengths.keys():
                    if self.videoLengths[curKey] is not None:
                        curIdx = self.videoLengths[curKey]
                else:
                    self.bufferEnding(curKey)                    
            else:
                curIdx = None
                curKey = None
        
        return curKey, curIdx
        
    def ensureBuffering(self, curKey, curIdx):
        try:
            self.videoDict[curKey][curIdx]
        except KeyError:
            self.fetchVideo(curKey, curIdx)
        except IndexError:
            self.fetchVideo(curKey, curIdx)
        
        
    def bufferEnding(self, key):
        if key in self.videoLengths.keys():            
            idx = np.mod(self.videoLengths[key], self.bufferWidth)
            self.fetchVideo(key, idx)
        else:
            self.videoLengths[key] = None
            self.newAnnotationLoader.emit([key])
            self.bufferEndingQueue += [key]
        
    @Slot(list)
    def endOfFileNotice(self, lst):
        key = lst[0] 
        length = lst[1]
        
        self.updateVideoLength(key, length)
        
        nextKey = self.posList[self.posList.keys().index(key) + 1]
        
        # if end of file notice was send, while moving towards the right-hand
        # side
        if len(self.videoDict[key]) > 1:
            self.ensureBuffering(nextKey, 0)
        
    @Slot(list)
    def updateVideoLengthAndFetchLastBuffer(self, lst):
        key = lst[0]
        length = lst[1]
        
        self.updateVideoLength(key, length)
        self.bufferEnding(key)
        
    def updateVideoLength(self, key, length):
        self.videoLengths[key] = length
        
        
    @cfg.logClassFunction
    def fetchVideo(self, path, idx):
        cfg.log.info("fetching {0}".format(path))
#         vL = VideoLoader(path)
#         vL.loadedAnnotation.connect(self.updateNewAnnotation)
        bufferStart = idx * self.bufferWidth
        idxRange = slice(bufferStart, bufferStart + self.bufferWidth)
        
        if path not in self.videoDict.keys():
            self.videoDict[path] = dict()
            
        self.videoDict[path][idx] = None        
        
        self.newVideoLoader.emit([path, self, self.selectedVials, 
                                  idx, idxRange])
        
        
    @cfg.logClassFunction
    @Slot(list)
    def linkToAnnoview(self, lst):
        """
        Args:
            lst ([path, idx, videoLoader]) 
        """ 
        path = lst[0]
        idx = lst[1]
        vL = lst[2]
        self.videoDict[path][idx] = vL
        
    @cfg.logClassFunction
    def addAnnoView(self, annoView):
        for vidPath in self.annoDict:
            if (not self.annoDict[vidPath] is None) and \
               (not self.annoDict[vidPath].loading):
                cfg.log.debug("annotation id: {0}".format(id(self.annoDict[vidPath].annotation)))
                annoView.addAnnotation(self.annoDict[vidPath].annotation, vidPath)
                
        self.annoViewList += [annoView]
        
    @cfg.logClassFunction
    def removeAnnoView(self, idx):
        self.annoViewList.pop(idx)
        
    @cfg.logClassFunction
    def updateAnnoViewPositions(self, updateOnlyTempPosition=False):
        if self.loadingFinished:
            self.loadingFinished = False
            self.loadAnnotationBundle()
            
        for aV in self.annoViewList:
            aV.setPosition(self.posPath, self.idx, 
                           tempPositionOnly= updateOnlyTempPosition,
                           metadata=self.curMetadata)
        
    
        
#     @cfg.logClassFunction
    @Slot(list)
    def updateNewAnnotation(self, annotationBundle):  
        self.annotationBundle += [annotationBundle]
        self.loadingFinished = True
        
    @cfg.logClassFunction
    def loadAnnotationBundle(self): 
        self.annotationBundle = sorted(self.annotationBundle, key=lambda x: x[1])
        
        for annotationBundle in self.annotationBundle:
            annotation = annotationBundle[0]
            path = annotationBundle[1]
            for aV in self.annoViewList:
                aV.addAnnotation(annotation, path , 
                                 addAllAtOnce=(not self.loadProgressive))
                
            self.annoDict[path] = annotation
            # save pathlength and bufferEnding if requested earlier
            self.videoLengths[path] = len(annotation.frameList)
            if path in self.bufferEndingQueue:
                self.bufferEnding(path)
                self.bufferEndingQueue.pop(self.bufferEndingQueue.index(path))
            
        self.annotationBundle = []
        
            
    @cfg.logClassFunction
    def addFrameToAnnotation(self, vialNo, annotator, behaviour):   
        for aV in self.annoViewList:
            aV.addFramesToAnnotation(self.posPath, [self.idx], annotator, 
                                                                    behaviour)
                                                                    
        
        self.annoDict[self.posPath].addAnnotation(vialNo, [self.idx], 
                                                   behaviour, annotator)
                                                                    
    @cfg.logClassFunction
    def annoViewZoom(self, zoomLevel):
        for aV in self.annoViewList:
            aV.setZoom(zoomLevel)
        
    @cfg.logClassFunction
    def updateAnnotationProperties(self, metadata):
        """
            metadata is the property of the annotation
        """
        
        self.curMetadata = metadata
        
        if not self.annoAltStart:
            return
                
        curAnnoEnd = bsc.FramePosition(self.annoDict, self.posPath, self.idx) 
        lenFunc = lambda x: len(x.frameList[0])                
        
        newRng = bsc.generateRangeValuesFromKeys(self.annoEnd, 
                                                 curAnnoEnd,
                                                 lenFunc=lenFunc)
        
        for key in newRng:
            for idx in newRng[key]:
                if not key in self.tempValue.keys():
                    self.tempValue[key] = dict()
                    
                self.tempValue[key][idx] =  metadata
                
        self.annoEnd = curAnnoEnd
        
    @cfg.logClassFunction
    def addAnnotation(self, vial, annotator, behaviour, metadata):
        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if vial == aV.vialNo:
                        cfg.log.debug("calling aV.addAnno()")
                        aV.addAnno(self.posPath, self.idx, metadata)
                        
        if self.annoAltStart == None:
            self.annoAltStart = bsc.FramePosition(self.annoDict, self.posPath, 
                                                                    self.idx)
            
            self.annoEnd = bsc.FramePosition(self.annoDict, self.posPath, 
                                             self.idx)
             
            self.annoAltFilter = AnnotationFilter([vial], [annotator], 
                                                                    [behaviour])
            
            self.tempValue = dict()
            
            self.updateAnnotationProperties(metadata)
            
            
        else:
            curFilter = AnnotationFilter([vial], [annotator], [behaviour])
            sameAnnotationFilter = \
                    all((sorted(curFilter[i]) == sorted(self.annoAltFilter[i]) \
                                        for i in range(len(curFilter))))
            if not sameAnnotationFilter:
                self.escapeAnnotationAlteration()
            else:
                annoEnd = bsc.FramePosition(self.annoDict, self.posPath, self.idx)    
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.frameList[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
                            
                for key in rng:
                    self.annoDict[key].annotation.addAnnotation(vial, rng[key], 
                                            annotator, behaviour, 
                                            self.tempValue[key])
                                            
                    cfg.log.info("add annotation vial {v}| range {r}| annotator {a}| behaviour {b}| confidence {c}".format(
                                v=vial, r=rng[key], a=annotator,
                                  b=behaviour, c=self.tempValue[key]))
                    
                    tmpFilename = '.'.join(key.split(".")[:-1]) + ".bhvr~"
                    self.annoDict[key].annotation.saveToFile(tmpFilename)
                    
                    # refresh annotation in anno view
                    for aV in self.annoViewList:
                        if (aV.behaviourName == None) \
                        or (behaviour == aV.behaviourName) \
                        or (behaviour in aV.behaviourName):
                            if (aV.annotator == None) \
                            or (annotator == aV.annotator) \
                            or (annotator in aV.annotator):
                                if vial == aV.vialNo:
                                    cfg.log.debug("refreshing annotation")
                                    aV.addAnnotation(\
                                                self.annoDict[key].annotation,
                                                     key)
                
                logGUI.info(json.dumps({"vial":vial,
                                       "key-range":rng, 
                                       "annotator":annotator,
                                       "behaviour":behaviour, 
                                       "metadata":self.tempValue[key]}))
                
                self.annoAltStart = None
        
    @cfg.logClassFunction
    def eraseAnnotation(self, vial, annotator, behaviour):
        for aV in self.annoViewList:
            if aV.behaviourName == None \
            or behaviour == aV.behaviourName \
            or behaviour in aV.behaviourName:
                if aV.annotator == None \
                or annotator == aV.annotator \
                or annotator in aV.annotator:
                    if vial == aV.vialNo:
                        cfg.log.debug("eraseAnnotation")
                        aV.eraseAnno(self.posPath, self.idx)
                        
        if self.annoAltStart == None:
            self.annoAltStart = bsc.FramePosition(self.annoDict, self.posPath, 
                                                                    self.idx)
            
            self.annoEnd = bsc.FramePosition(self.annoDict, self.posPath, 
                                             self.idx)
             
            self.annoAltFilter = AnnotationFilter([vial], [annotator], 
                                                                    [behaviour])
        else:
            curFilter = AnnotationFilter([vial], [annotator], [behaviour])
            sameAnnotationFilter = \
                    all((sorted(curFilter[i]) == sorted(self.annoAltFilter[i]) \
                                        for i in range(len(curFilter))))
            if not sameAnnotationFilter:
                self.escapeAnnotationAlteration()
            else:
                annoEnd = bsc.FramePosition(self.annoDict, self.posPath, self.idx)    
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.frameList[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
                self.annoAltStart = None
                
                for key in rng:
                    self.annoDict[key].annotation.removeAnnotation(vial, rng[key], 
                                            annotator, behaviour)
                    tmpFilename = '.'.join(key.split(".")[:-1]) + ".bhvr~"
                    self.annoDict[key].annotation.saveToFile(tmpFilename)
                
                    # refresh annotation in anno view
                    for aV in self.annoViewList:
                        if (aV.behaviourName == None) \
                        or (behaviour == aV.behaviourName) \
                        or (behaviour in aV.behaviourName):
                            if (aV.annotator == None) \
                            or (annotator == aV.annotator) \
                            or (annotator in aV.annotator):
                                if vial == aV.vialNo:
                                    cfg.log.debug("refreshing annotation")
                                    aV.addAnnotation(\
                                                self.annoDict[key].annotation,
                                                     key)
                                    
                logGUI.info(json.dumps({"vial":vial,
                                       "key-range":rng, 
                                       "annotator":annotator,
                                       "behaviour":behaviour}))
                
                self.annoAltStart = None
        
                        
    @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        self.annoAltStart = None
        self.annoAltFilter = None
        
        for aV in self.annoViewList:
            aV.escapeAnno()
            aV.setPosition()
            
    @cfg.logClassFunction
    def saveAll(self):
        for key in self.annoDict:
            tmpFilename = '.'.join(key.split(".")[:-1]) + ".bhvr"
            self.annoDict[key].annotation.saveToFile(tmpFilename)
    
class AnnotationItemLoader(BaseThread):
    annotationStuff = Signal(list)
    
    @cfg.logClassFunction
    def __init__(self, key, annotationDict, absIdx, aCol, uCol):
        super(AnnotationItemLoader, self).__init__()
        self.lines = dict()
        self.frames = dict()
        self.absIdx = absIdx
        self.chunks = dict()
        
        self.annotationDict = annotationDict
        self.aCol = aCol
        self.uCol = uCol
        self.key = key            
        self.processedSignal = False
        
    @cfg.logClassFunction
    def run(self):
        """
        Key needs to be in self.annotationDict !!
        """

        keys = sorted(self.annotationDict.keys())
        key = self.key
        
        if key == keys[0]:
            if len(keys) > 1:
                i = self.absIdx[keys[1]][0] - len(self.annotationDict[key].frameList)
            else:
                i = 0
        elif key == keys[-1]:
            if len(keys) > 1:
                i = self.absIdx[keys[-2]][-1] + 1
            else: 
                # should never happen anyway
                i = 0
        else:
            cfg.log.debug("tried to insert an annotation in the middle." + 
                 " It only makes sense to append, or prepend. Trying to clear and" +
                 " repopulate entirely")
            self.clearScene()
            self.populateScene()
            return
        
        cfg.log.debug("i: {i} key: {key}".format(i=i, key=key))
        
        boxHeight = 10
        
        aBrush = QBrush(self.aCol)
        aPen = QPen(self.aCol)
        
        uPen = QPen(self.uCol)
        uBrush = QBrush(self.uCol)
        
        self.lines[key] = []
        self.frames[key] = []
        chunkLength = len(self.annotationDict[key].frameList)
        self.chunks[key] = QGraphicsRectItem(QRectF(i, 0, chunkLength, boxHeight))         
        self.absIdx[key] = np.arange(chunkLength) + i
        
        for f in range(len(self.annotationDict[key].frameList)):
            line = QGraphicsLineItem(i+0.5, 0, i+0.5, boxHeight,
                                     self.chunks[key])
            line.setPen(QPen(QColor(100,100,100)))
            self.lines[key] += [line]
            if self.annotationDict[key].frameList[f] is not None:
                item = QGraphicsRectItem(   QRectF(i, 0, 1, boxHeight), 
                                            self.chunks[key])
                item.setPen(aPen)
                item.setBrush(aBrush)
                self.frames[key] += [item]
            else:
                item = QGraphicsRectItem(   QRectF(i, 0, 1, boxHeight), 
                                            self.chunks[key])
                item.setPen(uPen)
                item.setBrush(uBrush)
                self.frames[key] += [item]
                                                    
            i += 1
            
        self.annotationStuff.emit([self.chunks, self.absIdx, self.lines, 
                                self.frames, self])
        
        cfg.log.debug("end of worker thread for {key}".format(key=key))
        
        #~ while(True):
            #~ if self.processedSignal:
                #~ del self
            #~ else:
                #~ self.msleep(100)
                    
                    
class VideoLoaderLuncher(QObject):        
    createdVideoLoader = Signal(list)  
    loadVideos = Signal() 
    
    @cfg.logClassFunction
    def __init__(self, parent=None, eofCallback):
        """
        This object will exectute `func` with `args` in a
        separate thread. You can query ready() to check
        if processing finished and get() to get the result.

        Args:
            func (function pointer)
                        function will be called asyncroneously
            args (arguments)
                        arguments for func
        """
        super(VideoLoaderLuncher, self).__init__(None)
            
        self.availableVLs = []
        self.dumpingPlace = []
        self.threads = dict()
        self.eofCallback = eofCallback
            
    
    
#     @cfg.logClassFunction
    @Slot(list)
    def lunchVideoLoader(self, lst):
        """
        Args:
            lst ([string, callback])
        """
#         print "RUN", QThread.currentThread().objectName(), QApplication.instance().thread().objectName(), '\n'
        path = lst[0]
        vH = lst[1]
        selectedVials = lst[2]
        idx = lst[3]
        idxSlice = lst[4]
        
        if len(self.availableVLs) == 0:
            cfg.log.info("create new VideoLoader {0}".format(path))     
            
#             vL = VideoLoader(path, vH, selectedVials=selectedVials) 
                                     
            videoLoaderThread = MyThread("videoLoader {0}".format(len(
                                                        self.threads.keys())))
            
            vL = VideoLoader(path, vH, idxSlice=idxSlice, 
                             thread=videoLoaderThread, 
                             selectedVials=selectedVials)                 
            vL.moveToThread(videoLoaderThread)         
            videoLoaderThread.start()

            vL.startLoading.connect(vL.loadVideos)
            vL.eof.connect(self.eofCallback)
            
            cfg.log.info("finished thread coonecting signal create new VideoLoader {0}".format(path)) 
            vL.startLoading.emit()
            cfg.log.info("finished thread emit create new VideoLoader {0}".format(path)) 
            self.threads[vL] = [videoLoaderThread, vL.startLoading]
            
            cfg.log.info("finished create new VideoLoader {0}".format(path))  
        else:
            vL = self.availableVLs.pop()
            cfg.log.info("recycle new VideoLoader {0}, was previous: {1}".format(path, vL.posPath))
            thread, signal = self.threads[vL]
            vL.init(path, vH, idxSlice=idxSlice, thread=thread, 
                    selectedVials=selectedVials)     
            signal.emit()

        self.createdVideoLoader.emit([path, idx, vL])
#         cfg.log.debug("finish")
            
#     @cfg.logClassFunction
    @Slot(list)
    def deleteVideoLoader(self, lst):
        for vL in self.dumpingPlace:
            if vL is not None and not vL.loading:                 
                self.availableVLs += [vL]
                self.dumpingPlace.remove(vL)
                
        vL = lst[0]
#         vidPath = lst[1]
        
        # TODO is this potential memory leak?
        if vL is not None and not vL.loading:             
            self.availableVLs += [vL]
        else:
            self.dumpingPlace += [vL]
        
    @Slot()    
    def aboutToQuit(self):
        print "video-launcher, about to quit"
        for key in self.threads:
            self.threads[key].quit()
            
class AnnotationLoaderLuncher(QObject):      
    createdAnnotationLoader = Signal(list)  
    loadAnnotations = Signal()
    
    def __init__(self, loadedCallback): 
        super(VideoLoaderLuncher, self).__init__(None)
            
        self.availableALs = []
        self.dumpingPlace = []
        self.threads = dict()
        self.loadedCallback = loadedCallback
    
    @Slot(list)
    def lunchAnnotationLoader(self, lst):
        path = lst[0]
        
        if len(self.availableALs) == 0:
            cfg.log.info("create new AnnotationLoader {0}".format(path))     
            
#             vL = VideoLoader(path, vH, selectedVials=selectedVials) 
                                     
            annotationLoaderThread = MyThread("AnnotationLoader {0}".format(len(
                                                        self.threads.keys())))
            
            aL = AnnotationLoader(path)                 
            aL.moveToThread(annotationLoaderThread)         
            annotationLoaderThread.start()

            aL.startLoading.connect(aL.loadAnnotation)
            aL.loaded.connect(self.loadedCallback)
            
            cfg.log.info("finished thread coonecting signal create new VideoLoader {0}".format(path)) 
            aL.startLoading.emit()
            cfg.log.info("finished thread emit create new VideoLoader {0}".format(path)) 
            self.threads[aL] = [annotationLoaderThread, aL.startLoading]
            
            cfg.log.info("finished create new VideoLoader {0}".format(path))  
        else:
            aL = self.availableVLs.pop()
            cfg.log.info("recycle new VideoLoader {0}, was previous: {1}".format(path, aL.posPath))
            thread, signal = self.threads[aL]
            aL.init(path)     
            signal.emit()

        self.createdAnnotationLoader.emit([path])
        
#     @cfg.logClassFunction
    @Slot(list)
    def deleteVideoLoader(self, lst):
        for aL in self.dumpingPlace:
            if aL is not None and not aL.loading:  
                if aL.annotation.hasChanged:
                    aL.annotation.saveToFile(aL.path)               
                self.availableALs += [aL]
                self.dumpingPlace.remove(aL)
                
        aL = lst[0]
#         vidPath = lst[1]
        
        # TODO is this potential memory leak?
        if aL is not None and not aL.loading:  
            if aL.annotation.hasChanged:
                aL.annotation.saveToFile(aL.path)
                
            self.availableALs += [aL]
        else:
            self.dumpingPlace += [aL]
        
    @Slot()    
    def aboutToQuit(self):
        print "video-launcher, about to quit"
        for key in self.threads:
            self.threads[key].quit()
            
class AnnotationLoader(QObject):        
    loadedAnnotation = Signal(list) 
    startLoading = Signal()

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
                
        if self.annotation is not None:
            self.annotation.saveToFile('.'.join(self.posPath.split('.')[:-1]) + '.bhvr')
    
    @cfg.logClassFunction
    def __init__(self, path, thread, vialNames=None):
        super(VideoLoader, self).__init__(None)        
        self.init(path, thread, vialNames=None)
        
    def init(self, path, thread, vialNames=None):
        if vialNames is None:
            vialNames = [None]
        
        self.loading = False
        
        self.annotation = None
        
#         self.annotation = None # annotation object
        
        self.path = copy.copy(path)      
        
        self.thread = thread        
    
    @cfg.logClassFunction
    def loadAnnotation(self):
        from os.path import isfile    
        
        self.loading = True     
                    
        f = '.'.join(self.path.split('.')[:-1]) + '.bhvr'
        if isfile(f):
            cfg.log.debug("videoLoader: f exists create empty Annotation")
            out = Annotation()
            cfg.log.debug("videoLoader: created Annotation. try to load..")
            try:
                out.loadFromFile(f)
                cfg.log.debug("videoLoader: loaded Annotation")                    
            except:
                cfg.log.warning("load annotation of "+f+" failed, reset annotaions")
                videoLength = self.retrieveVideoLength(self.path)
                out = Annotation(frameNo=videoLength, vialNames=self.vialNames)
        else:
            cfg.log.info("videoLoader: f does NOT exist create empty Annotation")
            videoLength = self.retrieveVideoLength(self.path)
            out = Annotation(frameNo=videoLength, vialNames=self.vialNames)
            
        self.annotation = out
        self.loadedAnnotation.emit([out, self.path])
        self.loading = False
        
        
    def retrieveVideoLength(self, filename, initialStepSize=10000):
        """
        Finds video length by accessing it bruteforce
        
        """
        idx = 0
        modi = initialStepSize
        vE = videoExplorer()
        
        while modi > 1:
            while True:
                try:
                    vE.getFrame(filename, frameNo=idx, frameMode='RGB')
                except StopIteration:
                    break
                
                idx += modi
                
            idx -= modi
            modi /= 2
            

        return idx


class VideoLengthQuery(QObject):
    # signal ([filename, length])
    videoLength = Signal(list)
    startProcess = Signal()
    
    def __init__(self, filename, bufferWidth, resultSlot):
        super(VideoLengthQuery, self).__init__(None)
        self.filename = filename
        self.bufferWidth = bufferWidth
        self.length = None
        
        self.vE = videoExplorer()
        
        self.thread = MyThread("VideoLengthQuery")
                             
        self.moveToThread(self.thread)         
        self.thread.start()
        
        self.startProcess.connect(self.retrieveVideoLength) 
        self.videoLength.connect(resultSlot)
        self.startProcess.emit()
        
        
       
    @Slot()
    def retrieveVideoLength(self):
        """
        Finds video length by accessing it bruteforce
        
        """
        idx = 0
        modi = self.bufferWidth * 1000
        
        while modi > 1:
            while True:
                try:
                    self.vE.getFrame(self.filename, frameNo=idx, 
                                    frameMode='RGB')
                except StopIteration:
                    break
                
                idx += modi
                
            idx -= modi
            modi /= 2
            
            print modi, idx

        self.videoLength.emit([self.filename, idx])
        self.length = idx
        self.thread.quit()
        
        
        
class MyThread(QThread):    
    finished = Signal()
    wrapUp = Signal()
    
    def __init__(self, name):
        super(MyThread, self).__init__()
        self.setObjectName(name)    
        
        
        self.finished.connect(self.deleteLater)
#         self.finished.connect(self.deleteLater)        
        self.exiting = False

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wrapUp.emit()
        self.wait()

    def run(self):
        cfg.log.info("RUN THREAD {0} {1}".format(QThread.currentThread().objectName(),
                                                 QApplication.instance().thread().objectName()))
        self.exec_()
        print "RUN DONE", QThread.currentThread().objectName()        
        self.finished.emit()
        
        
class GraphicsVideoView(QGraphicsView):
    def enterEvent(self, event):
        QGraphicsView.enterEvent(event)
        self.viewport().setCursor(Qt.CrossCursor)
 
    def mousePressEvent(self, event):
        QGraphicsView.mousePressEvent(event);
        self.viewport().setCursor(Qt.CrossCursor);
 
    def mouseReleaseEvent(self, event):
        QGraphicsView.mouseReleaseEvent(event);
        self.viewport().setCursor(Qt.CrossCursor);
        
if __name__ == "__main__":
    
    import argparse
    import textwrap
    import json
    parser = argparse.ArgumentParser(\
    formatter_class=argparse.RawDescriptionHelpFormatter,\
    description=textwrap.dedent(\
    """
    Program to playback and annotate fly life-spans.
    
    This program can be configured with a configuration file that is specified
    in the command-line argument. An example file should have been distributed
    with this program. It should be a json file like this (remember that 
    numbers, especially vials, start with 0):
    
    {
    "vial": 3,
    "vialROI": [
        [
            350,
            660
        ],
        [
            661,
            960
        ],
        [
            971,
            1260
        ],
        [
            1290,
            1590
        ]
    ],
    "annotations": [
        {
            "annot": "peter",
            "behav": "falling"
        },
        {
            "annot": "peter",
            "behav": "dropping"
        },
        {
            "annot": "peter",
            "behav": "struggling"
        }
    ],
    "background": "/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png",
    "videoPath": "/run/media/peter/Elements/peter/data/tmp-20130506"
    }
    
    If you do not have the example file, you can simply copy and paste the 
    lines above (including the first and last { } ) in a text file and specify
    it as config-file path in the arguments.    
    """),
    epilog=textwrap.dedent(\
    """
    ============================================================================
    Written and tested by Peter Rennert in 2013 as part of his PhD project at
    University College London.
    
    You can contact the author via p.rennert@cs.ucl.ac.uk
    
    I did my best to avoid errors and bugs, but I cannot privide any reliability
    with respect to software or hardware or data (including fidelity and potential
    data-loss), nor any issues it may cause with your experimental setup.
    
    <Licence missing>
    """))
    
    parser.add_argument('-c', '--config-file', 
                help="path to file containing configuration")
    
       
    args = parser.parse_args()
    
    if args.config_file == None:
        print textwrap.dedent(\
            """
            Expect configuration file (-c option). 
            Run 'python videoPlayer_pySide.py -h' for more information
            """)
        sys.exit()
    
    with open(args.config_file, 'r') as f:
        config = json.load(f)
    
    
    path = config['videoPath']
    annotations = config['annotations']
    backgroundPath = config['background']
    selectedVial = config['vial']
    vialROI = config['vialROI']
    
    filterObjArgs = dict()
    
    try:
        keyMap = dict()
        for key in config['keyMap']:
            keyMap[key] = eval("Qt." + config['keyMap'][key], {"Qt":Qt})
    except KeyError:
        keyMap = None
    
    filterObjArgs["keyMap"] = keyMap
    
    try:
        stepSize = config['stepSize']
    except KeyError:
        stepSize = None
        
    filterObjArgs["stepSize"] = stepSize

    try:
        oneClickAnnotation = config['oneClickAnnotation']
    except KeyError:
        oneClickAnnotation = None
    
    filterObjArgs["oneClickAnnotation"] = oneClickAnnotation
    
    try:
        startVideo = config['startVideo']
    except KeyError:
        startVideo = None
        
    try:
        rewindOnClick = config['rewind-on-click']
    except KeyError:
        rewindOnClick = False
        
        
    
    
    logGUI = logging.getLogger("GUI")
    logGUI.setLevel(logging.DEBUG)
    hGUI = logging.FileHandler(os.path.join(path, 
                    "videoPlayer." + \
                    time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime()) +\
                    ".log"))
    fGUI = logging.Formatter('{"time": "%(asctime)s", "func":"%(funcName)s", "args":%(message)s}')
    hGUI.setFormatter(fGUI)
    for handler in logGUI.handlers:
        logGUI.removeHandler(handler)
        
    logGUI.addHandler(hGUI)
    
    
    app = QApplication(sys.argv)
    
    w = videoPlayer(path, annotations, backgroundPath, selectedVial, vialROI,
                     videoFormat='avi', filterObjArgs=filterObjArgs,
                     startVideoName=startVideo, rewindOnClick=rewindOnClick)
    
    app.connect(app, SIGNAL("aboutToQuit()"), w.exit)
    w.quit.connect(app.quit)
    
    sys.exit(app.exec_())
    
    np.asanyarray(a, dtype, order)
