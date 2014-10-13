import sys
import os
import itertools as iter


sys.path.append(os.path.abspath('../../'))
# from OpenGL import GL
# from OpenGL import GLU
from PySide import QtGui
from PySide import QtCore
# from PySide import QtOpenGL


from pyTools.gui.videoPlayer_auto import Ui_Form

from pyTools.gui.fullViewDialog import FullViewDialog as FVD

import pyTools.videoTagger.videoHandler as VH
import pyTools.videoTagger.dataLoader as DL
import pyTools.videoTagger.annoView as AV
import pyTools.videoProc.annotation as Annotation
import pyTools.videoTagger.overlayDialog as OD
import pyTools.videoTagger.modifyableRect as MR
import pyTools.system.misc as systemMisc
import pyTools.misc.config as cfg
import pyTools.videoTagger.eventFilter as EF
import pyTools.videoTagger.hud as HUD
if sys.platform != "win32":
    import pyTools.videoTagger.RPCController as RPC

import pyTools.misc.FrameDataVisualization2 as FDV
import pyTools.videoTagger.graphicsViewFDV as GFDV
import pyTools.gui.collapseContainer as CC

import numpy as np
import scipy.misc as scim
import pylab as plt
import time
import copy

import qimage2ndarray as qim2np
import json
import logging, logging.handlers
import yaml


def np2qimage(a):
    import numpy as np  
    a = a.astype(np.uint32)  
    
    data = (np.uint32(255) << 24 | a[:,:,0] << 16 | a[:,:,1] << 8 | a[:,:,2]).flatten()
    image = QtGui.QImage(data.data, a.shape[1], a.shape[0],
                          QtGui.QImage.Format_ARGB32)
    
    return image

def maxOfSelectedVials(selectedVials):
    if selectedVials is None:
        return 0
    else:
        return max(selectedVials)


#################################################################### 
class MyListModel(QtCore.QAbstractListModel): 
    def __init__(self, datain, parent=None, *args): 
        """ datain: a list where each item is a row
        """
        super(MyListModel, self).__init__(parent) 
        self.listdata = datain
 
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.listdata) 
 
    def data(self, index, role): 
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self.listdata[index.row()]
        else: 
            return None


                  
#########################################################################

class VideoTagger(QtGui.QMainWindow):
    quit = QtCore.Signal()
    startLoop = QtCore.Signal()
     
    def __init__(self, path, 
                        annotations,
                        backgroundPath,
                        selectedVial,
                        vialROI,
                        filterObjArgs=None,
                        startVideoName=None,
                        rewindOnClick=False,
                        croppedVideo=True,
                        videoExtension='.avi', #'.v0.avi',
                        runningIndeces=True,
                        fdvtPath=None,
                        bhvrListPath=None,
                        serverAddress="tcp://127.0.0.1:4242",
                        bufferWidth=300, 
                        bufferLength=4
                        ):
        """
        
        args:
            path (string):
                                root path to patches
            videoFormat (string):
                                postfix for video format *(without dot)*
        """
        QtGui.QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.cb_trajectory.setChecked(True)
        
        
        if filterObjArgs is None:
            filterObjArgs = {"keyMap":None, "stepSize":None,
                             "oneClickAnnotation":None}

        
        # self.eventFilter = EF.filterObj(self, **filterObjArgs)
        # self.installEventFilter(self.eventFilter)
        self.filterObjArgs = filterObjArgs

        self.path = path
        self.backgroundPath = backgroundPath
        self.vialROI = vialROI
        self.startVideoName = startVideoName
        self.videoEnding = videoExtension
        self.runningIndeces = runningIndeces
        self.bhvrListPath = bhvrListPath
        self.bufferWidth = bufferWidth
        self.bufferLength = bufferLength

        # self.mainShortCutFilter = EF.shortcutHandler(self, self, **self.filterObjArgs)
        self.dialogShortCutFilter = None
        self.connectSignals()       
        
        self.mouseEventFilter = EF.MouseFilterObj(self)
        
        
        self.croppedVideo = croppedVideo
        self.cropWidth = 64
        self.cropHeight = 32
        self.cropIncrement = 0
        self.isCropRectOpen = False
        self.inEditMode = True
        self.postLabelQuery = False

        if croppedVideo:
            videoExtension = "v{0}.{1}".format(selectedVial, videoExtension)

        if path.endswith(videoExtension):
            self.fileList = [path]#.split(videoExtension)[0] + '.' + videoExtension]
            print self.fileList
        elif bhvrListPath is None:
            self.fileList = systemMisc.providePosList(path, ending='.' + videoExtension)#'.bhvr')
        else:
            with open(bhvrListPath, "r") as f:
                self.fileList = json.load(f)
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.fileList))
        
        self.videoExtension = videoExtension
        self.idx = 0       
        self.play = False
        self.frameIdx = -1
        self.showTraject = False
        self.tempTrajSwap = False
        self.trajNo = 0
        self.trajLabels = []
        self.frames = []
        self.prevFrames = []
        self.increment = 0
        self.tempIncrement = 0
        self.stop = False
        self.addingAnnotations = True
        self.ui.lbl_eraser.setVisible(False)        
        self.prevSize = 100
        self.fdvtPath = fdvtPath
        self.isLabelingSingleFrame = False
        self.templateFrame = None

        self.fullVideoDialog = None
        self.displayingFullResolution = False
        self.fullResFrame = None
        self.videoSizeSmallToFullMult = 5
        
        self.rewindOnClick = rewindOnClick
        self.rewindStepSize = 500
        self.rewinding = False
        self.rewindCnt = 0
        
#         if self.rewindOnClick:
#             self.eventFilter.oneClickAnnotation = [True, True, True, True]
        
        self.annotations = annotations 
        self.tmpAnnotation = Annotation.Annotation(0, [''])
        self.annotationRoiLabels = []
        self.annoIsOpen = False
        self.metadata = []
        self.confidence = 0
        
        self.usingVideoRunningIndeces = runningIndeces
        
        self.vialROI = vialROI
        
        if type(selectedVial) == int:
            self.selectedVial = [selectedVial]
        else:
            self.selectedVial = selectedVial#3
        self.ui.lbl_vial.setText("<b>vial</b>: {0}".format(self.selectedVial))
                
        
        
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

        self.fileList = self.convertFileList(self.fileList, '.' + videoExtension)
        
        self.vh = VH.VideoHandler(self.fileList, self.changeVideo, 
                               self.selectedVial, startIdx=startIdx,
                               videoExtension='.' + videoExtension,
                               bufferWidth=bufferWidth, 
                               bufferLength=bufferLength)
        
        
        self.updateFrameList(range(2000))
        
        
        
        self.serverAddress = serverAddress
        self.connectedToServer = False
        self.rpcIH = None
        self.fdvt = None
        self.setupFrameView()
        self.bookmark = None

        
        self.configureUI()

        if self.croppedVideo:
            self.setBackground(backgroundPath)
        else:
            self.setBackground()

        self.hud = None
        # self.setupHUD()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showNextFrame)
        self.timerID = None
        
        
        self.ui.cb_trajectory.setChecked(self.showTraject)
        self.showTrajectories(self.showTraject)
            
        self.transferElementsInCollapseContainer()

        self.show()
        cfg.logGUI.info(json.dumps(
                            {"message":'"--------- opened GUI ------------"'})) 
        
        self.setCropCenter(None, None)

        self.firstLoop = True
        self.selectVideo(startIdx)
        # self.startLoop.emit()
        self.stopPlayback()
        

    # def showEvent(self, event):
    #     super(videoTagger, self).showEvent(event)
    #     self.displayFullResolutionFrame()

    @cfg.logClassFunction
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.pb_test.clicked.connect(self.testFunction)
        self.ui.pb_addAnno.clicked.connect(self.addAnno)
        self.ui.pb_eraseAnno.clicked.connect(self.eraseAnno)
        self.ui.pb_connect2server.clicked.connect(self.connectToServer)
        self.ui.pb_check4requests.clicked.connect(self.check4Requests)
        self.ui.cb_edit.toggled.connect(self.editToggle)
        self.ui.cb_anyLabel.toggled.connect(self.anyLabelToggle)
        
        self.ui.sldr_paths.valueChanged.connect(self.selectVideo)
        self.ui.lv_frames.activated.connect(self.selectFrame)
        self.ui.lv_jmp.activated.connect(self.selectFrameJump)
        self.ui.lv_paths.activated.connect(self.selectVideoLV)
        
        self.ui.cb_trajectory.stateChanged.connect(self.showTrajectories)
        
        self.startLoop.connect(self.startVideo)

        
    def transferElementsInCollapseContainer(self):
        self.createVideoDisplayWidget()
        self.createControlWidget()
        self.createDebugWidget()
        self.createProgressWidget()
        
        self.colCont = CC.collapseContainer(width= 1200)        
        self.setCentralWidget(self.colCont)
        
        self.colCont.addWidget(self.glw, "Video View", height=self.videoHeight)# + 30)
        self.colCont.addWidget(self.prevFramesWidget, "frame preview")
        self.colCont.addWidget(self.annoViewCol, "annotation views")
        self.colCont.addWidget(self.controlWidget, "control elements")
        self.colCont.addWidget(self.progressWidget, "progress")
        self.colCont.addWidget(self.ui.tabWidget, "Navigation and Inspection")
        self.colCont.addWidget(self.debugWidget, "debugging ")
        
        
    def createControlWidget(self):
        w = QtGui.QWidget(self)
        self.pb_playback = QtGui.QPushButton(">", w)
        self.pb_playback.clicked.connect(self.playback)
        self.pb_stopPlayback = QtGui.QPushButton("||", w)
        self.pb_stopPlayback.clicked.connect(self.stopPlayback)
        layout = QtGui.QHBoxLayout()
        
        layout.addWidget(self.ui.lbl_vial)
        layout.addWidget(self.ui.lbl_v0)
        layout.addWidget(self.ui.lbl_v1)
        layout.addWidget(self.ui.pb_check4requests)
        layout.addWidget(self.ui.speed_lbl)
        layout.addWidget(self.pb_playback)
        layout.addWidget(self.pb_stopPlayback)
        layout.addWidget(self.ui.cb_trajectory)
        layout.addWidget(self.ui.cb_anyLabel)
        
        w.setLayout(layout)
        w.show()
        w.setFixedHeight(40)
        
        self.controlWidget = w
        
    def createDebugWidget(self):
        w = QtGui.QWidget(self)
        
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.ui.pb_startVideo)
        layout.addWidget(self.ui.pb_stopVideo)
        layout.addWidget(self.ui.pb_connect2server)
        layout.addWidget(self.ui.pb_test)
        layout.addWidget(self.ui.pb_addAnno)
        layout.addWidget(self.ui.pb_eraseAnno)
        layout.addWidget(self.ui.cb_edit)
        
        w.setLayout(layout)
        w.show()
        w.setFixedHeight(40)
        
        self.debugWidget = w
        
    def createProgressWidget(self):
        w = QtGui.QWidget(self)
        
        
        self.progFilter = EF.ProgressFilterObj(self)
        self.ui.progBar.installEventFilter(self.progFilter)        
        
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.ui.progBar)
        
        w.setLayout(layout)
        w.show()
        w.setFixedHeight(30)
        
        self.progressWidget = w
        
        
    def createVideoDisplayWidget(self):
        w = QtGui.QWidget(self)
        
        # height = self.vialRoi[self.selectedVial[0]][1] - \
        #             self.vialRoi[self.selectedVial[0]][0]
                    
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.glw)
        
