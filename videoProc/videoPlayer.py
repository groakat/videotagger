import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtGui import *
from PyQt4.QtCore import * 
from PyQt4.QtOpenGL import * 

from videoPlayer_auto import Ui_Form

from pyTools.system.videoExplorer import *
from pyTools.imgProc.imgViewer import *
from pyTools.misc.basic import *

import numpy as np
#import matplotlib as mpl
import pylab as plt
import time


from qimage2ndarray import *

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



class videoPlayer(QMainWindow):
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
        self.show()
        
        self.posList = self.providePosList(path)    
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.posList))
        
        self.videoFormat = videoFormat
        self.idx = 0       
        self.play = False
        self.frameIdx = -1
        self.showTraject = False
        self.trajNo = 1
        self.trajLabels = []
        self.frames = []
        self.increment = 0
        self.stop = False
        
        self.vh = VideoHandler(self.fileList)
        self.vh.changedFile.connect(self.changeVideo)
        
        self.filterList = []
        
        self.vEs = []
        for i in range(4):
            self.vEs.append(videoExplorer())
        
        #self.setVideo(0)
        
        
        
        self.updateFrameList(range(2000))
        
        self.configureUI() 
        
        self.setBackground("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        
        #glMatrixMode(GL_PROJECTION)
        
        
        
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
        
    def configureUI(self):
        
        self.xFactor = self.ui.label.width() / 1920.0
        self.yFactor = self.ui.label.height() / 1080.0
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        self.ui.lbl_v0.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v1.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v2.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v3.resize(self.xFactor*64, self.yFactor*64)
        
        self.ui.lbl_v0.setStyleSheet("background-color: rgba(255, 255, 255, 10);")
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
        self.createAnnoViews()
        
        
    def createAnnoViews(self):
        self.annoViewList = []
             
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["peter"], color = QColor(0,0,255,150))]
        self.annoViewList[-1].setGeometry(QRect(70, 715, 701, 23))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1]) 
        
        
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["matt"],color = QColor(0,255,0,150))]
        self.annoViewList[-1].setGeometry(QRect(70, 730, 701, 23))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])        
        
        self.annoViewList += [AnnoView(self, vialNo=0, annotator=["peter"],color = QColor(255,0,0,150))]
        self.annoViewList[-1].setGeometry(QRect(70, 745, 701, 23))
        self.annoViewList[-1].show()
        self.vh.addAnnoView(self.annoViewList[-1])      
        
        for aV in self.annoViewList:
            print aV
        
    def keyPressEvent(self, event):
        key = event.key()
                
        if key == Qt.Key_S:
            self.increment = 0
            self.play = True
            
        if key == Qt.Key_D:
            self.increment = 1
            self.showNextFrame(self.increment)
            self.vh.annoViewZoom(6)
            self.play = False
            
        if key == Qt.Key_E:
            self.increment = 1
            self.vh.annoViewZoom(4)
            self.play = True
            
        if key == Qt.Key_Y:
            self.increment = 3
            self.vh.annoViewZoom(2)
            self.play = True
            
        if key == Qt.Key_O:
            self.increment = 5
            #self.vh.annoViewZoom(1)
            self.play = True
            
        if key == Qt.Key_C:
            self.increment = 10
            #self.vh.annoViewZoom(0)
            self.play = True
        
        if key == Qt.Key_A:
            self.increment = -1
            self.showNextFrame(self.increment)
            self.vh.annoViewZoom(6)
            self.play = False
            
        if key == Qt.Key_Q:
            self.increment = -1
            self.vh.annoViewZoom(4)
            self.play = True
            
        if key == Qt.Key_T:
            self.increment = -3
            self.vh.annoViewZoom(2)
            self.play = True
            
        if key == Qt.Key_U:
            self.increment = -5
            #self.vh.annoViewZoom(1)
            self.play = True
            
        if key == Qt.Key_X:
            self.increment = -10
            #self.vh.annoViewZoom(0)
            self.play = True
            
        if key == Qt.Key_I:
            print "position length:", self.vh.getCurrentPositionLength()
            print "video length:", self.vh.getCurrentVideoLength()
        
        
    def updateFrameList(self, intList):
        self.frameList = MyListModel(intList, self) 
        self.ui.lv_frames.setModel(self.frameList)
        
    def updateJumpList(self, intList):
        self.jmpIdx = intList
        
        strList = [str(x) for x in intList]
        self.jumpList = MyListModel(strList, self) 
        self.ui.lv_jmp.setModel(self.jumpList)
        
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
        
    def updateLabel(self, lbl, p, img):
        if img is not None:
            qi = array2qimage(img)
            pixmap = QPixmap()
            px = QPixmap.fromImage(qi)        
            #lbl.setScaledContents(True)
            lbl.setPixmap(px)
            
                
        newX = p[1] - 32 #lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = p[0] - 32 #lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
        
        lbl.setPos(newX,newY)
        #lbl.setStyleSheet("border: 1px dotted rgba(255, 0, 0, 75%);");
        #lbl.raise_()
        #lbl.update()
        
    def updateOriginalLabel(self, lbl, img):
        qi = array2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lbl.setScaledContents(False)
        lbl.setPixmap(px)
        
        lbl.update()
        
    
    def showNextFrame(self, increment=1):
        #if self.frames != []:
        #    self.frames.pop(0)
        self.frames = []    
        
        offset = 5  
        
        if increment > 0:
            self.frames += [self.vh.getNextFrame(increment)]
        elif increment < 0:
            self.frames += [self.vh.getPrevFrame(-increment)]
        else:
            self.frames += [self.vh.getCurrentFrame()]
            increment = 8
            offset = (self.trajNo / 2) 
        
        i = 0
        while len(self.frames) < self.trajNo:
            i += 1
            self.frames += [self.vh.getTempFrame(increment * (i - offset))] 
        
        for i in range(self.trajNo-1, -1, -1):
            frame = self.frames[i]
            if i == 0:
                self.updateLabel(self.lbl_v0, frame[0][0], frame[1][0])
                self.updateLabel(self.lbl_v1, frame[0][1], frame[1][1])
                self.updateLabel(self.lbl_v2, frame[0][2], frame[1][2])
                self.updateLabel(self.lbl_v3, frame[0][3], frame[1][3])
            
                self.updateOriginalLabel(self.ui.lbl_v0_full, frame[1][0])
                self.updateOriginalLabel(self.ui.lbl_v1_full, frame[1][1])
                self.updateOriginalLabel(self.ui.lbl_v2_full, frame[1][2])
                self.updateOriginalLabel(self.ui.lbl_v3_full, frame[1][3])
            else:
                self.updateLabel(self.trajLabels[i][0], frame[0][0], None)
                self.updateLabel(self.trajLabels[i][1], frame[0][1], None)
                self.updateLabel(self.trajLabels[i][2], frame[0][2], None)
                self.updateLabel(self.trajLabels[i][3], frame[0][3], None)
        
        if self.showTraject:
            pass
        
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
        
    def setBackground(self, path):
        a = plt.imread(path)
        
        qi = array2qimage(a*255)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        #~ 
        #~ self.ui.label.setScaledContents(True)
        #~ self.ui.label.setPixmap(px)
        
        self.videoView = QGraphicsView(self)        
        self.videoView.setGeometry(QRect(10, 10, 1920/2, 1080/2))
        self.videoScene = QGraphicsScene(self)
        self.videoScene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.videoScene.setSceneRect(QRectF(0, 0, 1920, 1080))
        
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
        
        fps = 25.0
        updateRate = 33.0 * 12
        
        print "start Video"
        
        i = 0
        t = time.time()
        while not self.stop:
            if self.play:            
                self.showNextFrame(self.increment)
                
                if self.increment == 0:
                    self.play = False
            else:
                time.sleep(0.003)
                
            if (i % 5) == 0:
                frameNo = self.vh.getCurrentFrameNo()
                self.ui.lv_frames.setCurrentIndex(self.frameList.index(frameNo,0))
                QApplication.processEvents()
                
            if (i % 1760) == 0:
                dt = time.time() - t
                print("fps: {0}".format(1760 / dt))
                t = time.time()
                    
            i += 1
        
    def providePosList(self, path):
        fileList  = []
        posList = []
        print "scaning files..."
        for root,  dirs,  files in os.walk(path):
            for f in files:
                if f.endswith('npy'):
                    path = root + '/' + f
                    fileList.append(path)
                    
        self.fileList = sorted(fileList)
        print "scaning files done"
        return posList
        
        
    def stopVideo(self):
        self.play = False
        
    def generatePatchVideoPath(self, posPath, vialNo):
        """
        strips pos path off its postfix and appends it with the vial + video
        format postfix
        """
        return posPath.split('.pos')[0] + '.v{0}.{1}'.format(vialNo, 
                                                            self.videoFormat)
                                                            
    def setVideo(self, idx):
        self.ui.lv_paths.setCurrentIndex(self.lm.index(idx,0))
        self.ui.sldr_paths.setSliderPosition(idx)
        for i in range(len(self.vEs)):
            f = self.generatePatchVideoPath(self.fileList[idx], i)
            self.vEs[i].setVideoStream(f, info=False, frameMode='RGB')
            
        self.pos = self.posList[idx]
        
        if self.filterList != []:
            lst = self.filterList[0][idx]
            for i in range(1, len(self.filterList)):
                lst = np.logical_or(lst, [self.filterList[i][idx]])
                
            lst = np.arange(len(lst.flatten()))[lst.flatten()]
            self.updateJumpList(list(lst))
        
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
            

    def selectVideo(self, idx):
        self.idx = idx
        #self.setVideo(self.idx)
        self.vh.getFrame(self.fileList[idx], 0)
        
    def selectVideoLV(self, mdl):
        self.idx = mdl.row()   
        self.selectVideo(self.idx)
        
    def selectFrame(self, mdl):
        idx = mdl.row()       
        print "select frame", idx
        self.setFrame(idx)
        
    def selectFrameJump(self, mdl):
        idx = mdl.row()       
        print "select frame idx", idx, self.jmpIdx[idx]
        self.setFrame(self.jmpIdx[idx])
        
    def compDistances(self):
        posList, idx = self.vh.getCurrentPosList()
        print "start computing the distances..."
        self.dists = computeDistancesFromPosList(posList, self.fileList)
        print "finished computing distances"
        
        print "start computing the jumps..."
        self.filterList = filterJumps(posList, self.dists, 25)
        print "finished computing jumps"
        
        #idx = 0
        lst = self.filterList[0][idx]
        for i in range(1, len(self.filterList)):
            lst = np.logical_or(lst, [self.filterList[i][idx]])
            
        lst = np.arange(len(lst.flatten()))[lst.flatten()]
        self.updateJumpList(list(lst))
        
    def loadNewVideo(self):
        self.videoList[self.fileList[0]] = VideoLoader(self.fileList[0])
        #self.prefetchVideo(self.fileList[0])
        
    def showTrajectories(self, state):
        self.showTraject = bool(state)        
        
        if self.showTraject:
            self.trajNo = 50
        else:
            self.trajNo = 1
            
        if self.trajLabels != []:
            for i in range(len(self.trajLabels)):
                for k in range(len(self.trajLabels[i])):
                    #self.trajLabels[i].pop().setVisible(False)
                    self.videoScene.removeItem(self.trajLabels[i].pop())
                    
        self.ui.label.update()
        self.trajLabels = []
        for i in range(self.trajNo):
            lbl = []
            for k in range(4):
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
    
    @pyqtSlot(list)
    def addVideo(self, videoList):
        print "slot"
        self.videoList += videoList
        
        print self.videoList
        
    @pyqtSlot(str)
    def changeVideo(self, filePath):
        print "Change video to", filePath
        posInLst = self.fileList.index(filePath)
                
        self.ui.lv_paths.setCurrentIndex(self.lm.index(posInLst,0))
        #self.updateFrameList(range(self.vh.getCurrentVideoLength()))
        
    def prefetchVideo(self, posPath):        
        self.vl = VideoLoader()
        self.vl.loadedVideos.connect(self.addVideo)
        self.vl.loadVideos(posPath)
        
    def testFunction(self):
        print "testFunction"
        self.vh.addFrameToAnnotation(0, "peter", "just kidding")
        
    def addAnno(self):
        self.vh.addAnnotation(0, "peter", "just testing", confidence=1)
        
    def eraseAnno(self):
        self.vh.eraseAnnotation(0, "peter", "just testing")
        
