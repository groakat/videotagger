import sys
import os


sys.path.append(os.path.abspath('../../'))
# from OpenGL import GL
# from OpenGL import GLU
from PySide import QtGui
from PySide import QtCore
from PySide import QtOpenGL


from pyTools.gui.videoPlayer_auto import Ui_Form

import pyTools.videoPlayer.videoHandler as VH
import pyTools.videoPlayer.dataLoader as DL
import pyTools.videoPlayer.annoView as AV
import pyTools.videoProc.annotation as Annotation
import pyTools.system.misc as systemMisc
import pyTools.misc.config as cfg
import pyTools.videoPlayer.eventFilter as EF
import pyTools.videoPlayer.RPCController as RPC
import pyTools.misc.FrameDataVisualization as FDV

import numpy as np
import scipy.misc as scim
import pylab as plt
import time

import qimage2ndarray as qim2np
import json
import logging, logging.handlers


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

class videoPlayer(QtGui.QMainWindow):      
    quit = QtCore.Signal()
    startLoop = QtCore.Signal()
     
    def __init__(self, path, 
                        annotations,
                        backgroundPath,
                        selectedVial,
                        vialROI,
                        videoFormat='avi',
                        filterObjArgs=None,
                        startVideoName=None,
                        rewindOnClick=False,
                        croppedVideo=True,
                        videoEnding='.avi', #'.v0.avi',
                        runningIndeces=True,
                        fdvtPath=None,
                        bhvrListPath=None,
                        serverAddress="tcp://127.0.0.1:4242"
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
        
        self.eventFilter = EF.filterObj(self, **filterObjArgs)
        self.installEventFilter(self.eventFilter)
        self.connectSignals()       
        
        self.mouseEventFilter = EF.MouseFilterObj(self)
        
        
        self.croppedVideo = croppedVideo
        
        if croppedVideo:
            videoEnding = ".v{0}{1}".format(selectedVial, videoEnding)
        
        if bhvrListPath is None:
            self.fileList = systemMisc.providePosList(path, ending='.bhvr')
        else:
            with open(bhvrListPath, "r") as f:
                self.fileList = json.load(f)
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.fileList))
        
        self.videoFormat = videoFormat
        self.idx = 0       
        self.play = False
        self.frameIdx = -1
        self.showTraject = False
        self.tempTrajSwap = False
        self.trajNo = 0
        self.trajLabels = []
        self.frames = []
        self.increment = 0
        self.tempIncrement = 0
        self.stop = False
        self.addingAnnotations = True
        self.ui.lbl_eraser.setVisible(False)        
        self.prevSize = 100
        self.fdvtPath = fdvtPath
        self.isLabelingSingleFrame = False
        
        
        self.rewindOnClick = rewindOnClick
        self.rewindStepSize = 500
        self.rewinding = False
        self.rewindCnt = 0
        
        if self.rewindOnClick:
            self.eventFilter.oneClickAnnotation = [True, True, True, True]
        
        self.annotations = annotations 
        self.tmpAnnotation = Annotation.Annotation(0, [''])
        self.annotationRoiLabels = []
        self.annoIsOpen = False
        self.metadata = []
        self.confidence = 0
        
        self.usingVideoRunningIndeces = runningIndeces
        
        self.vialRoi = vialROI
        
        if type(selectedVial) == int:
            self.selectedVial = [selectedVial]
        else:
            self.selectedVial = selectedVial#3
        self.ui.lbl_vial.setText("vial: {0}".format(self.selectedVial))
                
        
        
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
        
        self.fileList = self.convertFileList(self.fileList, videoEnding)
        
        self.vh = VH.VideoHandler(self.fileList, self.changeVideo, 
                               self.selectedVial, startIdx=startIdx,
                               videoEnding=videoEnding)
        
        
        self.updateFrameList(range(2000))
        
        self.configureUI()
        
        if self.croppedVideo:
            self.setBackground(backgroundPath)
        else:
            self.setBackground()
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showNextFrame)
        self.timerID = None
        
        
        self.ui.cb_trajectory.setChecked(self.showTraject)
        self.showTrajectories(self.showTraject)
        
        self.serverAddress = serverAddress
        self.connectedToServer = False
        self.rpcIH = None
            
        
        
        self.show()        
        cfg.logGUI.info(json.dumps(
                            {"message":'"--------- opened GUI ------------"'})) 
        
        self.setCropCenter(None, None)
        
        self.selectVideo(startIdx)
        self.startLoop.emit()
        
        
    @cfg.logClassFunction
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.pb_test.clicked.connect(self.testFunction)
        self.ui.pb_addAnno.clicked.connect(self.addAnno)
        self.ui.pb_eraseAnno.clicked.connect(self.eraseAnno)
        self.ui.pb_connect2server.clicked.connect(self.connectToServer)
        
        self.ui.sldr_paths.valueChanged.connect(self.selectVideo)
        self.ui.lv_frames.activated.connect(self.selectFrame)
        self.ui.lv_jmp.activated.connect(self.selectFrameJump)
        self.ui.lv_paths.activated.connect(self.selectVideoLV)
        
        self.ui.cb_trajectory.stateChanged.connect(self.showTrajectories)
        
        self.startLoop.connect(self.startVideo)
        
        
        
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
        
        self.xFactor = 1 
        self.yFactor = 1 
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        
        self.ui.lbl_v0.setStyleSheet("background-color: rgba(255, 255, 255, 10);")
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
        self.createAnnoViews()
        
    def createAnnoView(self, xPos, yPos, width, height, idx):
        self.annoViewList += [AV.AnnoView(self, vialNo=self.selectedVial, 
                                       annotator=[self.annotations[idx]["annot"]], 
                                       behaviourName=[self.annotations[idx]["behav"]], 
                                       color = self.annotations[idx]["color"], 
                                       geo=QtCore.QRect(xPos, yPos, width, 
                                                       height))]

        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])     
        self.annoViewLabel += [QtGui.QLabel(self)]
        self.annoViewLabel[-1].setText("{0}: {1}".format(\
                                            self.annotations[idx]["annot"],
                                            self.annotations[idx]["behav"]))
        self.annoViewLabel[-1].move(xPos + width + 10, yPos)          
        self.annoViewLabel[-1].adjustSize() 
        
        
    @cfg.logClassFunction
    def createAnnoViews(self):
        self.annoViewList = []
        self.annoViewLabel = []
        
        yPos = 430 
        xPos = 60 
        height = 20
        width = 1000
        
        self.annotations[0]["color"] = QtGui.QColor(0,0,255,150)
        self.annotations[1]["color"] = QtGui.QColor(0,0,255,150)
        self.annotations[2]["color"] = QtGui.QColor(0,255,0,150)
        self.annotations[3]["color"] = QtGui.QColor(0,255,0,150)
        

        self.createPrevFrames(xPos + 135, yPos - (self.prevSize + 20))
        
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
    
        
    def setupFrameView(self):
        frameView = self.ui.frameView
        frameView.registerButtonPressCallback('frames', self.selectVideoTime)
