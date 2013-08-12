import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtGui import *
from PyQt4.QtCore import * 
from PyQt4.QtOpenGL import * 


from videoPlayer_auto import Ui_Form

from pyTools.system.videoExplorer import *
from pyTools.imgProc.imgViewer import *
from pyTools.videoProc.annotation import *
import pyTools.misc.basic as bsc 
import pyTools.misc.config as cfg
import copy

import numpy as np
#import matplotlib as mpl
import pylab as plt
import time


from qimage2ndarray import *
from PyQt4.uic.Compiler.qtproxies import QtCore

from collections import namedtuple



#################################################################### 
class MyListModel(QAbstractListModel): 
    def __init__(self, datain, parent=None, *args): 
        """ datain: a list where each item is a row
        """
        QAbstractListModel.__init__(self, parent, *args) 
        self.listdata = datain
 
    def rowCount(self, parent=QModelIndex()): 
        return len(self.listdata) 
 
    def data(self, index, role): 
        if index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()])
        else: 
            return QVariant()
            
            

#################################################################### 

KeyIdxPair = namedtuple('KeyIdxPair', ['key', 'idx'])

class videoPlayer(QMainWindow):      
    quit = pyqtSignal()
     
    def __init__(self, path, videoFormat='avi'):
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
        
        self.connectSignals()       
        
        self.posList = self.providePosList(path)    
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.posList))
        
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
        
        self.vh = VideoHandler(self.fileList, self.changeVideo)