class AnnoView(QGraphicsView):
    
    def __init__(self, parent, vialNo=None, behaviourName=None, annotator=None,
                color=None):
        super(AnnoView, self).__init__(parent)
        #QGraphicsView.__init__(parent)
        
        # initialization of parameters
        self.annotationDict = dict()
        self.color = QColor(0,255,0,150)
        self.zoomLevels = [0.5, 0.6, 0.8, 1, 2, 5, 10]
        self.zoom = 4
        self.lines = dict()
        self.frames = dict()
        self.absIdx = dict()
        self.chunks = dict()
        
        self.scene = None
        self.selKey = None
        self.idx = None
        
        self.boxHeight = 10
        
        #filters
        self.vialNo = None
        self.behaviourName=None
        self.annotator=None
        
        geo = self.geometry()
        geo.setHeight(self.boxHeight + 6)
        self.setGeometry(geo)
        
        # setting values
        self.scene = QGraphicsScene(parent)
        #self.scene.setSceneRect(QRectF(-50000, -20, 50000, 20))
        self.setScene(self.scene)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.vialNo = vialNo
        self.behaviourName = behaviourName
        self.annotator = annotator
        
        self.setViewport(QGLWidget(parent))
        
        if color == None:
            color = QColor(0,255,0,150)
            
        self.color = color
        
    def addAnnotation(self, annotation, key):
        self.annotationDict[key] = annotation.filterFrameList(self.vialNo,
                                                            self.behaviourName,
                                                            self.annotator)
            
        if True:
            self.addAnnotationToScene(key)            
        else:
            # does not work. An idea would be to update a second scene
            # and swap the scenes, rather than adding the items to
            # the scene in addPrefetchedAnnoToScene
            aL = AnnotationItemLoader(key, self.annotationDict, self.absIdx,
                                        self.color, QColor(0,0,0,0))
            aL.annotationStuff.connect(self.addPrefetchedAnnoToScene)
            aL.start()
        
    @pyqtSlot(list)
    def addPrefetchedAnnoToScene(self, lst):
        t = time.time()
        print "addPrefetchedAnnoToScene: begin"
        for key in lst[0].keys():
            self.chunks[key] = QGraphicsRectItem(lst[0][key])
            self.absIdx[key] = deepcopy(lst[1][key])
            self.lines[key] = deepcopy(lst[2][key])
            self.frames[key] = deepcopy(lst[3][key])
            self.scene.addItem(self.chunks[key])
            
        lst[-1].processedSignal = True
        print "addPrefetchedAnnoToScene: end", time.time() - t
        
    def removeAnnotation(self, key):
        ######################################################################## TODO shift only if absIdx goes out of int range
        #shift = len(self.annotationDict[key].frameList)
        #self.shiftScene(shift)
        self.scene.removeItem(self.chunks[key])    
        del self.chunks[key] 
        del self.lines[key] 
        del self.frames[key]
        del self.absIdx[key]
        del self.annotationDict[key]
        #self.clearScene()
        #self.populateScene()
                
    def clearScene(self):
        keys = self.chunks.keys()
        for key in keys:
            self.scene.removeItem(self.chunks[key])       
                
        self.chunks.clear()
        self.lines.clear()
        self.frames.clear()
        self.absIdx.clear()
            
        # ignore any non-custom warnings that may be in the list            
                
        self.lines = dict()
        self.frames = dict()
        self.absIdx = dict()
        self.chunks = dict()      
        
    
        
    def addAnnotationToScene(self, key):
        """
        Key needs to be in self.annotationDict !!
        """
        keys = sorted(self.annotationDict.keys())
        
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
            print("addAnnotationToScene: tried to insert an annotation in the middle." + 
                 " It only makes sense to append, or prepend. Trying to clear and" +
                 " repopulate entirely")
            self.clearScene()
            self.populateScene()
            return
        
        print "i", i, "key", key
        
        boxHeight = self.boxHeight
        
        aCol = self.color
        uCol = QColor(0,0,0,0)
        
        aBrush = QBrush(aCol)
        aPen = QPen(uCol)
        
        uPen = QPen(uCol)
        uBrush = QBrush(uCol)
        
        self.lines[key] = []
        self.frames[key] = []
        chunkLength = len(self.annotationDict[key].frameList)
        self.chunks[key] = self.scene.addRect(QRectF(i, 0, chunkLength, boxHeight))        
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
            
    
    def populateScene(self):
        t = time.time()
        print "populate Scene: begin"
        keys = sorted(self.annotationDict.keys())
        i = 0
        
        boxHeight = self.boxHeight
        
        aCol = self.color
        uCol = QColor(0,0,0,0)
        
        aBrush = QBrush(aCol)
        aPen = QPen(uCol)
        
        uPen = QPen(uCol)
        uBrush = QBrush(uCol)
        
        for key in keys:
            self.lines[key] = []
            self.frames[key] = []
            self.absIdx[key] = []
            chunkLength = len(self.annotationDict[key].frameList)
            self.chunks[key] = self.scene.addRect(QRectF(i, 0, chunkLength, boxHeight)   )         
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
        
        
    def shiftScene(self, shift):
        t = time.time()
        print "shift Scene: begin"
        keys = sorted(self.annotationDict.keys())        
        trans = QTransform().translate(shift, 0)
        
        for key in keys:                
            self.chunks[key].setTransform(trans)        
            self.absIdx[key] += shift
                
        print "shift Scene: end", time.time() - t
        
        
    def addFramesToAnnotation(self, key, frames, annotator, behaviour):
        """
        
        Args:
            frames (list of int)
        """
        inScope = False
        if self.annotator is not None:
            if annotator == self.annotator:
                inScope = True
        else:
            inScope = True
        if self.behaviourName is not None:
            if behaviour == self.behaviourName:
                inScope = True
        else:
            inScope = True
                
        if inScope:
            for frame in frames:                    
                self.scene.removeItem(self.frames[key][frame])
                col = self.color
                i = self.absIdx[key][frame]
                boxHeight = self.boxHeight
                self.frames[key][frame] = \
                            (self.scene.addRect(QRectF(i, 0, 1, boxHeight), 
                                                QPen(col), QBrush(col)))
            
        
    def setPosition(self, key, idx):
        self.selKey = key
        self.idx = idx
        self.addTempAnno()
        self.updateGraphicView()
        
    def setFilter(self, vialNo=None, behaviourName=None, annotator=None):
        self.vialNo = vialNo
        self.behaviourName = behaviourName
        self.annotator = annotator
        
    def setZoom(self, zoomLevel):
        #scale absolute
        scale = self.zoomLevels[self.zoom]
        if self.zoom < 4:
            for key in self.lines:
                for line in self.lines[key]:
                    line.setVisible(False)
        else:
            for key in self.lines:
                for line in self.lines[key]:
                    line.setVisible(True)
        
        self.setTransform(QTransform().scale(scale, 1))
        
        self.zoom = zoomLevel
        self.updateGraphicView()
        
    def setColor(self, color):
        self.color = color
        self.clearScene()
        self.populateScene()
        
    def updateGraphicView(self):
        
        if self.selKey is not None:
            self.centerOn(self.frames[self.selKey][self.idx])
            
        #self.update()
        
    
    
    addingAnno = False
    tempAnno = dict()
    def addAnno(self):
        if not self.addingAnno:
            #self.tempStart = [self.selKey, self.idx]
            self.tempStart = FramePosition(self.annotationDict, self.selKey, 
                                                                    self.idx)
            self.addingAnno = True
        else:
            self.addingAnno = False  
            for key in self.tempAnno:
                for i in  self.tempAnno[key]:
                    idx = self.absIdx[key][i]
                    self.scene.removeItem(self.frames[key][i])
                    col = self.color
                    self.frames[key][i] = \
                            (self.scene.addRect(QRectF(idx, 0, 1, self.boxHeight),
                            QPen(QColor(0,0,0,0)), QBrush(col)))
                    self.scene.removeItem(self.tempAnno[key][i])
            
            # save range to original annotation
            # saveToFile
            self.tempAnno = dict()
            
        self.addTempAnno()
            
    erasingAnno = False
    def eraseAnno(self):
        if not self.erasingAnno:
            #self.tempStart = [self.selKey, self.idx]
            self.tempStart = FramePosition(self.annotationDict, self.selKey, 
                                                                    self.idx)
            self.erasingAnno = True
            self.tempAnno = dict()
            self.addTempAnno()
        else:
            self.erasingAnno = False
            for key in self.tempAnno:
                for i in  self.tempAnno[key]:
                    idx = self.absIdx[key][i]
                    self.scene.removeItem(self.frames[key][i])
                    col = QColor(0,0,0,0)
                    self.frames[key][i] = \
                            (self.scene.addRect(QRectF(idx, 0, 1, self.boxHeight),
                            QPen(QColor(0,0,0,0)), QBrush(col)))
                
            # erase in original annotation
            # save to file
            self.tempAnno = dict()           
            
            
    def addTempAnno(self):
        if self.addingAnno:
            for key in self.tempAnno:
                for idx in  self.tempAnno[key]:
                    self.scene.removeItem(self.tempAnno[key][idx])
                    #del self.tempAnno[idx]           
            
            tempEnd = FramePosition(self.annotationDict, self.selKey, self.idx + 1)            
            rng = generateRangeValuesFromKeys(self.tempStart, tempEnd) 
                                                    
            #print rng
                                                    
            self.tempAnno = dict()
            for key in rng:
                self.tempAnno[key] = dict()
                for i in rng[key]:
                    idx = self.absIdx[key][i]
                    col = self.color
                    self.tempAnno[key][i] = \
                        (self.scene.addRect(QRectF(idx, 0, 1, self.boxHeight),
                        QPen(QColor(0,0,0,0)), QBrush(col)))
                
        if self.erasingAnno:            
            for key in self.tempAnno:
                for idx in self.tempAnno[key]:
                    self.frames[key][idx].setVisible(True)  
            
            tempEnd = FramePosition(self.annotationDict, self.selKey, self.idx + 1)            
            rng = generateRangeValuesFromKeys(self.tempStart, tempEnd)                                                                  
            
            self.tempAnno = dict()
            for key in rng:
                self.tempAnno[key] = dict()
                for i in rng[key]:
                    idx = self.absIdx[key][i]
                    self.tempAnno[key][i] = self.frames[key][idx]
                    self.frames[key][idx].setVisible(False)
                
    #~ def generateRangeValuesFromKeys(self, start, end):
        #~ """        
        #~ Args:
            #~ start ([dict key, int])
            #~ end ([dict key, int])
        #~ """
        #~ 
        #~ c = [start,end]
        #~ if start[0] != end[0]:
            #~ c.sort(key=lambda x: x[0])
        #~ else:
            #~ c.sort(key=lambda x: x[1])
        #~ s = c[0]
        #~ e = c[1]
            #~ 
        #~ 
        #~ rng = dict()
        #~ isWithinRange = False
        #~ for key in sorted(self.annotationDict.keys()):
            #~ rngS = None
            #~ rngE = None
            #~ 
            #~ if key == s[0]:
               #~ isWithinRange = True
               #~ rngS = s[1]
            #~ else:
                #~ rngS = 0
               #~ 
            #~ if key == e[0]:
                #~ isWithinRange = False
                #~ rngE = e[1]
                #~ rng[key] = range(rngS, rngE)
                #~ return rng
            #~ else:
                #~ rngE = len(self.annotationDict[key].frameList)
            #~ 
            #~ if isWithinRange:
                #~ rng[key] = range(rngS, rngE)
                #~ 
        #~ return rng
                #~ 
        
class BaseThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.exiting = False

    def __del__(self):        
        print "deleting"
        self.exiting = True
        self.wait()
        
from IPython.parallel import Client
# Subclassing QObject and using moveToThread
# http://labs.qt.nokia.com/2007/07/05/qthreads-no-longer-abstract/
class VideoLoader(BaseThread):        
    loadedVideos = pyqtSignal(list) 
    loadedAnnotation = pyqtSignal(list)
    finished = pyqtSignal()   

    def __del__(self):        
        print "deleting"
        self.exiting = True
        self.wait()
                
        if self.annotation is not None:
            self.annotation.saveToFile(self.posPath.split('.pos')[0] + '.bhvr')
    
    def __init__(self, posPath):
        BaseThread.__init__(self)        
        
        self.loading = False
        
        self.videoLength = -1
        self.frameList = []
        
        self.annotation = None # annotation object
        
        self.posPath = posPath      
        self.loadVideos()

    def loadVideos(self):    
        self.exiting = False
        self.loading = True
        self.start()        
        
    def run(self):
        print "loadVideos"
        rc = Client()
        print rc.ids
        
        dview = rc[:]        
        lbview = rc.load_balanced_view()   
        
        #@lbview.parallel(block=True)
        def loadVideo(f, vialNo):    
            from qimage2ndarray import array2qimage
            from pyTools.system.videoExplorer import videoExplorer
            import numpy as np    
            
            vE = videoExplorer()        
            
            
            qi = [vE.getFrame(f, info=False, frameMode='RGB')]
            for frame in vE:
                qi += [frame]
                        
            ret = dict()
            
            ret["vialNo"] = vialNo
            ret["qi"] = qi
            return ret     
            
        def loadAnnotation(posPath, videoLength):
            from pyTools.videoProc.annotation import Annotation
            from os.path import isfile            
            
            f = posPath.split('.pos')[0] + '.bhvr'
            if isfile(f):
                out = Annotation()
                try:
                    out.loadFromFile(f)
                except:
                    print("load annotation of "+f+" failed, reset annotaions")
                    out = Annotation(frameNo=videoLength, vialNames=["Abeta +RU",
                                                                 "ABeta -RU",
                                                                 "dilp",
                                                                 "wDah(+)"])
            else:
                out = Annotation(frameNo=videoLength, vialNames=["Abeta +RU",
                                                                 "ABeta -RU",
                                                                 "dilp",
                                                                 "wDah(+)"])
            return out
            
        results = []
        for i in range(4):
            f = self.posPath.split('.pos')[0] + '.v{0}.{1}'.format(i, 'avi')
            results += [lbview.apply_async(loadVideo, f, i)]
        
        print "videoLoader: waiting for process..."
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
        
        self.frameList = [0]*4
        for i in range(4):
            # copy data
            ar = results[i].get()
            self.frameList[ar["vialNo"]] = ar["qi"]
            # delete data from cluster
            msgId = results[i].msg_id
            #~ del lbview.results[msgId]
            del rc.results[msgId]
            del rc.metadata[msgId]
        
        # close client to close socket connections
        rc.close()
        
        if not self.exiting:
            self.pos = np.load(self.posPath)
            self.videoLength = len(self.frameList[0])
        
        if not self.exiting:
            self.annotation = loadAnnotation(self.posPath, self.videoLength)
        
        print "finished computing, emiting signal"
        
        self.loading = False
        self.finished.emit()  
        self.loadedAnnotation.emit([self.annotation, self.posPath])
        
    def getVideoLength(self):
        if not self.loading:
            return self.videoLength
        else:
            raise RuntimeError("calling length, before video finished")
        
    def getPositionLength(self):
        if not self.loading:
            return len(self.pos)
        else:
            raise RuntimeError("calling length, before video finished loading")
            
    def getFrame(self, idx):
        if self.loading:
            self.wait()
            
        if self.exiting:
            return
        
        if idx < self.videoLength:
            out = []
            for i in range(len(self.frameList)):
                out += [self.frameList[i][idx]]
                
            return [self.pos[idx], out]
        else:
            raise RuntimeError("Video frame was not available")
            
    def getPosList(self):
        if not self.loading2:
            return self.pos
        else:
            raise RuntimeError("calling posList, before video finished loading")
            
    def addAnnotation(self, vialNo, frames, behaviour, annotator):
        if not self.loading:
            self.annotation.addAnnotation(vialNo, frames, behaviour, annotator)