#         if self.fdvtPath is not None:
#             frameView.loadSequence(self.fdvtPath)
            
            
    def createPrevFrames(self, xPos, yPos):
        size = self.prevSize
        
        self.noPrevFrames = 7
        self.prevFrameLbls = []
        self.prevConnectHooks = []
        
        for i in range(self.noPrevFrames):
            self.prevFrameLbls += [QtGui.QLabel(self)]
            self.prevFrameLbls[-1].setGeometry(QtCore.QRect(xPos, yPos, size, size))
            
            self.prevConnectHooks += [[QtCore.QPoint(xPos + size / 2, yPos + size), 
                                      QtCore.QPoint(xPos + size / 2, yPos + size + 2)]]
            
            if i == (self.noPrevFrames - 1) / 2:
                self.prevFrameLbls[-1].setLineWidth(3)
                self.prevFrameLbls[-1].setFrameShape(QtGui.QFrame.Box)
            xPos += size + 5
        
    
        
    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self) 
        painter.resetTransform() 
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        pen = QtGui.QPen(QtGui.QColor(100,100,100))
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
        
        
    def convertFileList(self, fileList, videoEnding):
        fl = []
        for f in sorted(fileList):
            fl += ['.'.join(f.split('.')[:-1]) + videoEnding]
        
        return fl
        
        
    def connectToServer(self):
        
        if self.serverAddress is not None:
            print "connecting to server .."
            self.rpcIH = RPC.RPCInterfaceHandler(self.serverAddress)
            self.rpcIH.updateFDVTSig.connect(self.setFrameView)
            
            self.connectedToServer = True
            
            self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
            if self.fdvtPath is not None:
                self.fdvt.load(self.fdvtPath)
            else:
                print "importing annotations for display (may take a while)"
                self.fdvt.importAnnotations(self.fileList, self.annotations, 
                                            self.selectedVial)
                print "finished importing annotations"
                
            self.rpcIH.sendLabelFDVT([self.fdvt])
                
            self.setFrameView([self.fdvt.serializeData()])
                   
            
    @QtCore.Slot(list)
    def setFrameView(self, lst):
        fdvt = lst[0]
        self.ui.frameView.setSerializedSequence(fdvt)
        
        
    @QtCore.Slot(int)
    def labelSingleFrame(self, idx):
        self.isLabelingSingleFrame = True
        day, hour, minute, frame = self.ui.frameView.fdvTree.idx2key(idx)        
        self.selectVideoTime(self, day, hour, minute, frame)
        
        
    @cfg.logClassFunction#Info
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
#         
        
            
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
            cfg.log.debug("copy image to pixmap")
            px = QtGui.QPixmap().fromImage(qi)     
            cfg.log.debug("set pixmap")
            lbl.setPixmap(px)
        
    @cfg.logClassFunction
    def updateLabel(self, lbl, p, img):
        if img is not None:
            self.loadImageIntoLabel(lbl, np.rot90(img))
            
                
        newX = p[0] - 32
        if self.selectedVial is None:
            newY = self.vialRoi[0][1] - p[1] - 32
        else:
            newY = self.vialRoi[self.selectedVial[0]][1] - p[1] - 32 
        
        cfg.log.debug("p= [{2}, {3}] --> x {0}, y {1}".format(newX, newY, p[0], p[1]))
        lbl.setPos(newX,newY)
        
    @cfg.logClassFunction
    def updatePreviewLabel(self, lbl, img):