#         self.vh.changedFile.connect(self.changeVideo)
        
        
        self.filterList = []
        
        
        #self.setVideo(0)
        
        
        
        self.updateFrameList(range(2000))
        
        self.configureUI() 
        
        self.vialRoi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
        
        self.selectedVial = 0
        
        self.setBackground("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showNextFrame)
        self.timerID = None
        
        
        self.ui.lbl_v0.setText("current file: {0}".format(self.vh.posPath))
        self.show()
        self.selectVideo(0)
        self.startVideo()
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
        
        self.ui.sldr_paths.valueChanged.connect(self.selectVideo)
        self.ui.lv_frames.activated.connect(self.selectFrame)
        self.ui.lv_jmp.activated.connect(self.selectFrameJump)
        self.ui.lv_paths.activated.connect(self.selectVideoLV)
        
        self.ui.cb_trajectory.stateChanged.connect(self.showTrajectories)
        
    @cfg.logClassFunction
    def configureUI(self):
        
        self.xFactor = 1 # self.ui.label.width() / 1920.0
        self.yFactor = 1 #self.ui.label.height() / 1080.0
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        
        self.ui.lbl_v0.setStyleSheet("background-color: rgba(255, 255, 255, 10);")
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
        self.createAnnoViews()
        
        
    @cfg.logClassFunction
    def createAnnoViews(self):
        self.annoViewList = []
        
        yPos = 420
        xPos = 60 
        height = 20
        width = 1000
        
        self.createPrevFrames(xPos - 15, yPos - 95)
        
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["peter"], behaviourName=["just testing"],  color = QColor(0,0,255,150), geo=QRect(xPos, yPos, width, height))]
#         self.annoViewList[-1].setGeometry(QRect(xPos, yPos, width, height))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1]) 
        yPos += height + 5
        
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["peter"], behaviourName=["struggle"], color = QColor(0,255,0,150), geo=QRect(xPos, yPos, width, height))]
#         self.annoViewList[-1].setGeometry()
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])       
        yPos += height + 5 
        
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["peter"], behaviourName=["flying"], color = QColor(255,0,0,150), geo=QRect(xPos, yPos, width, height))]
#         self.annoViewList[-1].setGeometry(QRect(xPos, yPos, width, height))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])      
        
        for aV in self.annoViewList:
            cfg.log.debug("av: {aV}".format(aV=aV))
            
            
    def createPrevFrames(self, xPos, yPos):
        
        self.noPrevFrames = 15
        self.prevFrameLbls = []
        self.prevConnectHooks = []
        
        for i in range(self.noPrevFrames):
            self.prevFrameLbls += [QLabel(self)]
            self.prevFrameLbls[-1].setGeometry(QRect(xPos, yPos, 64, 64))
            
            self.prevConnectHooks += [[QPoint(xPos + 32, yPos + 64), 
                                       QPoint(xPos + 32, yPos + 66)]]
            
            if i == (self.noPrevFrames - 1) / 2:
                self.prevFrameLbls[-1].setLineWidth(3)
                self.prevFrameLbls[-1].setFrameShape(QFrame.Box)
            xPos += 64 + 5
        
    @cfg.logClassFunction
    def keyPressEvent(self, event):
        key = event.key()
        
        self.showTrajectTemp = True
                
        if key == Qt.Key_S:
            self.increment = 0
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_D:
            self.increment = 1
            self.showNextFrame(self.increment)
            self.vh.annoViewZoom(6)
            self.play = False
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_E:
            self.increment = 1
            self.vh.annoViewZoom(4)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_Y:
            self.increment = 3
            self.vh.annoViewZoom(2)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_C:
            self.increment = 10
            #self.vh.annoViewZoom(1)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_V:
            self.increment = 40
            #self.vh.annoViewZoom(0)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_M:
            self.increment = 60
            #self.vh.annoViewZoom(0)
            self.play = True
            if not self.tempTrajSwap:
                self.tempTrajSwap = True
                self.showTrajectories(False)
        
        if key == Qt.Key_A:
            self.increment = -1
            self.showNextFrame(self.increment)
            self.vh.annoViewZoom(6)
            self.play = False
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_Q:
            self.increment = -1
            self.vh.annoViewZoom(4)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_T:
            self.increment = -3
            self.vh.annoViewZoom(2)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_X:
            self.increment = -10
            #self.vh.annoViewZoom(1)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_Z:
            self.increment = -40
            #self.vh.annoViewZoom(0)
            self.play = True
            if self.tempTrajSwap:
                self.tempTrajSwap = False
                self.showTrajectories(True)
            
        if key == Qt.Key_N:
            self.increment = -60
            #self.vh.annoViewZoom(0)
            self.play = True
            if not self.tempTrajSwap:
                self.tempTrajSwap = True
                self.showTrajectories(False)
            
        if key == Qt.Key_I:
            cfg.log.debug("position length: {0}".format(self.vh.getCurrentPositionLength()))
            cfg.log.debug("video length: {0}".format(self.vh.getCurrentVideoLength()))
            
        if key == Qt.Key_Escape:
            self.escapeAnnotationAlteration()
            
        if key == Qt.Key_1:
            self.vh.addAnnotation(0, "peter", "falling", confidence=1)
            
        if key == Qt.Key_2:
            self.vh.addAnnotation(0, "peter", "struggle", confidence=1)
            
        if key == Qt.Key_3:
            self.vh.addAnnotation(0, "peter", "flying", confidence=1)
            
        self.ui.speed_lbl.setText("Speed: {0}x".format(self.increment))
        
    def paintEvent(self, event):
        painter = QPainter(self)
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
            
            painter.drawLine(self.prevConnectHooks[i][0], self.prevConnectHooks[i][1])   
            painter.drawLine(self.prevConnectHooks[i][1], avHooks[aVi][1])            

            painter.drawLine(avHooks[aVi][0], avHooks[aVi][1])       
            
        
            
        
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
        
        img = frame.ndarray()
        
        qi = array2qimage(img)
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
    def updateLabel(self, lbl, p, img):
        if img is not None:
            qi = array2qimage(img)
            pixmap = QPixmap()
            px = QPixmap.fromImage(qi)        
            #lbl.setScaledContents(True)
            lbl.setPixmap(px)
            
                
        newX = p[0] - 32#lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = self.vialRoi[0][1] - p[1] - 32 #lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
        
        
        lbl.setPos(newX,newY)
        #lbl.setStyleSheet("border: 1px dotted rgba(255, 0, 0, 75%);");
        #lbl.raise_()
        #lbl.update()
        
    @cfg.logClassFunction
    def updateOriginalLabel(self, lbl, img):
        qi = array2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lbl.setScaledContents(False)
        lbl.setPixmap(px)
        
        lbl.update()
        
        
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
        if increment is None:
            increment = self.increment
        
        #if self.frames != []:
        #    self.frames.pop(0)
        self.frames = []    
        sv = self.selectedVial
        
        offset = 5  
        
        if increment > 0:
            self.frames += [self.vh.getNextFrame(increment, checkBuffer)]
        elif increment < 0:
            self.frames += [self.vh.getPrevFrame(-increment, checkBuffer)]
        else:
            self.frames += [self.vh.getCurrentFrame()]
            increment = 8
            offset = (self.trajNo / 2) 
        
        frame = self.frames[0]
        self.updateLabel(self.lbl_v0, frame[0][0], frame[1][sv])
        
        self.frames = []
        for i in range(self.trajNo):
            self.frames += [self.vh.getTempFrame(increment * (i - offset))] 
        
        
        for i in range(len(self.frames)-1, -1, -1):
            frame = self.frames[i]
#             if i == 0:
# #                 self.updateLabel(self.lbl_v1, frame[0][1], frame[1][1])
# #                 self.updateLabel(self.lbl_v2, frame[0][2], frame[1][2])
# #                 self.updateLabel(self.lbl_v3, frame[0][3], frame[1][3])
#             
# #                 self.updateOriginalLabel(self.ui.lbl_v3_full, frame[1][3])
#             else:
            self.updateLabel(self.trajLabels[i][0], frame[0][sv], None)