#         w.setFixedHeight(height + 10)
        
        self.videoDisplayWidget = w
        
    def updateProgress(self):
        path, idx = self.vh.getCurrentKey_idx()
        percent = self.fileList.index(path) / float(len(self.fileList))
        self.ui.progBar.setValue(percent * 100)
        
        
    def jumpToPercent(self, pixel):
        percent = pixel / float(self.ui.progBar.width())
        print percent, pixel
        self.selectVideo(int(percent * len(self.fileList)))
        
        
    @QtCore.Slot()
    def playback(self):
        self.increment = 1
        
        if not self.play:
            self.play = True
            
    @QtCore.Slot()
    def stopPlayback(self):
        self.increment = 0
        
    @cfg.logClassFunction
    def configureUI(self):
        
        self.xFactor = 1 
        self.yFactor = 1 
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        
        self.ui.lbl_v0.setStyleSheet("background-color: rgba(255, 255, 255, 10);")
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
        self.createAnnoViews()
        self.setupLabelMenu()
        
        
        self.ui.pb_check4requests.setVisible(False)
        
        
    def createAnnoView(self, width, height, idx):
        w = QtGui.QWidget(self)
        
        # AnnoView
        av = AV.AnnoView(self, w, vialNo=self.selectedVial, 
                                       annotator=[self.annotations[idx]["annot"]], 
                                       behaviourName=[self.annotations[idx]["behav"]], 
                                       color = self.annotations[idx]["color"], 
                                       geo=QtCore.QRect(10, 5, width, 
                                                       height))        
        av.show()
        av.move(15, 5)     
        self.annoViewList += [av]
        
        # label        
        lbl = QtGui.QLabel(w)
        lbl.setText("{0}: {1}".format(\
                                            self.annotations[idx]["annot"],
                                            self.annotations[idx]["behav"]))
        lbl.move(width + 30, 0)     
        lbl.setStyleSheet("""
        QLabel {{ 
        border-bottom-color: {0};
        border-top: transparent;
        border-left: transparent;
        border-right: transparent;
        border-width : 1.5px;
        border-style:inset; }}""".format(self.annotations[idx]["color"].name()))  
        lbl.adjustSize()           
        self.annoViewLabel += [lbl]
        
        # layout        
#         lay = QtGui.QHBoxLayout()
#         lay.addWidget(av, alignment=QtCore.Qt.AlignHCenter)
#         lay.addWidget(lbl,  alignment=QtCore.Qt.AlignHCenter)
#         
#         w.setLayout(lay)
#         
        w.setFixedHeight(height + 25)
        
        return w
        
    @cfg.logClassFunction
    def createAnnoViews(self):
        self.annoViewList = []
        self.annoViewLabel = []
        
        yPos = 430 
        xPos = 60 
        height = 10
        width = 1000
        
                        
        self.annoViewCol = CC.collapseContainer(width=1100)
        
        for i in range(len(self.annotations)):            
            self.annotations[i]["color"] = QtGui.QColor(self.annotations[i]["color"])
            self.annotations[i]["color"].setAlphaF(0.8)
            
            
            w = self.createAnnoView(width, height, i)
            title = "Annotation View: {a}: {b}".format(\
                                                a=self.annotations[i]['annot'],
                                                b=self.annotations[i]['behav'])
            self.annoViewCol.addWidget(w, title)
            
        for aV in self.annoViewList:
            self.vh.addAnnoView(aV)  
            
            cfg.log.debug("av: {aV}".format(aV=aV))
            
        
        self.prevFramesWidget = self.createPrevFrames(xPos + 125, yPos - (self.prevSize + 20))
            
    
        
    def setupFrameView(self):
        self.frameView = GFDV.GraphicsViewFDV(self.ui.tab_2)
        self.frameView.setGeometry(QtCore.QRect(10, 10, 891, 221))
        self.frameView.setObjectName("frameView")

        self.frameView.registerButtonPressCallback('frames', self.selectVideoTime)
        
        colors = [a['color'] for a in self.annotations]
        self.frameView.setColors(colors)
        
        if self.fdvtPath is not None:
            self.frameView.loadSequence(self.fdvtPath)
            
        self.fdvt = self.frameView.fdvt
            
            
    def createPrevFrames(self, xPos, yPos):
        w = QtGui.QWidget(self)
        layout = QtGui.QHBoxLayout(w)
        
#         xPos = 0
        yPos = 0
        
        size = self.prevSize
        
        self.noPrevFrames = 7
        self.prevFrameLbls = []
#         self.prevConnectHooks = []
        
        for i in range(self.noPrevFrames):
            lbl = QtGui.QLabel(w)
            layout.addWidget(lbl)
            self.prevFrameLbls += [lbl]
            # self.prevFrameLbls[-1].setGeometry(QtCore.QRect(xPos, yPos, size, size))
#             
#             self.prevConnectHooks += [[QtCore.QPoint(xPos + size / 2, yPos + size), 
#                                       QtCore.QPoint(xPos + size / 2, yPos + size + 2)]]
            
            if i == (self.noPrevFrames - 1) / 2:
                self.prevFrameLbls[-1].setLineWidth(3)
                self.prevFrameLbls[-1].setFrameShape(QtGui.QFrame.Box)
            xPos += size + 5

        layout.insertStretch(0)
        layout.insertStretch(-1)
        return w
    
    
    def calculatePrevConnectHooks(self):
        self.prevConnectHooks = []
        l = QtGui.QLabel()
                    
        for lbl in self.prevFrameLbls:
            rect = lbl.geometry()
            xPos = rect.x()
            yPos = rect.y()
            size = rect.width()
            pnt = lbl.mapToGlobal(QtCore.QPoint(xPos, yPos))
            xPos = pnt.x()
            yPos = pnt.y()
            
            self.prevConnectHooks += [[QtCore.QPoint(xPos + size / 2, yPos + size), 
                                      QtCore.QPoint(xPos + size / 2, yPos + size + 2)]]
        
    
#         
#     def paintEvent(self, event):
#         painter = QtGui.QPainter()
#         painter.begin(self) 
#         painter.resetTransform() 
#         painter.setRenderHint(QtGui.QPainter.Antialiasing)
#         
#         pen = QtGui.QPen(QtGui.QColor(100,100,100))
#         pen.setWidth(0.2)
#         
#         painter.setPen(pen)
#         
#         self.calculatePrevConnectHooks()
#         avHooks = self.annoViewList[0].prevConnectHooks
#         midAVHook = len(avHooks) / 2
#         startAVHook = midAVHook - (len(self.prevConnectHooks) - 1) / 2 + \
#                         self.tempIncrement
#                                     
#         for i in range(0,len(self.prevConnectHooks),2):            
#             aVi = startAVHook + i
#             try:
#                 painter.drawLine(self.prevConnectHooks[i][0], self.prevConnectHooks[i][1])   
#                 painter.drawLine(self.prevConnectHooks[i][1], avHooks[aVi][1])            
#                 
#                 painter.drawLine(avHooks[aVi][0], avHooks[aVi][1])  
#             except:
#                 pass
#         painter.end()
        
        
    def convertFileList(self, fileList, videoEnding):
        fl = []
        for f in sorted(fileList):
            if self.usingVideoRunningIndeces:
                fl += [f.split('.')[0] + videoEnding]                
            else:
                fl += ['.'.join(f.split('.')[:2]) + videoEnding]
        
        return fl
        
        
        
    def connectToServer(self):
        if self.serverAddress is not None:
            print "connecting to server .."
            self.rpcIH = RPC.RPCInterfaceHandler(self.serverAddress)
            self.rpcIH.updateFDVTSig.connect(self.setFrameView)
            
            self.connectedToServer = True
            
            if self.fdvt is None:            
                self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
                cfg.log.warning("making new FDVT")
                if self.fdvtPath is not None:
                    self.fdvt.load(self.fdvtPath)
                else:
                    print "importing annotations for display (may take a while)"
                    self.fdvt.importAnnotations(self.convertFileList(self.fileList, 
                                                                     '.bhvr'), 
                                                self.annotations, 
                                                self.selectedVial)
                    print "finished importing annotations"
                
                
                self.setFrameView([self.fdvt.serializeData()])
            
            self.rpcIH.sendLabelFDVT([self.fdvt])
                
            print "connected to server!"
                   
            self.rpcIH.labelFrameSig.connect(self.labelSingleFrame)
            self.rpcIH.newJobSig.connect(self.newJobOnServer)