#         img = data[0]
        if self.croppedVideo:
            img = np.rot90(img)

        if not self.croppedVideo:
            img = scim.imresize(img[self.prevYCrop, self.prevXCrop], 
                                        (self.prevSize,self.prevSize))
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
        
        
    @cfg.logClassFunction
    def updateMainLabel(self, lbl, img):
        h = img.shape[0]
        w = img.shape[1]
        if self.sceneRect != QtCore.QRectF(0, 0, w,h):
            cfg.log.debug("changing background")
            self.videoView.setGeometry(QtCore.QRect(380, 10, w, h))#1920/2, 1080/2))
            self.videoScene.setSceneRect(QtCore.QRectF(0, 0, w,h))            
            self.videoScene.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.black))
            lbl.setPos(0,0)
            self.sceneRect = QtCore.QRectF(0, 0, w,h)
                    
        self.loadImageIntoLabel(lbl, img)
        
        
    @cfg.logClassFunction
    def positionAnnotationRoi(self, rois):
        while len(self.annotationRoiLabels) < len(rois):
            rect = QtCore.QRectF(0, 0, 64, 64)
            self.annotationRoiLabels += [self.videoScene.addRect(rect)]
            
        usedRoi = 0
        
        cfg.log.debug("Rois: {0}".format(rois))
        for i in range(len(rois)):        
            x1, y1, x2, y2 = rois[i][0]
            color = rois[i][1]
            
            width = x2 - x1
            height = y2 - y1
            
            cfg.log.debug("setting rect to: {0} {1} {2} {3}".format(x1/2, 
                                                                   y1/2,
                                                                   width /2,
                                                                   height / 2))
            self.annotationRoiLabels[i].setRect(0,0, width / 2, height / 2)
            self.annotationRoiLabels[i].setPos(x1/2, y1/2)
            self.annotationRoiLabels[i].setPen(QtGui.QPen(color))
             
            cfg.log.debug("set rect to: {0}".format(self.annotationRoiLabels[i].rect()))
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
        self.frames = []    
        
        if self.selectedVial is None:
            sv = 0            
        else:
            sv = 0
        
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
        if not self.croppedVideo:
            self.updateMainLabel(self.lbl_v0, frame[1][sv][0])
        else:
            self.updateLabel(self.lbl_v0, frame[0][2], frame[1][sv][0])
        
        
        
        # place annotation roi
        
        anno = frame[2]
        self.tmpAnnotation.setFrameList([anno])
        
        rois = []
        for i in range(len(self.annotations)):
            filt = Annotation.AnnotationFilter(None, 
                                            [self.annotations[i]["annot"]],
                                            [self.annotations[i]["behav"]])
            tmpAnno  = self.tmpAnnotation.filterFrameList(filt)      
            
            if tmpAnno.frameList[0][sv] == None:
                continue
                         
            bb = Annotation.getPropertyFromFrameAnno(tmpAnno.frameList[0][sv], 
                                                     "boundingBox")
            
            for b in bb:
                # ensure that annotations without boundingbox do not mess up
                # anything
                if None in b:
                    continue
                rois += [[b, self.annotations[i]["color"]]]
                
        self.positionAnnotationRoi(rois)
        
        
        
        # showing trajectory #
        self.frames = []
        for i in range(self.trajNo):
            self.frames += [self.vh.getTempFrame(increment * (i - offset), 
                                                 posOnly=True)] 
         
        for i in range(len(self.frames)-1, -1, -1):
            frame = self.frames[i]
            self.updateLabel(self.trajLabels[i][0], frame[0][2], None)


        # showing previews #
        offset = (len(self.prevFrameLbls) - 1) / 2
        self.prevFrames = []
                 
        for i in range(len(self.prevFrameLbls)):
            self.prevFrames += [self.vh.getTempFrame(i - offset)]
            self.updatePreviewLabel(self.prevFrameLbls[i], self.prevFrames[i][1][sv][0])
             
        
        self.vh.updateAnnotationProperties(self.getMetadata())

        
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
        
    @cfg.logClassFunction
    def setBackground(self, path=None):
        
        if path:        
            a = plt.imread(path) * 255
            
            # crop and rotate background image to show only one vial
            rng = slice(*self.vialRoi[self.selectedVial[0]])
            a = np.rot90(a[:, rng]).astype(np.uint32)
            
            h = a.shape[0]
            w = a.shape[1]
            
            # grey conversion
            b = a[:,:,0] * 0.2126 + a[:,:,1] * 0.7152 + a[:,:,2] * 0.0722
            a[:,:,0] = b
            a[:,:,1] = b
            a[:,:,2] = b
            
            im = np2qimage(a).convertToFormat(QtGui.QImage.Format_RGB32, QtCore.Qt.MonoOnly)
            
            pixmap = QtGui.QPixmap()
            px = QtGui.QPixmap.fromImage(im)
            
        else:
            h = 0
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
        
        fmt = QtOpenGL.QGLFormat()
        fmt.setAlpha(True)
        fmt.setOverlay(True)
        fmt.setDoubleBuffer(True);                 
        fmt.setDirectRendering(True);
         
        glw = QtOpenGL.QGLWidget(fmt)