#                 self.updateLabel(self.trajLabels[i][1], frame[0][1], None)
#                 self.updateLabel(self.trajLabels[i][2], frame[0][2], None)
#                 self.updateLabel(self.trajLabels[i][3], frame[0][3], None)


        offset = (len(self.prevFrameLbls) - 1) / 2
        self.prevFrames = []
        for i in range(len(self.prevFrameLbls)):
            self.prevFrames += [self.vh.getTempFrame(i - offset)]
            self.updateOriginalLabel(self.prevFrameLbls[i], self.prevFrames[i][1][sv])
#             
#         self.prevFrames += [self.vh.getTempFrame(-1)]
#         self.prevFrames += [self.vh.getTempFrame(0)]
#         self.prevFrames += [self.vh.getTempFrame(1)]
#         
#         self.updateOriginalLabel(self.ui.lbl_v0_full, prevFrames[0][1][sv])
#         self.updateOriginalLabel(self.ui.lbl_v1_full, prevFrames[1][1][sv])
#         self.updateOriginalLabel(self.ui.lbl_v2_full, prevFrames[2][1][sv])
        
        
        
        if self.showTraject:
            pass
        
    @cfg.logClassFunction
    def jumpToFrame(self, vE, lbl, p, frameNo):    
        
        frame = vE.vs.get_frame_no(frameNo)
        
        img = frame.ndarray()
        
        qi = array2qimage(img)
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
    def setBackground(self, path):
        a = plt.imread(path)
        
        # crop and rotate background image to show only one vial
        rng = slice(*self.vialRoi[self.selectedVial])
        a = np.rot90(a[:, rng])
        
        h = a.shape[0]
        w = a.shape[1]
        
        qi = array2qimage(a*255)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        #~ 
        #~ self.ui.label.setScaledContents(True)
        #~ self.ui.label.setPixmap(px)
        
        self.videoView = QGraphicsView(self)        
        self.videoView.setFrameStyle(QFrame.NoFrame)
        self.videoView.setGeometry(QRect(10, 10, w, h))#1920/2, 1080/2))
        self.videoScene = QGraphicsScene(self)
        self.videoScene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.videoScene.setSceneRect(QRectF(0, 0, w,h))#1920, 1080))
        self.videoScene.setBackgroundBrush(QBrush(Qt.black))
        
        self.videoView.setScene(self.videoScene)
        #self.videoView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.videoView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.bgImg = QGraphicsPixmapItem(px)        
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
        
        self.videoView.setViewport(QGLWidget(fmt))
        self.videoView.show()
        self.videoView.fitInView(self.bgImg, Qt.KeepAspectRatio)
        
    def startVideo(self):
        #self.play = True
        #self.setBackground("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        
        cfg.log.debug("start Video")
        self.showNextFrame(0)
        self.vh.loadProgressive = True
        
        self.stop = False
        
         
         
        while not self.stop:
            cfg.log.debug("begin   --------------------------------------- main loop")
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
             
            cfg.log.debug("---------------------------------------- while loop() - begin")
            while(QTime.currentTime() < dieTime):
                cfg.log.debug("processEvents() - begin")
                QApplication.processEvents(QEventLoop.AllEvents)#, QTime.currentTime().msecsTo(dieTime)
                cfg.log.debug("processEvents() - end")
                 
            if not(QTime.currentTime() < (dieTime.addMSecs(1))):
                cfg.log.warning("no realtime display!!! " + 
                                cfg.Back.YELLOW + 
                                "mainloop overflow after processEvents(): {0}ms".format(
                                        dieTime.msecsTo(QTime.currentTime())))
            cfg.log.debug("---------------------------------------  while loop() - end")
             
            cfg.log.debug("end   ------------------------------------------ main loop")
         
        self.vh.loadProgressive = False
        
    @cfg.logClassFunction
    def providePosList(self, path):
        fileList  = []
        posList = []
        cfg.log.debug("scaning files...")
        for root,  dirs,  files in os.walk(path):
            for f in files:
                if f.endswith('npy'):
                    path = root + '/' + f
                    fileList.append(path)
                    
        self.fileList = sorted(fileList)
        cfg.log.debug("scaning files done")
        return posList
        
        
    @cfg.logClassFunction
    def close(self):
        self.stop = True
        
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
        self.vh.getFrame(self.fileList[idx], 0)
        