class VideoHandler(QObject):       
    
    changedFile = pyqtSignal(str)
    
    def __init__(self, posList):
        super(VideoHandler, self).__init__()        
        
        self.videoDict = dict()
        self.posList = []
        self.annoViewList = []
        self.posPath = ''
        self.idx = 0
        self.pathIdx = 0
        self.dictLength = 9         # should be odd, otherwise fix checkBuffers()!
        
        self.posList = sorted(posList)
        self.posPath = posList[0]
        self.checkBuffer()
        
        self.annoStart = None
    
    def setFrameIdx(self, idx):
        self.idx = idx
    
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
    
    def getCurrentVideoLength(self):
        return self.videoDict[self.posPath].getVideoLength()
        
    def getCurrentPositionLength(self):
        return self.videoDict[self.posPath].getPositionLength()
        
    def getCurrentFrameNo(self):
        return self.idx
    
    def getFrame(self, posPath, idx):        
        self.idx = idx
        self.posPath = posPath
        return self.getCurrentFrame()
        
        
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
            print "something went wrong during the fetching procedure"
                
        self.idx = idx
        self.posPath = path
        
        return frame
        
    def getCurrentFrame(self, doBufferCheck=True):      
        try:
            frame = self.videoDict[self.posPath].getFrame(self.idx)
        except KeyError:
            print "accessing video out of scope, fetching..."
            self.fetchVideo(self.posPath)
            #self.getFrame(self.posPath, idx)
            self.getCurrentFrame()
        except RuntimeError:
            print "something went wrong during the fetching procedure"
        
        
        if doBufferCheck:
            self.updateAnnoViewPositions()
            self.checkBuffer()
        return frame
        
    def getBufferFrame(self, posPath, idx):    
        frame = []  
        try:
            frame = self.videoDict[posPath].getFrame(idx)
            
        except KeyError:
            pass
            
        return frame
                
    def getNextFrame(self, increment=1, doBufferCheck=True, emitFileChange=True):
        self.idx += increment
        if self.idx >= self.videoDict[self.posPath].getVideoLength():
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != self.dictLength:
                        self.idx -= self.videoDict[self.posPath].getVideoLength()                                         
                        self.posPath = pos[i+1]     
                        if emitFileChange:
                            self.changedFile.emit(self.posPath)  
                        break
                    else:
                        self.idx = self.videoDict[self.posPath].getVideoLength() -1
                        print "This is the very last frame, cannot advance further"
                        
        return self.getCurrentFrame(doBufferCheck=doBufferCheck)
        
    def getPrevFrame(self, decrement=1, doBufferCheck=True, emitFileChange=True):
        self.idx -= decrement
        if self.idx < 0:
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != 0:
                        self.idx += self.videoDict[self.posPath].getVideoLength() 
                        self.posPath = pos[i-1]               
                        if emitFileChange:
                            self.changedFile.emit(self.posPath) 
                        break
                    else:
                        self.idx = 0
                        print "This is the very first frame, cannot go back further"
                        
        return self.getCurrentFrame(doBufferCheck=doBufferCheck)
                
    def checkBuffer(self):        
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
                self.posList[delRng].index(vidPath)
            except ValueError:
                ################################################################ TODO: remove only if annotation is not open
                for aV in self.annoViewList:
                    aV.removeAnnotation(vidPath)
                del self.videoDict[vidPath]
                
        
        # prefetch all videos that are not prefetched yet
        for vidPath in self.posList[fetchRng]:
            try:
                self.videoDict[vidPath]
            except KeyError:
                self.fetchVideo(vidPath)
        
        
    def fetchVideo(self, path):
        print "fetching", path
        vL = VideoLoader(path)
        vL.loadedAnnotation.connect(self.updateNewAnnotation)
        self.videoDict[path] = vL
        
    def addAnnoView(self, annoView):
        for vidPath in self.videoDict:
            if not self.videoDict[vidPath].loading:
                annoView.addAnnotation(self.videoDict[vidPath].annotation, vidPath)
                
        self.annoViewList += [annoView]
        
    def removeAnnoView(self, idx):
        self.annoViewList.pop(idx)
        
    def updateAnnoViewPositions(self):
        for aV in self.annoViewList:
            aV.setPosition(self.posPath, self.idx)
        
    @pyqtSlot(list)
    def updateNewAnnotation(self, annotationBundle):
        for aV in self.annoViewList:
            aV.addAnnotation(annotationBundle[0], annotationBundle[1])
            
    def addFrameToAnnotation(self, vialNo, annotator, behaviour):
        for aV in self.annoViewList:
            aV.addFramesToAnnotation(self.posPath, [self.idx], annotator, 
                                                                    behaviour)
                                                                    
        
        self.videoDict[self.posPath].addAnnotation(vialNo, [self.idx], 
                                                   behaviour, annotator)
                                                                    
    def annoViewZoom(self, zoomLevel):
        for aV in self.annoViewList:
            aV.setZoom(zoomLevel)
        
    def addAnnotation(self, vial, annotator, behaviour, confidence):
        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if vial == aV.vialNo:
                        print "addAnnotation"
                        aV.addAnno()
                        
        if self.annoStart == None:
            self.annoStart = FramePosition(self.videoDict, self.posPath, 
                                                                    self.idx)
        else:
            annoEnd = FramePosition(self.videoDict, self.posPath, self.idx + 1)            
            rng = generateRangeValuesFromKeys(self.annoStart, annoEnd)
            self.annoStart = None
            
            for key in rng:
                self.videoDict[key].annotation.addAnnotation(vial, rng[key], 
                                        annotator, behaviour, confidence)
                                        
                print "add annotation", vial, rng[key], annotator, behaviour, confidence
                tmpFilename = key.split(".pos")[0] + ".bhvr~"
                self.videoDict[key].annotation.saveToFile(tmpFilename)
        
    def eraseAnnotation(self, vial, annotator, behaviour):
        for aV in self.annoViewList:
            if aV.behaviourName == None \
            or behaviour == aV.behaviourName \
            or behaviour in aV.behaviourName:
                if aV.annotator == None \
                or annotator == aV.annotator \
                or annotator in aV.annotator:
                    if vial == aV.vialNo:
                        print "eraseAnnotation"
                        aV.eraseAnno()
                        
        if self.annoStart == None:
            self.annoStart = FramePosition(self.videoDict, self.posPath, 
                                                                    self.idx)
        else:
            annoEnd = FramePosition(self.videoDict, self.posPath, self.idx + 1)            
            rng = generateRangeValuesFromKeys(self.annoStart, annoEnd)
            self.annoStart == None
            
            for key in rng:
                self.videoDict[key].annotation.removeAnnotation(vial, rng[key], 
                                        annotator, behaviour)
                tmpFilename = key.split(".pos")[0] + ".bhvr~"
                self.videoDict[key].annotation.saveToFile(tmpFilename)
    
                        
                        
class AnnotationItemLoader(BaseThread):
        annotationStuff = pyqtSignal(list)
        
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
                print("addAnnotationToScene: tried to insert an annotation in the middle." + 
                     " It only makes sense to append, or prepend. Trying to clear and" +
                     " repopulate entirely")
                self.clearScene()
                self.populateScene()
                return
            
            print "i", i, "key", key
            
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
            
            print "end of worker thread for", key
            
            #~ while(True):
                #~ if self.processedSignal:
                    #~ del self
                #~ else:
                    #~ self.msleep(100)
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    path = '/run/media/peter/Elements/peter/data/tmp-20130506'
    w = videoPlayer(path, videoFormat='avi')
    
    sys.exit(app.exec_())