#         glw.setMouseTracking(True)
        
        self.videoView.setViewport(glw)
        self.videoView.viewport().setCursor(QtCore.Qt.BlankCursor)
        self.videoView.setGeometry(QtCore.QRect(100, 10, w, h))#1920/2, 1080/2))
        self.videoView.show()
        self.videoView.fitInView(self.bgImg, QtCore.Qt.KeepAspectRatio)
        
#         self.videoView.installEventFilter(self.mouseEventFilter)
        self.videoView.setMouseTracking(True)
#         self.lbl_v0.setAcceptHoverEvents(True)
#         self.videoScene.setAcceptHoverEvents(True)
        self.videoScene.installEventFilter(self.mouseEventFilter)
        
        
        
        geo = QtCore.QRectF(0, 0, 64, 64)
        penCol = QtGui.QColor()
        penCol.setHsv(50, 255, 255, 255)
        self.cropRect = self.videoScene.addRect(geo, QtGui.QPen(penCol))
#         self.videoView.setCursor(QCursor(Qt.CrossCursor))
        
        
    @QtCore.Slot()
    def startVideo(self):
        self.play = True
        
        
        cfg.log.debug("start Video")
        self.showNextFrame(0)
        self.vh.loadProgressive = True
        
        self.stop = False
        skipCnt = 0 # counts how often process events were skipped
        
        
        cfg.logGUI.info('"--------- start mainloop ------------"')
         
        while not self.stop:
            #cfg.log.info("begin   --------------------------------------- main loop")
            self.vh.loadProgressive = True
             
            dieTime = QtCore.QTime.currentTime().addMSecs(33)
                         
            if self.play:            
                self.showNextFrame(self.increment)
                 