#             self.ui.pb_check4requests.setVisible(False)
                   
            
    
    @cfg.logClassFunction#Info
    def check4Requests(self):
        self.bookmark = self.vh.getCurrentKey_idx()
        self.rpcIH.getNextJob()
        self.ui.pb_check4requests.setVisible(False)
        
        
    @cfg.logClassFunction#Info
    def jumpToBookmark(self):
        if self.bookmark and self.rewindOnClick:
            self.vh.getFrame(*self.bookmark, checkBuffer=True)
            self.bookmark = None
            self.showNextFrame(0)
        
        
    @QtCore.Slot(list)
    def setFrameView(self, lst):
        fdvt = lst[0]
        # self.ui.frameView.setSerializedSequence(fdvt)
        
        
    @QtCore.Slot()
    def newJobOnServer(self):
        self.ui.pb_check4requests.setVisible(True)
        
        
    @QtCore.Slot(int)
    def labelSingleFrame(self, idx):
        self.isLabelingSingleFrame = True
        self.ui.pb_check4requests.setVisible(False)
        day, hour, minute, frame = self.ui.frameView.fdvTree.idx2key(idx) 
        self.selectVideoTime(day, hour, minute, frame)
        
        
    @cfg.logClassFunction#Info
    def setCropCenter(self, x, y, width=None, height=None, increment=None):
        if width != None and increment != None:
            raise ValueError("width and increment cannot be both specified")
        cfg.log.debug("width: {0}, increment {1}".format(width, increment))
        if width is None:
            width = self.cropWidth
        else:
            self.cropWidth = width

        if height is None:
            height = self.cropHeight
        else:
            self.cropHeight = height


        # self.cropWidth = 64
        # self.cropHeight = 32

        if increment is not None:
            width += (self.cropWidth / float(self.cropWidth + self.cropHeight) * increment / 5)
            if width < 0:
                width = 2

            height += (self.cropHeight / float(self.cropWidth + self.cropHeight) * increment / 5)
            if height < 0:
                height = 2
                
        if x is None:
            self.prevXCrop = slice(None, None)
        else:
            if x-width/2 < 0:
                start = 0
            else:
                start = x-width/2
                
            if self.templateFrame is not None:
                if x+width/2 > self.templateFrame.shape[1] * \
                               self.videoSizeSmallToFullMult:
                    stop = self.templateFrame.shape[1] * \
                           self.videoSizeSmallToFullMult
                else:
                    stop = x+width/2
            else:
                stop =  x+width/2           
            
            self.prevXCrop = slice(start, stop)
            
        if y is None:
            self.prevYCrop = slice(None, None)
        else:
            if y-height/2 < 0:
                start = 0
            else:
                start = y-height/2
                
            if self.templateFrame is not None:
                if y+height/2 > self.templateFrame.shape[0] * \
                           self.videoSizeSmallToFullMult:
                    stop = self.templateFrame.shape[0] * \
                           self.videoSizeSmallToFullMult
                else:
                    stop = y+height/2
            else:
                stop = y+height/2
            
            self.prevYCrop = slice(start, stop)
            
        if x is None or y is None:
            self.cropRect.setPos(-1000, -1000)            
            return
            
        x -= width / 2 
        y -= height / 2
#         
        
            
        self.cropRect.setRect(0,0, width, height)
        self.cropRect.setPos(x, y)
        r = self.cropRect.rect()
            
        cfg.log.debug("after width: {0}, height: {3}, increment {1}, rect {2}".format(width, increment, r, height))
        

    def openNewCropRectangle(self, x, y):
        self.cropX = x
        self.cropY = y
        self.cropWidth = 0
        self.cropHeight = 0
        self.fullVideoDialog.graphicsView.setCursor(QtCore.Qt.ArrowCursor)

    def resizeCropRectangle(self, x, y):
        self.cropWidth = np.abs(x - self.cropX)
        self.cropHeight = np.abs(y - self.cropY)

        if self.cropHeight < 1:
            self.cropHeight = 1

        if self.cropWidth < 1:
            self.cropWidth = 1

        if x >= self.cropX:
            if y >= self.cropY:
                self.setCropCenter(x - self.cropWidth/2.0,
                                   y - self.cropHeight/2.0,
                                   self.cropWidth,
                                   self.cropHeight)
            else:
                self.setCropCenter(x - self.cropWidth/2.0,
                                   self.cropY - self.cropHeight/2.0,
                                   self.cropWidth,
                                   self.cropHeight)
        else:
            if y >= self.cropY:
                self.setCropCenter(self.cropX - self.cropWidth/2.0,
                                   y - self.cropHeight/2.0,
                                   self.cropWidth,
                                   self.cropHeight)
            else:
                self.setCropCenter(self.cropX - self.cropWidth/2.0,
                                   self.cropY - self.cropHeight/2.0,
                                   self.cropWidth,
                                   self.cropHeight)



    def closeNewCropRectangle(self, x, y):
        self.resizeCropRectangle(x, y)
        self.cropIncrement = 0
        if x >= self.cropX:
            if y >= self.cropY:
                center = QtCore.QPoint(x - self.cropWidth/2.0,
                                       y - self.cropHeight/2.0)
            else:
                center = QtCore.QPoint(x - self.cropWidth/2.0,
                                       self.cropY - self.cropHeight/2.0)
        else:
            if y >= self.cropY:
                center = QtCore.QPoint(self.cropX - self.cropWidth/2.0,
                                       y - self.cropHeight/2.0)
            else:
                center = QtCore.QPoint(self.cropX - self.cropWidth/2.0,
                                       self.cropY - self.cropHeight/2.0)

        QtGui.QCursor.setPos(self.fullVideoDialog.graphicsView.mapToGlobal(
                                self.fullVideoDialog.graphicsView.mapFromScene(
                                    center)))

        self.fullVideoDialog.graphicsView.setCursor(QtCore.Qt.CrossCursor)

    def clickInScene(self, x, y):
        if self.inEditMode:
            return

        if not self.isCropRectOpen:
            self.openNewCropRectangle(x,y)
            self.isCropRectOpen = True
        else:
            self.closeNewCropRectangle(x,y)
            self.isCropRectOpen = False

    def moveInScene(self, x, y):
        if self.isCropRectOpen:
            self.resizeCropRectangle(x, y)
        else:
            self.setCropCenter(x, y, increment = self.cropIncrement)
            self.updatePreviewLabels()

    def mouseWheelInScene(self, delta):
        self.cropIncrement -= delta
        
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
        pixmap = QtGui.QPixmap()
        px = QtGui.QPixmap.fromImage(qi)
        
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
            qi = qim2np.array2qimage(img)
            if self.fullResFrame:
                h = self.fullResFrame[1][0][0].shape[0]
                w = self.fullResFrame[1][0][0].shape[1]
                qi = qi.scaled(w, h)

            cfg.log.debug("copy image to pixmap")
            px = QtGui.QPixmap().fromImage(qi)     
            cfg.log.debug("set pixmap")
            lbl.setPixmap(px)
        
    @cfg.logClassFunction
    def updateLabel(self, lbl, p, img):
        print p
        if img is not None:
            self.loadImageIntoLabel(lbl, np.rot90(img))
            
                
        newX = p[0] - 32
        if self.selectedVial is None:
            newY = self.vialROI[0][1] - p[1] - 32
        else:
            newY = self.vialROI[self.selectedVial[0]][1] - p[1] - 32
        
        cfg.log.debug("p= [{2}, {3}] --> x {0}, y {1}".format(newX, newY, p[0], p[1]))
        lbl.setPos(newX,newY)
        
    @cfg.logClassFunction
    def updatePreviewLabel(self, lbl, img, multiplier=1,
                           addToQueryPreviews=False):