#     @cfg.logClassFunction
    def selectVideoLV(self, mdl):
        self.idx = mdl.row()   
        self.selectVideo(self.idx)
        
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
                penCol.setHsv(i / 50.0 * 255, 200, 150, 15)
                lbl += [self.videoScene.addRect(geo, QPen(penCol))]
                #l.setLineWidth(1)
                #l.setStyleSheet("border: 1px solid hsva({0}, 200, 150, 15%);".format(i / 50.0 * 255));
                #l.show()
                #lbl += [l]
            self.trajLabels += [lbl]
    
    @cfg.logClassFunction
    @pyqtSlot(list)
    def addVideo(self, videoList):
        cfg.log.debug("slot")
        self.videoList += videoList
        
        cfg.log.debug("{0}".format(self.videoList))
        
    @cfg.logClassFunction
    @pyqtSlot(str)
    def changeVideo(self, filePath):
        cfg.log.debug("Change video to {0}".format(filePath))
        
        self.ui.lbl_v0.setText("current file: {0}".format(filePath))
#         posInLst = self.fileList.index(filePath)
                
#         self.ui.lv_paths.setCurrentIndex(self.lm.index(posInLst,0))
        #self.updateFrameList(range(self.vh.getCurrentVideoLength()))
        
        cfg.log.debug("end")
        
    @cfg.logClassFunction
    def prefetchVideo(self, posPath):        
        self.vl = VideoLoader()
        self.vl.loadedVideos.connect(self.addVideo)
        self.vl.loadVideos(posPath)
        
    def testFunction(self):
        cfg.log.debug("testFunction")
#         self.vh.saveAll()
        self.showNextFrame(0)
        self.vh.loadProgressive = True
        
#     @cfg.logClassFunction
    def addAnno(self, annotator="peter", behaviour="just testing", confidence=1):
        self.vh.addAnnotation(0, annotator, behaviour, confidence=confidence)
#     @cfg.logClassFunction

        
#     @cfg.logClassFunction
    def eraseAnno(self):
        self.vh.eraseAnnotation(0, "peter", "just testing")
        
#     @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        cfg.log.info("escape annotation")
        self.vh.escapeAnnotationAlteration()
        
        
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
        QGraphicsRectItem.__init__(self)
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.annoView = annoView

    def hoverEnterEvent(self, event):
        self.setPen(Qt.red)
        self.annoView.centerAt(self)
        QGraphicsRectItem.hoverEnterEvent(self, event)
    
    def hoverLeaveEvent(self, event):
        self.setPen(QColor(0,0,0,0))
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
        self.cMarker1.setFrameShape(QFrame.Box)
        
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
        self.annotationUnfiltered = dict()
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
        self.setZoom(self.zoom)
#         self.centerOn(self.frames[0])
            
    def centerAt(self, avItem):        
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                mid = (self.frameAmount + 1) / 2
                cfg.log.info("centering at {0} - {1}".format(i, mid))
                self.parent().showTempFrame(i-mid)
                
        if avItem is None:
            self.parent().resetTempFrame()
            
    def alterAnnotation(self, avItem):        
        for i in range(len(self.frames)):
            if avItem is self.frames[i]:
                self.parent().addAnno(annotator="peter", behaviour="just testing", confidence=1)
                
        if avItem is None:
            self.parent().resetTempFrame()
        
    @cfg.logClassFunction
    def addAnnotation(self, annotation, key, addAllAtOnce=True):
        """
        adds an annotation to a scene
        """
        filt = AnnotationFilter([self.vialNo], self.annotator, 
                                                        self.behaviourName)
        self.annotationUnfiltered[key] = annotation
        self.annotationDict[key] = annotation.filterFrameList(filt)
        
        
        return
#         
    @cfg.logClassFunction
    def removeAnnotation(self, key, rng=None):
        if key in self.annotationDict.keys():
            del self.annotationDict[key]   
            del self.annotationUnfiltered[key]   
        
    @cfg.logClassFunction
    def setPosition(self, key=None, idx=None):
        if key is None:
            key = self.selKey
        if idx is None:
            idx = self.idx
                    
        self.selKey = key
        self.idx = idx
        self.addTempAnno()
        
        self.updateConfidenceList(key, idx)
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
        if self.zoom < 4:
            for line in self.lines:
                line.setVisible(False)
        else:
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
        curKeyPos =  [i for i,x in enumerate(keyList) if x == key][0]
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
                    cfg.log.debug("distFirst {0}".format(dist2first))
                    for i in range(dist2first + 1):
                        self.confidenceList += [None]
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
                curKeyPos += 1
                curKey = keyList[curKeyPos]
                curIdx = 0
                            
            if (self.addingAnno 
                            and (curKey in tempKeys) 
                            and (curIdx in self.tempRng[curKey])):
                conf = 1
            elif (self.erasingAnno 
                            and (curKey in tempKeys) 
                            and (curIdx in self.tempRng[curKey])):
                conf = None
            else:
                conf = KeyIdxPair(curKey, curIdx)
                  
            self.confidenceList += [conf]            
            curIdx += 1     
        
    @cfg.logClassFunction
    def updateGraphicView(self):
        for i in range(len(self.confidenceList)):   
            kip = self.confidenceList[i]
            if kip == None:
                conf = None
            elif kip == 1:
                conf = 1
            else:
                conf = self.annotationDict[kip.key].frameList[kip.idx]