#                 if self.increment == 0:
#                     self.play = False
                    
            if not(QtCore.QTime.currentTime() < dieTime):
                cfg.log.warning("no realtime display!!! " + 
                                cfg.Back.BLUE + 
                                "mainloop overflow before processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QtCore.QTime.currentTime())))
                
            elif(QtCore.QTime.currentTime() < dieTime.addMSecs(15)):
                frameNo = self.vh.getCurrentFrameNo()
                self.ui.lbl_v1.setText("no: {0}".format(frameNo))
             
#             cfg.log.debug("---------------------------------------- while loop() - begin")

            if not (QtCore.QTime.currentTime() < dieTime):                
                skipCnt += 1
            else:
                skipCnt = 0
                
            while(QtCore.QTime.currentTime() < dieTime) or (skipCnt > 10):
                skipCnt = 0
#                 cfg.log.debug("processEvents() - begin")
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents, QtCore.QTime.currentTime().msecsTo(dieTime))
#                 cfg.log.debug("processEvents() - end")
                 
            if not(QtCore.QTime.currentTime() < (dieTime.addMSecs(1))):
                cfg.log.warning("no realtime display!!! " + 
                                cfg.Back.YELLOW + 
                                "mainloop overflow after processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QtCore.QTime.currentTime())))
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
        self.vh.loadProgressive = False
        
    @cfg.logClassFunction
    def generatePatchVideoPath(self, posPath, vialNo):
        """
        strips pos path off its postfix and appends it with the vial + video
        format postfixq
        """
        return posPath.split('.pos')[0] + '.v{0}.{1}'.format(vialNo, 
                                                            self.videoFormat)
                                                            
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
        self.ui.lbl_v0.setText("current file: {0}".format( \
                                                    sorted(self.fileList)[idx]))
        
        self.increment = 0 
        self.showNextFrame(0)
#         self.startLoop.emit()
        
    def selectVideoTime(self, day, hour, minute, frame, data=None):
        
        print "selectVideoTime: clicked on day {0}, hour {1}, minute {2}, frame {3}, data {4}".format(
                                                    day, hour, minute, frame, data)
        
        if self.usingVideoRunningIndeces:
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
                    
        self.ui.label.update()
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

        
    def testFunction(self):
        cfg.log.debug("testFunction")
#         1/0
#         self.increment = 40
        self.rpcIH.getNextJob()
        
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
        cfg.logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour,
                                "confidence": confidence}))
        
        if not self.annoIsOpen:
            self.confidence = confidence     
                                
        if self.rewindOnClick:
            if not self.rewinding:
                self.initRewind()
                
                ##
            else:
                labelledFrames = self.vh.addAnnotation(self.selectedVial, 
                                                       annotator, 
                                      behaviour, metadata=self.getMetadata())
                
                if oneClickAnnotation:                
                    labelledFrames = self.vh.addAnnotation(self.selectedVial, 
                                                           annotator, 
                                      behaviour, metadata=self.getMetadata())
                
                self.stopRewind()
                    
        
        else:    
            labelledFrames = self.vh.addAnnotation(self.selectedVial, annotator, 
                                  behaviour, metadata=self.getMetadata())
                
            if oneClickAnnotation:                
                labelledFrames = self.vh.addAnnotation(self.selectedVial, annotator, 
                                  behaviour, metadata=self.getMetadata())
                
        self.annoIsOpen = not self.annoIsOpen
        
        if labelledFrames is not None:
            if self.isLabelingSingleFrame:
                self.rpcIH.sendReply(labelledFrames)
        
    def convertLabelListAndReply(self, labelledFrames):
        """
        Args
            labelledFrames (output from vh.addAnnotation or vh.eraseAnnotation
        
        """
        frames = labelledFrames[0]
        filt = labelledFrames[1]
        
        deltaVector = []
        for key in frames.keys():
            treeKey = FDV.filename2Time(key)
            day = treeKey[0]
            hour = treeKey[1]
            minute = treeKey[2]
            for frame in frames[key]:
                deltaVector += [{'day': day,
                                 'hour': hour,
                                 'minute': minute,
                                 'frame': frame},
                                filt]
        
        