#         img = data[0]
        if self.croppedVideo:
            img = np.rot90(img)

        if not self.croppedVideo:
            if multiplier != 1:
                if self.prevYCrop.start:
                    ystart = int(self.prevYCrop.start * multiplier)
                else:
                    ystart = None

                if self.prevYCrop.stop:
                    ystop = int(self.prevYCrop.stop * multiplier)
                else:
                    ystop = None

                if self.prevXCrop.start:
                    xstart = int(self.prevXCrop.start * multiplier)
                else:
                    xstart = None

                if self.prevXCrop.stop:
                    xstop = int(self.prevXCrop.stop * multiplier)
                else:
                    xstop = None

                prevYCrop = slice(ystart, ystop)
                prevXCrop = slice(xstart, xstop)
            else:
                prevYCrop = self.prevYCrop
                prevXCrop = self.prevXCrop

            crop = img[prevYCrop, prevXCrop]
            if np.prod(crop.shape) != 0:
                img = scim.imresize(crop, (self.prevSize,self.prevSize))
            else:
                img = scim.imresize(img, (self.prevSize,self.prevSize))
        else:
            img = scim.imresize(img, (self.prevSize,self.prevSize))
            
        
        qi = qim2np.array2qimage(img)
        
        cfg.log.debug("creating pixmap")
        pixmap = QtGui.QPixmap()
        
        cfg.log.debug("copy image to pixmap")
        px = QtGui.QPixmap.fromImage(qi)
                
        cfg.log.debug("configure label")
        lbl.setScaledContents(False)
        lbl.setPixmap(px)
                
        cfg.log.debug("update label")
        lbl.update()

        if addToQueryPreviews:
            self.queryPreviews += [copy.copy(img)]
        
        
    @cfg.logClassFunction
    def updateMainLabel(self, lbl, img):
        self.templateFrame = img


        if self.fullResFrame:
            h = self.fullResFrame[1][0][0].shape[0]
            w = self.fullResFrame[1][0][0].shape[1]
        else:
            h = img.shape[0]
            w = img.shape[1]

        if self.sceneRect != QtCore.QRectF(0, 0, w,h):
            cfg.log.debug("changing background")
            # self.videoView.setGeometry(QtCore.QRect(380, 10, w, h))#1920/2, 1080/2))
            self.videoView.setGeometry(QtCore.QRect(380, 10, 360, 203))#1920/2, 1080/2))
            self.videoView.fitInView(QtCore.QRect(380, 10, w, h))#1920/2, 1080/2))
            self.videoScene.setSceneRect(QtCore.QRectF(0, 0, w,h))            
            self.videoScene.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.black))
            lbl.setPos(0,0)
            self.sceneRect = QtCore.QRectF(0, 0, w,h)
                    
        self.loadImageIntoLabel(lbl, img)
        
        
    @cfg.logClassFunction
    def positionAnnotationRoi(self, rois):
        while len(self.annotationRoiLabels) < len(rois):
            rect = QtCore.QRectF(0, 0, 64, 64)

            # anRect

            anRect = BehaviourRectItem(self.menu,
                                              self.registerLastLabelRectContext,
                                              '',
                                              rectChangedCallback=self.labelRectChangedSlot)
            anRect.setRect(rect)
            # anRect.setColor(penCol)
            anRect.setResizeBoxColor(QtGui.QColor(255,255,255,50))
            anRect.setupInfoTextItem(fontSize=12)
            self.videoScene.addItem(anRect)
            self.annotationRoiLabels += [anRect]

            if not self.inEditMode:
                anRect.deactivate()
            
        usedRoi = 0
        
        cfg.log.debug("Rois: {0}".format(rois))
        for i in range(len(rois)):        
            x1, y1, x2, y2 = rois[i][0]
            color = rois[i][1]['color']
            lbl = rois[i][2]
            
            width = x2 - x1
            height = y2 - y1
            
            cfg.log.debug("setting rect to: {0} {1} {2} {3}".format(x1,
                                                                   y1,
                                                                   width ,
                                                                   height))
            self.annotationRoiLabels[i].rectChangedCallback = None
            self.annotationRoiLabels[i].setRect(0,0, width, height)
            self.annotationRoiLabels[i].setPos(x1, y1)
            self.annotationRoiLabels[i].setColor(color)
            self.annotationRoiLabels[i].setInfoString("{a}:\n{b}".format(
                                                    a=rois[i][1]['annot'],
                                                    b=lbl))
            self.annotationRoiLabels[i].setAnnotationLabel(rois[i][1]['annot'],
                                                           lbl)
            self.annotationRoiLabels[i].rectChangedCallback = \
                                                    self.labelRectChangedSlot
             
            cfg.log.debug("set rect to: {0}".format(self.annotationRoiLabels[i].rect()))
            usedRoi = i + 1
            
            
        # move unused rects out of sight
        for k in range(usedRoi, len(self.annotationRoiLabels)):
            self.annotationRoiLabels[k].rectChangedCallback = None
            self.annotationRoiLabels[k].setRect(0,0, 0, 0)
            self.annotationRoiLabels[k].setPos(-10, -10)
            
        
    
    @cfg.logClassFunction
    def showTempFrame(self, increment):
        self.nonTempIncrement = self.increment
        self.increment = 0
        self.tempIncrement = increment
        self.showNextFrame(self.tempIncrement, checkBuffer=False)
        self.update()
        
        
    @cfg.logClassFunction
    def resetTempFrame(self):
        self.increment = self.nonTempIncrement
        self.showNextFrame(-self.tempIncrement, checkBuffer=False)
        self.tempIncrement = 0
        self.update()


    def displayFullResolutionFrame(self):
        if not self.croppedVideo:
            self.displayingFullResolution = True
            self.fullResFrame = self.vh.getFullResolutionFrame()
            self.videoSizeSmallToFullMult = self.fullResFrame[1][0][0].shape[0] / \
                                        float(self.frames[0][1][0][0].shape[0])

            self.displayFrame(self.fullResFrame, 0)

        if self.fullVideoDialog is None:
            # self.fullVideoDialog = FVD(self, self.prevFramesWidget)
            self.fullVideoDialog = FVD(self, self.createPrevFrames(0, 0))
            self.fullVideoDialog.setScene(self.videoScene)
            self.setupHUD()
            self.fullVideoDialog.show()
            self.dialogShortCutFilter = EF.shortcutHandler(self.fullVideoDialog, self, **self.filterObjArgs)
            # self.fullVideoDialog.installEventFilter(self.dialogShortCutFilter)
            self.deactivateEditMode()
        else:
            self.fullVideoDialog.show()



    def displayFrame(self, frame, selectedVial):
        sv = selectedVial
        if not self.croppedVideo:
            self.updateMainLabel(self.lbl_v0, frame[1][sv][0])
        else:
            self.updateLabel(self.lbl_v0, frame[0][sv], frame[1][0][0])


    def displayAnnotationROIs(self, anno, selectedVial):
        # place annotation roi
        sv = selectedVial
        self.tmpAnnotation.setFrameList([anno])

        rois = []
        for i in range(len(self.annotations)):
            filt = Annotation.AnnotationFilter(None,
                                            [self.annotations[i]["annot"]],
                                            [self.annotations[i]["behav"]])
            tmpAnno  = self.tmpAnnotation.filterFrameList(
                                    filt,
                                    exactMatch=False)

            if tmpAnno.frameList[0][sv] == None:
                continue

            # print tmpAnno.frameList[0][sv]

            bb = Annotation.getPropertyFromFrameAnno(tmpAnno.frameList[0][sv],
                                                     "boundingBox")
            lbls = Annotation.getExactBehavioursFromFrameAnno(
                                                    tmpAnno.frameList[0][sv])

            for b, l in zip(bb, lbls):
                # ensure that annotations without boundingbox do not mess up
                # anything
                if None in b:
                    continue
                rois += [[b, self.annotations[i], l]]

        self.positionAnnotationRoi(rois)


    def displayTrajectory(self, increment, selectedVial, offset=5):
        sv = selectedVial
        # showing trajectory #
        if increment == 0:
            prevIncrement = 2
        else:
            prevIncrement = increment

        self.prevFrames = []
        for i in range(self.trajNo):
            self.prevFrames += [self.vh.getTempFrame(prevIncrement * (i - offset),
                                                 posOnly=True)]

        for i in range(len(self.prevFrames)-1, -1, -1):
            frame = self.prevFrames[i]
            self.updateLabel(self.trajLabels[i][0], frame[0][sv], None)


    def updatePreviewLabels(self, frameSwitch=False):
        offset = (len(self.prevFrameLbls) - 1) / 2
        self.prevFrames = []
        multipliers = []

        for i in range(len(self.prevFrameLbls)):
            self.prevFrames += [self.vh.getTempFrame(i - offset)]
            multipliers += [1.0 / self.videoSizeSmallToFullMult]

        if self.displayingFullResolution:
            self.prevFrames[offset] = self.fullResFrame
            multipliers[offset] = 1

        for i in range(len(self.prevFrameLbls)):
            if frameSwitch\
            and self.postLabelQuery and self.annoIsOpen\
            and i == (len(self.prevFrameLbls) - 1) / 2:
                addToQueryPreviews = True
            else:
                addToQueryPreviews = False

            self.updatePreviewLabel(self.prevFrameLbls[i],
                                    self.prevFrames[i][1][0][0],
                                    multipliers[i],
                                    addToQueryPreviews)

    
    @cfg.logClassFunction
    def showNextFrame(self, increment=None, checkBuffer=True):
        #~ logGUI.debug(json.dumps({"increment":increment, 
                                 #~ "checkBuffer":checkBuffer}))

        self.displayingFullResolution = False

        if self.annoIsOpen:
            if np.abs(increment) > 1:
                # set increment to either 1 or -1
                increment /= int(np.abs(increment))
        
        if increment is None:
            increment = self.increment
            
            
        self.rewindIncrement()
        self.frames = []    
        
        if self.selectedVial is None:
            sv = 0            
        else:
            sv = self.selectedVial[0]
        
        offset = 5  
        
        cfg.log.debug("increment: {0}, checkBuffer: {1}".format(increment, checkBuffer))
        
        if increment >= 0:
            self.frames += [self.vh.getNextFrame(increment, doBufferCheck=checkBuffer, 
                                                 unbuffered=False)]
        elif increment < 0:
            self.frames += [self.vh.getPrevFrame(-increment, doBufferCheck=checkBuffer,
                                                 unbuffered=False)]
        else:
            self.frames += [self.vh.getCurrentFrame()]
            increment = 8
            offset = (self.trajNo / 2) 
        
        frame = self.frames[0]
        anno = frame[2]

        self.displayFrame(frame, sv)
        self.displayAnnotationROIs(anno, sv)
        self.displayTrajectory(increment, sv, offset)

        # showing previews #
        self.updatePreviewLabels(frameSwitch=(increment != 0))
        self.vh.updateAnnotationProperties(self.getMetadata())

        frameNo = self.vh.getCurrentFrameNo()
        self.ui.lbl_v1.setText("<b> frame no</b>: {0}".format(frameNo))

        self.updateHUD()
             


        
    @cfg.logClassFunction
    def jumpToFrame(self, vE, lbl, p, frameNo):    
        
        frame = vE.vs.get_frame_no(frameNo)
        
        img = frame.ndarray() #* 255
        
        qi = np2qimage(img)
        pixmap = QtGui.QPixmap()
        px = QtGui.QPixmap.fromImage(qi)
        
        lblOrigin = self.ui.label.pos()
        
        newX = lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
                    
        lbl.move(newX,newY)
        
        lbl.setScaledContents(True)
        lbl.setPixmap(px)
        
        lbl.update()
        
        return img


    ##### MOVEABLE RECT
    def deleteLeftLabels(self):
        annotator = self.lastLabelRectContext.annotator
        behaviour = self.lastLabelRectContext.behaviour
        labelledFrames = self.vh.eraseAnnotationSequence(self.selectedVial,
                                                         annotator,
                                                         behaviour,
                                                         direction='left')

        labelledFrames = (labelledFrames[0], labelledFrames[1], -1)
        self.convertLabelListAndReply(labelledFrames)

    def deleteRightLabels(self):
        annotator = self.lastLabelRectContext.annotator
        behaviour = self.lastLabelRectContext.behaviour
        labelledFrames = self.vh.eraseAnnotationSequence(self.selectedVial,
                                                         annotator,
                                                         behaviour,
                                                         direction='right')

        labelledFrames = (labelledFrames[0], labelledFrames[1], -1)
        self.convertLabelListAndReply(labelledFrames)

    def deleteAllLabels(self):
        annotator = self.lastLabelRectContext.annotator
        behaviour = self.lastLabelRectContext.behaviour
        labelledFrames = self.vh.eraseAnnotationSequence(self.selectedVial,
                                                         annotator,
                                                         behaviour,
                                                         direction='both')

        labelledFrames = (labelledFrames[0], labelledFrames[1], -1)
        self.convertLabelListAndReply(labelledFrames)

    def deleteLabel(self):
        annotator = self.lastLabelRectContext.annotator
        behaviour = self.lastLabelRectContext.behaviour
        labelledFrames = self.vh.eraseAnnotationCurrentFrame(self.selectedVial,
                                                             annotator,
                                                             behaviour)

        labelledFrames = (labelledFrames[0], labelledFrames[1], -1)
        self.convertLabelListAndReply(labelledFrames)


    def lineEditChanged(self):
        self.menu.hide()
        behaviourNew = self.cle.text()

        behaviourOld = self.lastLabelRectContext.behaviour
        annotatorOld = self.lastLabelRectContext.annotator

        self.editAnnoLabel(annotatorOld, behaviourOld,
                           annotatorOld, behaviourNew)

    def registerLastLabelRectContext(self, labelRect):
        self.lastLabelRectContext = labelRect

    def labelRectChangedSlot(self, activeRect):
        self.contentChanged = True
        if self.inEditMode \
        and activeRect.annotator is not None\
        and activeRect.behaviour is not None:
            roi = [activeRect.pos().x(),
                   activeRect.pos().y()]
            roi += [roi[0] + activeRect.boundingRect().width()]
            roi += [roi[1] + activeRect.boundingRect().height()]

            self.editAnnoROI(activeRect.annotator,
                             activeRect.behaviour,
                             roi)

    def setupLabelMenu(self):
        wa = QtGui.QWidgetAction(self)
        self.cle = MR.ContextLineEdit(wa, self)

        labels = []

        for i in range(len(self.annotations)):
            labels += ["{b}".format(b=self.annotations[i]['behav'])]

        self.cle.setModel(labels)

        wa.setDefaultWidget(self.cle)

        self.menu = QtGui.QMenu(self)
        self.menu.addAction(wa)
        delAction = self.menu.addAction("delete (this frame)")
        delAllAction = self.menu.addAction("delete (all)")
        delRightAction = self.menu.addAction("delete (this and all to right)")
        delLeftAction = self.menu.addAction("delete (this and all to left)")

        wa.triggered.connect(self.lineEditChanged)
        delAction.triggered.connect(self.deleteLabel)
        delAllAction.triggered.connect(self.deleteAllLabels)
        delRightAction.triggered.connect(self.deleteRightLabels)
        delLeftAction.triggered.connect(self.deleteLeftLabels)

    def setupLabelRequestMenu(self):
        wa = QtGui.QWidgetAction(self)
        self.clre = MR.ContextLineEdit(wa, self)

        labels = []

        for i in range(len(self.annotations)):
            labels += ["{b}".format(b=self.annotations[i]['behav'])]

        self.clre.setModel(labels)

        wa.setDefaultWidget(self.clre)

        self.requestLabelMenu = QtGui.QMenu(self)
        self.requestLabelMenu.addAction(wa)
        # delAction = self.requestLabelMenu.addAction("delete (this frame)")
        # delAllAction = self.requestLabelMenu.addAction("delete (all)")
        # delRightAction = self.requestLabelMenu.addAction("delete (this and all to right)")
        # delLeftAction = self.requestLabelMenu.addAction("delete (this and all to left)")

        wa.triggered.connect(self.lineEditChanged)
        # delAction.triggered.connect(self.deleteLabel)
        # delAllAction.triggered.connect(self.deleteAllLabels)
        # delRightAction.triggered.connect(self.deleteRightLabels)
        # delLeftAction.triggered.connect(self.deleteLeftLabels)

    def deactivateAllLabelRects(self):
        for lr in self.annotationRoiLabels:
            if lr:
                lr.deactivate()

    def activateAllLabelRects(self):
        for lr in self.annotationRoiLabels:
            if lr:
                lr.activate()

    def activateEditMode(self):
        self.activateAllLabelRects()
        self.inEditMode = True
        self.isCropRectOpen = False
        self.cropRect.setVisible(False)
        if self.fullVideoDialog is not None:
            self.fullVideoDialog.setMode('edit-mode',
                                         QtGui.QColor(255, 50, 50))
            self.fullVideoDialog.graphicsView.setCursor(QtCore.Qt.ArrowCursor)

        self.stopVideo()

    def deactivateEditMode(self):
        self.deactivateAllLabelRects()
        self.inEditMode = False
        self.cropRect.setVisible(True)
        self.increment = 0

        if self.fullVideoDialog is not None:
            self.fullVideoDialog.setMode('additive mode',
                                         QtGui.QColor(0, 0, 0))
            self.fullVideoDialog.graphicsView.setCursor(QtCore.Qt.CrossCursor)

        if not self.play:
            self.startVideo()

    def activatePostLabelQuery(self):
        self.postLabelQuery = True

    def deactivatePostLabelQuery(self):
        self.postLabelQuery = False

    def toggleEditModeCheckbox(self):
        self.ui.cb_edit.setChecked(not self.ui.cb_edit.isChecked())

    def editToggle(self, state):
        if state:
            self.activateEditMode()
        else:
            self.deactivateEditMode()

    def anyLabelToggle(self, state):
        if state:
            self.activatePostLabelQuery()
        else:
            self.deactivatePosLabelQuery()

    def addCropRect(self):
        geo = QtCore.QRectF(0, 0, 64, 64)
        penCol = QtGui.QColor()
        penCol.setHsv(50, 255, 255, 255)
        self.cropRect = self.videoScene.addRect(geo, QtGui.QPen(penCol))

    @cfg.logClassFunction
    def setBackground(self, path=None):
        
        if path:        
            a = plt.imread(path) * 255
            
            # crop and rotate background image to show only one vial
            rng = slice(*self.vialROI[self.selectedVial[0]])
            a = np.rot90(a[:, rng]).astype(np.uint32)
            
            h = a.shape[0]
            w = a.shape[1]
            
            # grey conversion
            b = a[:,:,0] * 0.2126 + a[:,:,1] * 0.7152 + a[:,:,2] * 0.0722
            a[:,:,0] = b
            a[:,:,1] = b
            a[:,:,2] = b
            
            im = np2qimage(a).convertToFormat(QtGui.QImage.Format_RGB32,
                                              QtCore.Qt.MonoOnly)
            
            pixmap = QtGui.QPixmap()
            px = QtGui.QPixmap.fromImage(im)
            
        else:
            h = 250
            w = 0            
            
        
        self.sceneRect = QtCore.QRectF(0, 0, w,h)
        
        self.videoView = QtGui.QGraphicsView(self)        
        self.videoView.setFrameStyle(QtGui.QFrame.NoFrame)
        self.videoView.setGeometry(QtCore.QRect(10, 10, w, h))#1920/2, 1080/2))
        self.videoView.setGeometry(QtCore.QRect(150, 10, w, h))#1920/2, 1080/2))
        self.videoScene = QtGui.QGraphicsScene(self)
        self.videoScene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.videoScene.setSceneRect(self.sceneRect)#1920, 1080))
        self.videoScene.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.black))
        
        self.videoView.setScene(self.videoScene)
            
            
        if path:
            self.bgImg = QtGui.QGraphicsPixmapItem(px)
        else:
            self.bgImg = QtGui.QGraphicsPixmapItem()
              
              
        self.videoScene.addItem(self.bgImg)   
        self.bgImg.setPos(0,0)     
        
        
        self.lbl_v0 = QtGui.QGraphicsPixmapItem()
        self.lbl_v1 = QtGui.QGraphicsPixmapItem()
        self.lbl_v2 = QtGui.QGraphicsPixmapItem()
        self.lbl_v3 = QtGui.QGraphicsPixmapItem()   
         
        self.videoScene.addItem(self.lbl_v0)   
        self.videoScene.addItem(self.lbl_v1)   
        self.videoScene.addItem(self.lbl_v2)   
        self.videoScene.addItem(self.lbl_v3)   
        
        # fmt = QtOpenGL.QGLFormat()
        # fmt.setAlpha(True)
        # fmt.setOverlay(True)
        # fmt.setDoubleBuffer(True);
        # fmt.setDirectRendering(True);
        #
        #
        self.glw = QtGui.QWidget(self)#QtOpenGL.QGLWidget(fmt)
        # self.glw.setFixedHeight(h + 50)
        
        