#             cfg.log.warning("{0}".format(conf))
            if conf is not None:
                self.frames[i].setBrush(self.brushA)
                self.frames[i].setPen(self.penA)
            else:                
                self.frames[i].setBrush(self.brushI)
                self.frames[i].setPen(self.penI)
                
    @cfg.logClassFunction
    def addAnno(self):
        if not self.addingAnno:
            self.addingAnno = True
            #self.tempStart = [self.selKey, self.idx]
            self.tempStart = bsc.FramePosition(self.annotationDict, self.selKey, 
                                                                    self.idx)
            self.setPosition()  
        else:
            self.addingAnno = False  
            self.tempRng = dict()
            self.tempAnno = dict()

             
    @cfg.logClassFunction
    def eraseAnno(self):
        if not self.erasingAnno:
            self.erasingAnno = True
            self.tempStart = bsc.FramePosition(self.annotationDict, self.selKey, 
                                                                    self.idx)
            self.tempAnno = dict()
            self.setPosition()   
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
    def addTempAnno(self):
        self.resetAnno()
        if self.addingAnno:
            tempEnd = bsc.FramePosition(self.annotationDict, self.selKey, self.idx)            
            self.tempRng = bsc.generateRangeValuesFromKeys(self.tempStart, tempEnd) 

        if self.erasingAnno:                         
            tempEnd = bsc.FramePosition(self.annotationDict, self.selKey, self.idx)            
            self.tempRng = bsc.generateRangeValuesFromKeys(self.tempStart, tempEnd)                    
        
class BaseThread(QThread):
    @cfg.logClassFunction
    def __init__(self):
        QThread.__init__(self)
        self.exiting = False

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
        
    @cfg.logClassFunction
    def delay(self, secs):
        dieTime = QTime.currentTime().addSecs(secs)
        while(QTime.currentTime() < dieTime ):
            self.processEvents(QEventLoop.AllEvents, 100)
        
from IPython.parallel import Client
# Subclassing QObject and using moveToThread
# http://labs.qt.nokia.com/2007/07/05/qthreads-no-longer-abstract/
class VideoLoader(BaseThread):        
    loadedVideos = pyqtSignal(list) 
    loadedAnnotation = pyqtSignal(list)
    finished = pyqtSignal()   

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
                
        if self.annotation is not None:
            self.annotation.saveToFile(self.posPath.split('.pos')[0] + '.bhvr')
    
    @cfg.logClassFunction
    def __init__(self, posPath, videoHandler, selectedVials=[0]):
        BaseThread.__init__(self)        
        
        self.loading = False
        
        self.videoLength = -1
        self.frameList = []
        
        self.annotation = None # annotation object
        
        self.posPath = copy.copy(posPath)      
        
        self.selectedVials = selectedVials
        
        self.videoHandler = videoHandler
        
        # call at the end
        self.loadVideos()

    @cfg.logClassFunction
    def loadVideos(self):    
        self.exiting = False
        self.loading = True
        self.start()        
        
    @cfg.logClassFunction
    def run(self):
        cfg.log.debug("loadVideos")
        rc = Client()
        cfg.log.debug("rc.ids : {0}".format(rc.ids))
        
        dview = rc[:]        
        lbview = rc.load_balanced_view()   
        
        #@lbview.parallel(block=True)
        def loadVideo(f, vialNo):    
            from qimage2ndarray import array2qimage
            from pyTools.system.videoExplorer import videoExplorer
            import numpy as np    
            
            vE = videoExplorer()        
            
            
            qi = [np.rot90(vE.getFrame(f, info=False, frameMode='RGB'))]
            for frame in vE:
                qi += [np.rot90(frame)]
                        
            ret = dict()
            
            ret["vialNo"] = vialNo
            ret["qi"] = qi
            return ret     
            
        @cfg.logClassFunction
        def loadAnnotation(posPath, videoLength):
            from pyTools.videoProc.annotation import Annotation
            from os.path import isfile         
                        
            f = posPath.split('.pos')[0] + '.bhvr'
            if isfile(f):
                cfg.log.debug("videoLoader: f exists create empty Annotation")
                out = Annotation()
                cfg.log.debug("videoLoader: created Annotation. try to load..")
                try:
                    out.loadFromFile(f)
                    cfg.log.debug("videoLoader: loaded Annotation")                    
                except:
                    cfg.log.warning("load annotation of "+f+" failed, reset annotaions")
                    out = Annotation(frameNo=videoLength, vialNames=["Abeta +RU",
                                                                 "ABeta -RU",
                                                                 "dilp",
                                                                 "wDah(+)"])
            else:
                cfg.log.debug("videoLoader: f exists NOT create empty Annotation")
                out = Annotation(frameNo=videoLength, vialNames=["Abeta +RU",
                                                                 "ABeta -RU",
                                                                 "dilp",
                                                                 "wDah(+)"])
            return out
            
        results = []
        for i in self.selectedVials:
            f = self.posPath.split('.pos')[0] + '.v{0}.{1}'.format(i, 'avi')
            results += [lbview.apply_async(loadVideo, f, i)]
        
        cfg.log.debug("videoLoader: waiting for process...")
        allReady = False
        while not allReady:
            if self.exiting:
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
                
            self.msleep(10)
        
        cfg.log.debug("videoLoader: copy results")
        self.frameList = [0 for i in range(len(self.selectedVials))]
        for i in range(len(self.selectedVials)):
            # copy data
            ar = results[i].get()
            self.frameList[ar["vialNo"]] = ar["qi"]
            # delete data from cluster
            msgId = results[i].msg_id
            #~ del lbview.results[msgId]
            del rc.results[msgId]
            del rc.metadata[msgId]
        
        # close client to close socket connections
        cfg.log.debug("videoLoader: close client to close socket connections")
        rc.close()
        
        if not self.exiting:
            cfg.log.debug("videoLoader: load positions")
            self.pos = np.load(self.posPath)
            self.videoLength = len(self.frameList[0])
        
        if not self.exiting:
            cfg.log.debug("videoLoader: load annotations")
            self.annotation = loadAnnotation(self.posPath, self.videoLength)
        
        cfg.log.debug("finished loading, emiting signal")
        