#     @cfg.logClassFunction
    def eraseAnno(self, annotator="peter", behaviour="just testing"):      
        cfg.logGUI.info(json.dumps({"annotator": annotator,
                                "behaviour": behaviour}))
        self.vh.eraseAnnotation(self.selectedVial, annotator, behaviour)
        
#     @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        cfg.log.info("escape annotation")    
        cfg.logGUI.info('"------escape annotation--------"')
        self.vh.escapeAnnotationAlteration()
        
        
        
    
    def aboutToQuit(self):
        self.exit()
        
        
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
            keyMap[key] = eval("Qt." + config['keyMap'][key], {"Qt":QtCore.Qt})
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
        
    try:
        croppedVideo = config['cropped-video']
    except KeyError:
        croppedVideo = False
        
    try:
        runningIndeces = config['files-running-indeces']
    except KeyError:
        runningIndeces = True
        
    try:
        fdvtPath = config['frame-data-visualization-path']
    except KeyError:
        fdvtPath = None
        
    try:
        bhvrListPath = config['bhvr-cache']
    except KeyError:
        bhvrListPath = None
        
    try:
        serverAddress = config['remote-request-server']
    except KeyError:
        serverAddress = "tcp://127.0.0.1:4242"
        
    hGUI = logging.FileHandler(os.path.join(path, 
                    "videoPlayer." + \
                    time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime()) +\
                    ".log"))
    fGUI = logging.Formatter('{"time": "%(asctime)s", "func":"%(funcName)s", "args":%(message)s}')
    hGUI.setFormatter(fGUI)
    for handler in cfg.logGUI.handlers:
        cfg.logGUI.removeHandler(handler)
        
    cfg.logGUI.addHandler(hGUI)
    
    
    app = QtGui.QApplication(sys.argv)
    
    w = videoPlayer(path, annotations, backgroundPath, selectedVial, vialROI,
                     videoFormat='avi', filterObjArgs=filterObjArgs,
                     startVideoName=startVideo, rewindOnClick=rewindOnClick,
                     croppedVideo=croppedVideo, runningIndeces=runningIndeces,
                     fdvtPath=fdvtPath, bhvrListPath=bhvrListPath)
    
    app.connect(app, QtCore.SIGNAL("aboutToQuit()"), w.exit)
    w.quit.connect(app.quit)
    
    sys.exit(app.exec_())