#         glw.setMouseTracking(True)
        
        self.videoView.setViewport(self.glw)
        self.videoView.viewport().setCursor(QtCore.Qt.BlankCursor)
        self.videoView.setGeometry(QtCore.QRect(0, 0, w + 200, h+ 50))#1920/2, 1080/2))
        self.videoView.show()
#         self.videoView.fitInView(self.bgImg, QtCore.Qt.KeepAspectRatio)
        self.videoView.fitInView(QtCore.QRect(0, 0, w, h + 50),
                                 QtCore.Qt.KeepAspectRatio)
        
#         self.videoView.installEventFilter(self.mouseEventFilter)
        self.videoView.setMouseTracking(True)
#         self.lbl_v0.setAcceptHoverEvents(True)
#         self.videoScene.setAcceptHoverEvents(True)
        self.videoScene.installEventFilter(self.mouseEventFilter)

        self.videoHeight = h + 50
        self.addCropRect()
        self.videoView.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

    def setupHUD(self):
        if self.fullVideoDialog:
            self.fullVideoDialog.setAnnotator("")
            self.fullVideoDialog.setBehaviour("")

    def updateHUD(self, annotator=None, behaviour=None):
        if self.fullVideoDialog:
            frameNo = self.vh.getCurrentFrameNo()
            self.fullVideoDialog.setFrame(str(frameNo))
            filename = self.vh.posPath
            self.fullVideoDialog.setFile(filename)

            self.fullVideoDialog.setSpeed(self.increment)

            if annotator is not None:
                if annotator == "":
                    self.fullVideoDialog.setAnnotator("")
                else:
                    self.fullVideoDialog.setAnnotator("Annotator: " + annotator)

            if behaviour is not None:
                if behaviour == "":
                    self.fullVideoDialog.setBehaviour("")
                else:
                    color = None
                    for i in range(len(self.annotations)):
                        if self.annotations[i]["annot"] == annotator\
                        and self.annotations[i]['behav'] == behaviour:
                            color = self.annotations[i]["color"]

                    self.fullVideoDialog.setBehaviour("Behaviour: "+behaviour,
                                                      color=color)


    def openFDV(self):
        OD.FDVShowDialog.getSelection(self.fullVideoDialog.centralWidget(),
                                      self.frameView)

    def openKeySettings(self):
        filterObjArgs = OD.ControlsSettingDialog.getSelection(self.fullVideoDialog.centralWidget(),
                                              self.dialogShortCutFilter.keyMap,
                                              self.dialogShortCutFilter.stepSize)

        self.dialogShortCutFilter.setKeyMap(filterObjArgs['keyMap'])
        self.dialogShortCutFilter.setStepSize(filterObjArgs['stepSize'])
        self.exportSettings()


    @QtCore.Slot()
    def startVideo(self):
        self.play = True

        
        cfg.log.debug("start Video")
        self.showNextFrame(0)
        self.vh.loadProgressive = True
        
        self.stop = False
        self.increment = 0
        skipCnt = 0 # counts how often process events were skipped
        
        
        cfg.logGUI.info('"--------- start mainloop ------------"')
         
        while not self.stop:
            #cfg.log.info("begin   --------------------------------------- main loop")
            self.vh.loadProgressive = True
             
            dieTime = QtCore.QTime.currentTime().addMSecs(33)
                         
            if self.play:            
                self.showNextFrame(self.increment)
                self.ui.speed_lbl.setText("<b>speed</b>: {0}x".format(\
                                                                self.increment))
                self.updateProgress()