#         self.finished.emit()  
#         self.loadedAnnotation.emit([self.annotation, self.posPath])


        self.videoHandler.updateNewAnnotation([self.annotation, self.posPath])
        
        
        self.loading = False
        
        
    @cfg.logClassFunction
    def getVideoLength(self):
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
            self.wait()
            

        if self.exiting:
            return
        
        if idx < self.videoLength:
            out = []
            for i in range(len(self.frameList)):
                out += [self.frameList[i][idx]]
                
            return [self.pos[idx], out]
        else:
            raise RuntimeError("Video frame was not available (index out of range (requested {0} of {1})".format(idx, len(self.frameList)))
            
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
    newVideoLoader = pyqtSignal(list)
    deleteVideoLoader = pyqtSignal(list)
    changedFile = pyqtSignal(str)
    
    @cfg.logClassFunction
    def __init__(self, posList, fileChangeCb):
        super(VideoHandler, self).__init__()        
        
        self.videoDict = dict()
        self.posList = []
        self.annoViewList = []
        self.posPath = ''
        self.idx = 0
        self.pathIdx = 0
        self.dictLength = 51         # should be odd, otherwise fix checkBuffers()!
        
        self.posList = sorted(posList)
        self.posPath = posList[0]
        
        self.annoAltStart = None
        
        self.vLL = VideoLoaderLuncher()
#         time.sleep(10)
        self.vLL.createdVideoLoader.connect(self.linkToAnnoview)
        self.newVideoLoader.connect(self.vLL.lunchVideoLoader)
        self.deleteVideoLoader.connect(self.vLL.deleteStuff)
        
        
        self.loadProgressive = False
        
        self.loadingFinished = False
        self.annotationBundle = []
        
        self.fileChangeCB = fileChangeCb
        
        
        # always do that at the end
        self.checkBuffer()
    
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
        try:
            frame = self.videoDict[self.posPath].getFrame(self.idx)
        except KeyError:
            cfg.log.exception("accessing video out of scope, fetching...")
            self.fetchVideo(self.posPath)
            #self.getFrame(self.posPath, idx)
            self.getCurrentFrame()
        except RuntimeError as e:
            cfg.log.error("something went wrong during the fetching procedure: error message {0}".format(e.message))
            frame = [[[0,0]], None]
        
        
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
    def getNextFrame(self, increment=1, doBufferCheck=True, emitFileChange=True):
        self.idx += increment
        cfg.log.debug("(videohander) - begin frameno: {0}".format(self.idx))
        if self.idx >= self.videoDict[self.posPath].getVideoLength():
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != self.dictLength:
                        self.idx -= self.videoDict[self.posPath].getVideoLength()                                         
                        self.posPath = pos[i+1]     
                        if emitFileChange:
#                             self.changedFile.emit(self.posPath)
                            self.fileChangeCB(self.posPath)  
                        break
                    else:
                        self.idx = self.videoDict[self.posPath].getVideoLength() -1
                        if doBufferCheck:
                            cfg.log.warning("This is the very last frame, cannot advance further")
                        
        
#         for aV in self.annoViewList:
#             aV.addAnnotationToSceneIncrement(increment * 2)
            
        cfg.log.debug("(videohander) - end")
        return self.getCurrentFrame(doBufferCheck=doBufferCheck)
        
    @cfg.logClassFunction
    def getPrevFrame(self, decrement=1, doBufferCheck=True, emitFileChange=True):
        cfg.log.debug("(videohander) - begin")
        self.idx -= decrement
        if self.idx < 0:
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != 0:
                        self.idx += self.videoDict[self.posPath].getVideoLength() 
                        self.posPath = pos[i-1]               
                        if emitFileChange:
#                             self.changedFile.emit(self.posPath)
                            self.fileChangeCB(self.posPath)   
                        break
                    else:
                        self.idx = 0
                        if doBufferCheck:
                            cfg.log.warning("This is the very first frame, cannot go back further")
                        
#         for aV in self.annoViewList:
#             aV.addAnnotationToSceneIncrement(decrement * 2)
            
        cfg.log.debug("(videohander) - end")
        return self.getCurrentFrame(doBufferCheck=doBufferCheck)
                
    @cfg.logClassFunction
    def checkBuffer(self, updateAnnoViewPositions=True):        
        hS = ((self.dictLength + 1) / 2.0)
        currIdx = self.posList.index(self.posPath)
        
        s = int(currIdx - hS)
        e = int(currIdx + hS +1)
        if s < 0:
            s = 0
        if e > len(self.posList):
            e = len(self.posList)            
        fetchRng = slice(s, e) 
        
        s -= 2
        e += 2
        if s < 0:
            s = 0
        if e > len(self.posList):
            e = len(self.posList)   
          
        delRng = slice(s, e)
        
        # delete all videos that are out of scope
        for vidPath in self.videoDict.keys():
            try:
                self.posList[fetchRng].index(vidPath)
            except ValueError:
                ################################################################ TODO: remove only if annotation is not open                
                cfg.log.debug("delete {0}".format(vidPath))
                if updateAnnoViewPositions:
                    for aV in self.annoViewList:
                        aV.removeAnnotation(vidPath)
                                    
                cfg.log.debug("delete video dict")
#                 self.dump = self.videoDict[vidPath]
                self.deleteVideoLoader.emit([self.videoDict[vidPath]])
                
                # first make sure to not refer anymore to VL
                self.videoDict[vidPath] = None
#                 delete key/value pair
                del self.videoDict[vidPath]
                                
                cfg.log.debug("delete finish")
                
        
        # prefetch all videos that are not prefetched yet
        for vidPath in self.posList[fetchRng]:
            try:
                self.videoDict[vidPath]
            except KeyError:
                self.fetchVideo(vidPath)
        
        
    @cfg.logClassFunction
    def fetchVideo(self, path):
        cfg.log.debug("fetching {0}".format(path))