#                 if self.increment == 0:
#                     self.play = False


            if not(QtCore.QTime.currentTime() < dieTime):
                cfg.log.info("no realtime display!!! " +
                                cfg.Back.BLUE + 
                                "mainloop overflow before processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QtCore.QTime.currentTime())))
                
            elif(QtCore.QTime.currentTime() < dieTime.addMSecs(15)):
                # frameNo = self.vh.getCurrentFrameNo()
                # self.ui.lbl_v1.setText("<b> frame no</b>: {0}".format(frameNo))
                
                if self.rpcIH is not None:
                    self.rpcIH.checkForNewJob()
             
#             cfg.log.debug("---------------------------------------- while loop() - begin")

            if not (QtCore.QTime.currentTime() < dieTime):                
                skipCnt += 1
            else:
                skipCnt = 0
                
            if(QtCore.QTime.currentTime() < dieTime) or (skipCnt > 10):
                skipCnt = 0
#                 cfg.log.debug("processEvents() - begin")
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents, QtCore.QTime.currentTime().msecsTo(dieTime))
#                 cfg.log.debug("processEvents() - end")

                 
            if not(QtCore.QTime.currentTime() < (dieTime.addMSecs(1))):
                cfg.log.debug("no realtime display!!! " +
                                cfg.Back.YELLOW + 
                                "mainloop overflow after processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QtCore.QTime.currentTime())))

            # if self.firstLoop:
            #     self.firstLoop = False
            #     self.deactivateEditMode()
                # self.displayFullResolutionFrame()
#             else:
#                 self.thread().msleep(QtCore.QTime.currentTime().msecsTo(dieTime))
                
        self.vh.loadProgressive = False
        cfg.logGUI.info('"--------- stopped mainloop ------------"')
        cfg.log.info('"--------- stopped mainloop ------------"')
        
#     @cfg.logClassFunction
#     def providePosList(self, path, ending=None):
#         if not ending:
#             ending = '.pos.npy'
#         
#         fileList  = []
#         posList = []
#         cfg.log.debug("scaning files...")
#         for root,  dirs,  files in os.walk(path):
#             for f in files:
#                 if f.endswith(ending):
#                     path = root + '/' + f
#                     fileList.append(path)
#                     
#         self.fileList = sorted(fileList)
#         cfg.log.debug("scaning files done")
#         return self.fileList
        
        
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
        self.play = False
        self.vh.loadProgressive = False
        
    @cfg.logClassFunction
    def generatePatchVideoPath(self, posPath, vialNo):
        """
        strips pos path off its postfix and appends it with the vial + video
        format postfixq
        """
        return posPath.split('.pos')[0] + '.v{0}.{1}'.format(vialNo, 
                                                            self.videoExtension)
                                                            
    @cfg.logClassFunction
    def setVideo(self, idx):
        self.ui.lv_paths.setCurrentIndex(self.lm.index(idx,0))
        self.ui.sldr_paths.setSliderPosition(idx)
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
        self.vh.setFrameIdx(idx)
        self.showNextFrame(1)
        self.ui.lv_frames.setCurrentIndex(self.frameList.index(idx,0))
            

    @cfg.logClassFunction
    def selectVideo(self, idx, frame=0):
        self.idx = idx
        self.vh.getFrame(sorted(self.fileList)[idx], frame)
        self.ui.lbl_v0.setText("<b>current file</b>: {0}".format( \
                                                    sorted(self.fileList)[idx]))
        
        self.increment = 0 
        self.showNextFrame(0)
        self.startLoop.emit()
        
    @cfg.logClassFunctionInfo
    def selectVideoTime(self, day, hour, minute, frame, data=None):
        
        print "selectVideoTime: clicked on day {0}, hour {1}, minute {2}, frame {3}, data {4}".format(
                                                    day, hour, minute, frame, data)
        if len(self.fileList) == 1:
            idx = 0
            minutes = day * (24 * 60) + hour * 60  + minute
            frame += minutes * 30 * 60
        elif self.usingVideoRunningIndeces:
            idx = day * (24 * 60) + hour * 60 + minute
            idx -= 1
        else:
            dataStr = "{day}.{hour}-{minute}".format(day=day, hour=hour, 
                                                     minute=minute)
            idx = [idx for idx in range(len(self.fileList))  
                            if dataStr in self.fileList[idx]]
            if len(idx) == 0:
                raise ValueError("dataStr retrieved no result")
            if len(idx) > 1:
                raise ValueError("dataStr retrieved ambigous result")
            
            idx = idx[0]

        self.selectVideo(idx, frame)

    def selectVideoKeyIdx(self, key, idx):
        keyidx = self.lm.listdata.index(key)
        frame = idx

        self.selectVideo(idx, frame)
                
        
    @cfg.logClassFunctionInfo
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
    def loadNewVideo(self):
        self.videoList[self.fileList[0]] = DL.VideoLoader(self.fileList[0])
        
    @cfg.logClassFunction
    def showTrajectories(self, state):
        self.showTraject = bool(state)        
        
        if self.showTraject:
            self.trajNo = 50
        else:
            self.trajNo = 0
            
        if self.trajLabels != []:
            for i in range(len(self.trajLabels)):
                for k in range(len(self.trajLabels[i])):
                    self.videoScene.removeItem(self.trajLabels[i].pop())
                    
        self.trajLabels = []
        for i in range(self.trajNo):
            lbl = []
            for k in range(1):
                #l = QLabel(self)
                geo = QtCore.QRectF(0, 0, 64, 64)
                penCol = QtGui.QColor()
                penCol.setHsv(i / 50.0 * 255, 255, 150, 50)
                lbl += [self.videoScene.addRect(geo, QtGui.QPen(penCol))]
            self.trajLabels += [lbl]
    
    @cfg.logClassFunction
    @QtCore.Slot(list)
    def addVideo(self, videoList):
        cfg.log.debug("slot")
        self.videoList += videoList
        
        cfg.log.debug("{0}".format(self.videoList))
        
    @cfg.logClassFunction
    @QtCore.Slot(str)
    def changeVideo(self, filePath):
        cfg.log.debug("Change video to {0}".format(filePath))
        
        self.ui.lbl_v0.setText("current file: {0}".format(filePath))
        
        cfg.log.debug("end")
        
    @cfg.logClassFunction
    def saveAll(self):
        cfg.logGUI.info('""')
        self.vh.saveAll()
        if type(self.fdvt) == FDV.FrameDataVisualizationTreeBehaviour:
            self.fdvt.save(self.fdvtPath) 


        
    def testFunction(self):
        cfg.log.debug("testFunction")
        #
        # self.addNewAnnotation(Annotation.AnnotationFilter([0],
        #                                     ["Peter"],
        #                                     ["shit"]),
        #                      QtGui.QColor(0,0,0))
        self.displayFullResolutionFrame()


    ### new stuff

    def addNewAnnotation(self, af, color):
        self.annotations += [{'annot': af.annotators,
                              'behav': af.behaviours,
                              'color': color}]

        height = 10
        width = 1000
        i = len(self.annotations) - 1

        w = self.createAnnoView(width, height, i)
        title = "Annotation View: {a}: {b}".format(\
                                            a=self.annotations[i]['annot'],
                                            b=self.annotations[i]['behav'])
        self.annoViewCol.addWidget(w, title)


#         self.increment = 40
#         self.rpcIH.getNextJob()
        
#     def initRewind(self):        
#         self.rewinding = True
#         ## set filterObj to normal playback
#         self.eventFilter.swapToConstantSpeed(1)
#         ## rewind
#         self.rewindCnt = 0
#         self.increment = 1
#         self.ui.progBar.setMaximum(self.rewindStepSize)
#         self.ui.progBar.setValue(0)
#         self.ui.progBar.setVisible(True)        
#         self.showNextFrame(-self.rewindStepSize)
#         self.startVideo()    
#         
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
            xStart = self.prevXCrop.start
        else:
            xStart= None
            
        if self.prevYCrop.start is not None:
            yStart = self.prevYCrop.start
        else:
            yStart = None
            
        if self.prevXCrop.stop is not None:
            xStop = self.prevXCrop.stop
        else:
            xStop = None
        
        if self.prevYCrop.stop is not None:
            yStop = self.prevYCrop.stop
        else:
            yStop = None
            
        metadata =           {"confidence": self.confidence,
                              "boundingBox":[xStart, 
                                             yStart,
                                             xStop,
                                             yStop]}
        
        return metadata

    def removeIDFromBehaviour(self, filt):
        for i in range(len(filt.behaviours)):
            if len(filt.behaviours[i].split("_")) > 1:
                try:
                    test = int(filt.behaviours[i].split("_")[-1])
                    filt.behaviours[i] = "_".join(filt.behaviours[i].split("_")[:-1])
                except ValueError:
                    pass

        return filt

    def convertLabelListAndReply(self, labelledFrames):
        """
        Args
            labelledFrames (output from vh.addAnnotation or vh.eraseAnnotation

        """
        if not self.fdvt:
            return

        frames = labelledFrames[0]
        filt = labelledFrames[1]

        filt = self.removeIDFromBehaviour(filt)

        increment = labelledFrames[2]

        if self.fdvt.meta['not-initialized']:
            print "aiwodfjawoigfwghoaifai"
            curFile = self.fileList[self.idx]
            self.fdvt.importAnnotation(self.vh.annoDict[curFile].annotation)
            for a in self.annotations:
                newFilt = Annotation.AnnotationFilter(self.selectedVial,
                                                   [a['annot']],
                                                   [a['behav']])
                self.fdvt.addNewClass(newFilt)

            self.frameView.loadFDVT(self.fdvt)

        deltaVector = []
        for key in frames.keys():
            # treeKey = FDV.filename2Time(key)
            # day = treeKey[0]
            # hour = treeKey[1]
            # minute = treeKey[2]
            for frame in frames[key]:
                # deltaVector += [[self.fdvt.key2idx(day, hour, minute, frame),
                #                 self.fdvt.getAnnotationFilterCode(filt)]]
                dv = self.fdvt.getDeltaValue(key, frame, filt, increment)
                if dv[1] is None:
                    self.fdvt.addNewClass(filt)
                    colors = [a['color'] for a in self.annotations]
                    self.frameView.setColors(colors)
                    dv = self.fdvt.getDeltaValue(key, frame, filt, increment)
                deltaVector += [dv]


        if type(self.fdvt) == FDV.FrameDataVisualizationTreeBehaviour:
            self.fdvt.insertDeltaVector(deltaVector)
            self.frameView.updateDisplay(useCurrentPos=True)


        if self.rpcIH:
            self.rpcIH.sendReply([deltaVector])
            self.isLabelingSingleFrame = False
            self.jumpToBookmark()

    def addNewBehaviourClass(self, selectedBehaviour, color):
        self.annotations += [{'behav': selectedBehaviour,
                              'annot': self.annotations[0]['annot'],
                              'color': color}]

        self.exportSettings()


    def queryForLabel(self):
        # self.setupLabelRequestMenu()
        # cfg.log.info("---------- {0}".format( self.mapFromGlobal(QtGui.QCursor.pos())))
        # self.requestLabelMenu.exec_(self.mapFromGlobal(QtGui.QCursor.pos()))

        strList = [x['behav'] for x in self.annotations]


        self.dialogShortCutFilter.deactivateShortcuts()
        selectedBehaviour = OD.ClassSelectDialog.getLabel(
                                        self.fullVideoDialog.centralWidget(),
                                        strList,
                                        self.queryPreviews)

        self.dialogShortCutFilter.activateShortcuts()

        print selectedBehaviour
        if selectedBehaviour is None:
            ## delete label
            pass
        else:
            for i , elem in enumerate(self.annotations):
                if elem['behav'] == selectedBehaviour:
                    newAnnotator = elem['annot']
                    newBehaviour = elem['behav']
                    self.editAnnoLabel(self.annotations[0]['annot'], "unknown",
                                       newAnnotator, newBehaviour)

                    return selectedBehaviour

            color = OD.ColorRequestDialog.getColor(
                                self.fullVideoDialog.centralWidget(),
                                ("Are you sure you want to create a " +
                                "new class called <b>{0}</b>? If yes, " +
                                "please select a color. Otherwise " +
                                "press ESC.").format(selectedBehaviour))
            if color is None:
                self.vh.eraseAnnotationSequence(self.selectedVial,
                                                self.annotations[0]['annot'],
                                                "unknown", direction='both')
                return None
            else:
                self.addNewBehaviourClass(selectedBehaviour, color)
                self.editAnnoLabel(self.annotations[0]['annot'], "unknown",
                                   self.annotations[0]['annot'],
                                   selectedBehaviour)

        return selectedBehaviour


#     @cfg.logClassFunction
    def addAnno(self, annotator="peter", behaviour="just testing",
                confidence=1, oneClickAnnotation=False):        
        cfg.logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour,
                                "confidence": confidence}))

        if not self.annoIsOpen:
            self.confidence = confidence
            self.queryPreviews = []

        labelledFrames = self.vh.addAnnotation(self.selectedVial, annotator, 
                              behaviour, metadata=self.getMetadata())
            
        if oneClickAnnotation:                
            labelledFrames = self.vh.addAnnotation(self.selectedVial, annotator, 
                              behaviour, metadata=self.getMetadata())
                
        self.annoIsOpen = self.vh.annoAltStart is not None #not self.annoIsOpen

        if self.annoIsOpen:
            self.updateHUD(annotator=annotator, behaviour=behaviour)
        else:
            self.updateHUD(annotator="", behaviour="")
        
        if labelledFrames != (None, None):
            if self.postLabelQuery:
                newBehaviour = self.queryForLabel()
                newFilt = Annotation.AnnotationFilter(
                                labelledFrames[1].vials,
                                labelledFrames[1].annotators,
                                [newBehaviour])
                labelledFrames = (labelledFrames[0], newFilt, 1)
            else:
                labelledFrames = (labelledFrames[0], labelledFrames[1], 1)

            self.convertLabelListAndReply(labelledFrames)


    def addTempAnno(self):
        if not self.inEditMode:
            self.postLabelQuery = True
            self.addAnno(self.annotations[0]['annot'], "unknown")