#         vL = VideoLoader(path)
#         vL.loadedAnnotation.connect(self.updateNewAnnotation)
        self.newVideoLoader.emit([path, self])
        
        
    @cfg.logClassFunction
    @pyqtSlot(list)
    def linkToAnnoview(self, lst):
        """
        Args:
            lst ([path, videoLoader]) 
        """ 
        path = lst[0]
        vL = lst[1]
        self.videoDict[path] = vL
        
    @cfg.logClassFunction
    def addAnnoView(self, annoView):
        for vidPath in self.videoDict:
            if not self.videoDict[vidPath].loading:
                cfg.log.debug("annotation id: {0}".format(id(self.videoDict[vidPath].annotation)))
                annoView.addAnnotation(self.videoDict[vidPath].annotation, vidPath)
                
        self.annoViewList += [annoView]
        
    @cfg.logClassFunction
    def removeAnnoView(self, idx):
        self.annoViewList.pop(idx)
        
    @cfg.logClassFunction
    def updateAnnoViewPositions(self):
        if self.loadingFinished:
            self.loadingFinished = False
            self.loadAnnotationBundle()
            
        for aV in self.annoViewList:
            aV.setPosition(self.posPath, self.idx)
        
    @cfg.logClassFunction
    @pyqtSlot(list)
    def updateNewAnnotation(self, annotationBundle):  
        self.annotationBundle += [annotationBundle]
        self.loadingFinished = True
        
    @cfg.logClassFunction
    def loadAnnotationBundle(self):   
        self.annotationBundle = sorted(self.annotationBundle, key=lambda x: x[1])
        
        for annotationBundle in self.annotationBundle:
            for aV in self.annoViewList:
                aV.addAnnotation(annotationBundle[0], annotationBundle[1], 
                                 addAllAtOnce=(not self.loadProgressive))
            
        self.annotationBundle = []
            
    @cfg.logClassFunction
    def addFrameToAnnotation(self, vialNo, annotator, behaviour):   
        for aV in self.annoViewList:
            aV.addFramesToAnnotation(self.posPath, [self.idx], annotator, 
                                                                    behaviour)
                                                                    
        
        self.videoDict[self.posPath].addAnnotation(vialNo, [self.idx], 
                                                   behaviour, annotator)
                                                                    
    @cfg.logClassFunction
    def annoViewZoom(self, zoomLevel):
        for aV in self.annoViewList:
            aV.setZoom(zoomLevel)
        
    @cfg.logClassFunction
    def addAnnotation(self, vial, annotator, behaviour, confidence):
        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if vial == aV.vialNo:
                        cfg.log.debug("calling aV.addAnno()")
                        aV.addAnno()
                        
        if self.annoAltStart == None:
            self.annoAltStart = bsc.FramePosition(self.videoDict, self.posPath, 
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
                annoEnd = bsc.FramePosition(self.videoDict, self.posPath, self.idx)    
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.frameList[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
            
                for key in rng:
                    self.videoDict[key].annotation.addAnnotation(vial, rng[key], 
                                            annotator, behaviour, confidence)
                                            
                    cfg.log.info("add annotation vial {v}| range {r}| annotator {a}| behaviour {b}| confidence {c}".format(
                                  v=vial, r=rng[key], a=annotator,
                                  b=behaviour, c=confidence))
                    tmpFilename = key.split(".pos")[0] + ".bhvr~"
                    self.videoDict[key].annotation.saveToFile(tmpFilename)
                    
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
                                                self.videoDict[key].annotation,
                                                     key)
                
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
                        aV.eraseAnno()
                        
        if self.annoAltStart == None:
            self.annoAltStart = bsc.FramePosition(self.videoDict, self.posPath, 
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
                annoEnd = bsc.FramePosition(self.videoDict, self.posPath, self.idx)    
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.frameList[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
                self.annoAltStart = None
                
                for key in rng:
                    self.videoDict[key].annotation.removeAnnotation(vial, rng[key], 
                                            annotator, behaviour)
                    tmpFilename = key.split(".pos")[0] + ".bhvr~"
                    self.videoDict[key].annotation.saveToFile(tmpFilename)
                
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
                                                self.videoDict[key].annotation,
                                                     key)
        
                        
    @cfg.logClassFunction
    def escapeAnnotationAlteration(self):
        self.annoAltStart == None
        
        for aV in self.annoViewList:
            aV.escapeAnno()
            
    @cfg.logClassFunction
    def saveAll(self):
        for key in self.videoDict:
            tmpFilename = key.split(".pos")[0] + ".bhvr"
            self.videoDict[key].annotation.saveToFile(tmpFilename)
    
class AnnotationItemLoader(BaseThread):
    annotationStuff = pyqtSignal(list)
    
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
                    
                    
class VideoLoaderLuncher(BaseThread):        
    createdVideoLoader = pyqtSignal(list)   
    
    @cfg.logClassFunction
    def __init__(self):
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
        BaseThread.__init__(self)   
            
        self.VLs = []
        
        self.start()
    
    @cfg.logClassFunction
    def run(self):
        cfg.log.debug("(VideoLoaderLuncher) begin")        
        self.exec_()
        cfg.log.debug("(VideoLoaderLuncher) end")
            
    
    
    @cfg.logClassFunction
    @pyqtSlot(list)
    def lunchVideoLoader(self, lst):
        """
        Args:
            lst ([string, callback])
        """
        cfg.log.debug("begin")
        path = lst[0]
        vH = lst[1]
        if len(self.VLs) == 0:
            cfg.log.debug("create new VideoLoader")
            vL = VideoLoader(path, vH)
        else:
            cfg.log.debug("recycle new VideoLoader")
            vL = self.VLs.pop()
            vL.__init__(path, vH)
            
#         vL.loadedAnnotation.connect(cb)
        self.createdVideoLoader.emit([path, vL])
        cfg.log.debug("finish")
            
    @cfg.logClassFunction
    def deleteStuff(self, lst):
        vL = lst[0]
        
        self.VLs += [vL]
        
if __name__ == "__main__":
    # settings    
    
    # set qt stuff up and lunch the thing
    
    app = QApplication(sys.argv)
    
    path = '/run/media/peter/Elements/peter/data/tmp-20130506'
    w = videoPlayer(path, videoFormat='avi')
    
    app.connect(app, SIGNAL("aboutToQuit()"), w.stopVideo)
    w.quit.connect(app.quit)
    
    sys.exit(app.exec_())