#     @cfg.logClassFunction
    def eraseAnno(self, annotator="peter", behaviour="just testing"):      
        cfg.logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour}))
        self.vh.eraseAnnotation(self.selectedVial, annotator, behaviour)

    def editAnnoROI(self, annotator, behaviour, newROI):
        self.editAnnoMeta(annotator, behaviour, "boundingBox", newROI)

    def editAnnoMeta(self, annotator, behaviour, newMetaKey, newMetaValue):
        self.vh.editAnnotationMetaCurrentFrame(self.selectedVial, annotator,
                                    behaviour, newMetaKey, newMetaValue)

    def editAnnoLabel(self, annotatorOld, behaviourOld, annotatorNew, behaviourNew):

        cfg.log.info("--------- edit label ------------")
        self.vh.editAnnotationLabel(self.selectedVial, annotatorOld,
                                behaviourOld, annotatorNew, behaviourNew)

        if self.selectedVial is None:
            sv = 0
        else:
            sv = self.selectedVial[0]

        anno = self.frames[0][2]
        self.displayAnnotationROIs(anno, sv)
        
#     @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        cfg.log.info("escape annotation")    
        cfg.logGUI.info('"------escape annotation--------"')
        self.vh.escapeAnnotationAlteration()
        self.annoIsOpen = False
        
        
    def getCurrentKey_idx(self):
        return self.idx, self.vh.getCurrentKey_idx()[1]

    def getBookmarksFilename(self):
        folder = os.path.dirname(self.fileList[0])
        annotator = self.annotations[0]['annot']
        filename = os.path.join(folder,
                                "{anno}.bookmarks.json".format(anno=annotator))

        return filename

    def exportSettings(self):
        cfgDict = dict()
        cfgDict['Video'] = dict()
        cfgDict['Video']['background'] = self.backgroundPath
        cfgDict['Video']['bhvr-cache'] = self.bhvrListPath
        cfgDict['Video']['bufferLength'] = self.bufferLength
        cfgDict['Video']['bufferWidth'] = self.bufferWidth
        cfgDict['Video']['cropped-video'] = self.croppedVideo
        cfgDict['Video']['files-running-indices'] = self.runningIndeces
        cfgDict['Video']['frame-data-visualization-path'] = self.fdvtPath
        cfgDict['Video']['rewind-on-click'] = self.rewindOnClick
        cfgDict['Video']['vial'] = self.selectedVial
        cfgDict['Video']['vialROI'] = self.vialROI
        cfgDict['Video']['videoPath'] = self.path

        cfgDict['StepSize'] = self.filterObjArgs['stepSize']
        cfgDict['KeyMap'] = dict()

        for k in self.filterObjArgs['keyMap']:
            cfgDict['KeyMap'][k] = self.filterObjArgs['keyMap'][k].toString()

        cfgDict['Annotation'] = {'annotations': []}
        for anno in self.annotations:
            cfgDict['Annotation']['annotations'] += \
                            [{'annot': anno['annot'],
                              'behav': anno['behav'],
                              'color': anno['color'].name()}]


        cfgDict['ActiveLearning'] = dict()
        cfgDict['ActiveLearning']['remote-request-server'] = self.serverAddress

        yamlStr = yaml.dump(cfgDict, default_flow_style=False,
                            encoding=('utf-8'))

        with open(os.path.join(os.path.dirname(self.path),
                               'config.yaml'), 'w') as f:
            f.writelines(yamlStr)

    def aboutToQuit(self):
        self.exit()

    def debug(self):
        1/0

    @staticmethod
    def parseConfig(path):
        stream = file(path, 'r')
        cfgFile = yaml.load(stream)

        # Video
        if 'vial' in cfgFile['Video'].keys():
            selectedVial = cfgFile['Video']['vial']
        else:
            selectedVial = None

        if 'vialROI' in cfgFile['Video'].keys():
            vialROI = cfgFile['Video']['vialROI']
        else:
            vialROI = None

        if 'videoExtension' in cfgFile['Video'].keys():
            videoExtension = cfgFile['Video']['videoExtension']
        else:
            videoExtension = 'avi'

        if 'background' in cfgFile['Video'].keys():
            backgroundPath = cfgFile['Video']['background']
        else:
            backgroundPath = None

        if 'videoPath' in cfgFile['Video'].keys():
            videoPath = cfgFile['Video']['videoPath']
        else:
            raise ValueError('no videopath in config file')

        if 'frame-data-visualization-path' in cfgFile['Video'].keys():
            fdvtPath = cfgFile['Video']['frame-data-visualization-path']
        else:
            fdvtPath = None

        if 'bhvr-cache' in cfgFile['Video'].keys():
            bhvrListPath = cfgFile['Video']['bhvr-cache']
        else:
            bhvrListPath = None

        if 'startvideo' in cfgFile['Video'].keys():
            startVideo = cfgFile['Video']['startvideo']
        else:
            startVideo = None

        if 'bufferwidth' in cfgFile['Video'].keys():
            bufferWidth = cfgFile['Video']['bufferwidth']
        else:
            bufferWidth = 300

        if 'bufferlength' in cfgFile['Video'].keys():
            bufferLength = cfgFile['Video']['bufferlength']
        else:
            bufferLength = 4

        if 'cropped-video' in cfgFile['Video'].keys():
            croppedVideo = cfgFile['Video']['cropped-video']
        else:
            croppedVideo = False

        if 'files-running-indices' in cfgFile['Video'].keys():
            runningIndeces = cfgFile['Video']['files-running-indices']
        else:
            runningIndeces = True

        if 'rewind-on-click' in cfgFile['Video'].keys():
            rewindOnClick = cfgFile['Video']['rewind-on-click']
        else:
            rewindOnClick = False

        #Active Learning
        if 'ActiveLearning' in cfgFile.keys():
            if 'remote-request-server' in cfgFile['ActiveLearning'].keys():
                serverAddress = \
                    cfgFile['ActiveLearning']['remote-request-server']
            else:
                serverAddress = None
        else:
            serverAddress = None

        # KeyMap
        keyMap = { "stop": cfgFile['KeyMap']['stop'],
                    "step-f": cfgFile['KeyMap']['step-f'],
                    "step-b": cfgFile['KeyMap']['step-b'],
                    "fwd-1": cfgFile['KeyMap']['fwd-1'],
                    "fwd-2": cfgFile['KeyMap']['fwd-2'],
                    "fwd-3": cfgFile['KeyMap']['fwd-3'],
                    "fwd-4": cfgFile['KeyMap']['fwd-4'],
                    "fwd-5": cfgFile['KeyMap']['fwd-5'],
                    "fwd-6": cfgFile['KeyMap']['fwd-6'],
                    "bwd-1": cfgFile['KeyMap']['bwd-1'],
                    "bwd-2": cfgFile['KeyMap']['bwd-2'],
                    "bwd-3": cfgFile['KeyMap']['bwd-3'],
                    "bwd-4": cfgFile['KeyMap']['bwd-4'],
                    "bwd-5": cfgFile['KeyMap']['bwd-5'],
                    "bwd-6": cfgFile['KeyMap']['bwd-6'],
                    "escape": cfgFile['KeyMap']['escape'],
                    "anno-1": cfgFile['KeyMap']['anno-1'],
                    "anno-2": cfgFile['KeyMap']['anno-2'],
                    "anno-3": cfgFile['KeyMap']['anno-3'],
                    "anno-4": cfgFile['KeyMap']['anno-4'],
                    "erase-anno": cfgFile['KeyMap']['erase-anno'],
                    "info": cfgFile['KeyMap']['info']}

        try:
            for key in keyMap:
                keyMap[key] = QtGui.QKeySequence(str(keyMap[key]))#eval("Qt." + keyMap[key], {"Qt":QtCore.Qt})
        except KeyError:
            keyMap = None


        # Step size
        stepSize = {"stop": cfgFile['StepSize']['stop'],
                    "step-f": cfgFile['StepSize']['step-f'],
                    "step-b": cfgFile['StepSize']['step-b'],
                    "fwd-1": cfgFile['StepSize']['fwd-1'],
                    "fwd-2": cfgFile['StepSize']['fwd-2'],
                    "fwd-3": cfgFile['StepSize']['fwd-3'],
                    "fwd-4": cfgFile['StepSize']['fwd-4'],
                    "fwd-5": cfgFile['StepSize']['fwd-5'],
                    "fwd-6": cfgFile['StepSize']['fwd-6'],
                    "bwd-1": cfgFile['StepSize']['bwd-1'],
                    "bwd-2": cfgFile['StepSize']['bwd-2'],
                    "bwd-3": cfgFile['StepSize']['bwd-3'],
                    "bwd-4": cfgFile['StepSize']['bwd-4'],
                    "bwd-5": cfgFile['StepSize']['bwd-5'],
                    "bwd-6": cfgFile['StepSize']['bwd-6'],
                    "allow-steps": cfgFile['StepSize']['allow-steps']}

        filterObjArgs = dict()
        filterObjArgs['keyMap'] = keyMap
        filterObjArgs['stepSize'] = stepSize


        # Annotations
        annotations = cfgFile['Annotation']['annotations']

        return videoPath, annotations, backgroundPath, selectedVial, vialROI, \
                videoExtension, filterObjArgs, startVideo, rewindOnClick,\
                croppedVideo, runningIndeces, fdvtPath, bhvrListPath, \
                bufferWidth, bufferLength



class ContextLineEdit(QtGui.QLineEdit):

    def __init__(self, *args, **kwargs):
        super(ContextLineEdit, self).__init__(*args, **kwargs)
        self.comp = QtGui.QCompleter([""], self)
        self.comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(self.comp)#
        self.setModel(["hallo", "world", "we", "are"])

    def setModel(self, strList):
        self.comp.model().setStringList(strList)

class BehaviourRectItem(MR.LabelRectItem):
    def __init__(self, *args, **kwargs):
        super(BehaviourRectItem, self).__init__(*args, **kwargs)
        self.annotator = None
        self.behaviour = None

    def setAnnotationLabel(self, annotator, behaviour):
        self.annotator = annotator
        self.behaviour = behaviour

        
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
#     
#     with open(args.config_file, 'r') as f:
#         config = json.load(f)
        
        
    # import ConfigParser
    # config = ConfigParser.ConfigParser()
    # config.read(args.config_file)


    videoPath, annotations, backgroundPath, selectedVial, vialROI, \
    videoExtension, filterObjArgs, startVideo, rewindOnClick, croppedVideo, \
    runningIndeces, fdvtPath, bhvrListPath, bufferWidth, \
    bufferLength = VideoTagger.parseConfig(args.config_file)
        
    #### finish parsing config file
    
    if videoPath.endswith(('.' + videoExtension)):
        vp = os.path.split(videoPath)[0]
    else:
        vp = videoPath

    if not os.path.exists(os.path.join(vp, "log")):
        os.makedirs(os.path.join(vp, "log"))

    hGUI = logging.FileHandler(os.path.join(vp, "log",
                    "videoTagger." + \
                    time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime()) +\
                    ".log"))
    fGUI = logging.Formatter('{"time": "%(asctime)s", "func":"%(funcName)s", "args":%(message)s}')
    hGUI.setFormatter(fGUI)
    for handler in cfg.logGUI.handlers:
        cfg.logGUI.removeHandler(handler)
        
    cfg.logGUI.addHandler(hGUI)

    app = QtGui.QApplication(sys.argv)
    
    w = VideoTagger(videoPath, annotations, backgroundPath, selectedVial, vialROI,
                     videoExtension=videoExtension, filterObjArgs=filterObjArgs,
                     startVideoName=startVideo, rewindOnClick=rewindOnClick,
                     croppedVideo=croppedVideo, runningIndeces=runningIndeces,
                     fdvtPath=fdvtPath, bhvrListPath=bhvrListPath,
                     bufferWidth=bufferWidth, bufferLength=bufferLength)
    
    app.connect(app, QtCore.SIGNAL("aboutToQuit()"), w.exit)
    w.quit.connect(app.quit)
    
    sys.exit(app.exec_())