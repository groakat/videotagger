import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import * 
from videoPlayer_auto import Ui_Form

from pyTools.system.videoExplorer import *
from pyTools.imgProc.imgViewer import *

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
        
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.pb_compDist.clicked.connect(self.compDistances)
        self.ui.pb_test.clicked.connect(self.loadNewVideo)
        
        self.ui.sldr_paths.valueChanged.connect(self.selectVideo)
        self.ui.lv_frames.activated.connect(self.selectFrame)
        self.ui.lv_jmp.activated.connect(self.selectFrameJump)
        self.ui.lv_paths.activated.connect(self.selectVideoLV)
        
    def configureUI(self):
        
        self.xFactor = self.ui.label.width() / 1920.0
        self.yFactor = self.ui.label.height() / 1080.0
        self.xOffset = -32 + (self.xFactor*64) / 2
        self.yOffset = -32 + (self.yFactor*64) / 2
        
        self.ui.lbl_v0.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v1.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v2.resize(self.xFactor*64, self.yFactor*64)
        self.ui.lbl_v3.resize(self.xFactor*64, self.yFactor*64)
        
        self.ui.lv_paths.setCurrentIndex(self.lm.index(0,0))
        
    def keyPressEvent(self, event):
        key = event.key()
        showFrame = False
        
        if key == Qt.Key_D:
            self.showNextFrame(1)
            showFrame = True
            
        if key == Qt.Key_E:
            self.showNextFrame(5)
            showFrame = True
        
        if key == Qt.Key_A:
            self.showNextFrame(-1)
            showFrame = True
            
        if key == Qt.Key_Q:
            self.showNextFrame(-5)
            showFrame = True
            
        if key == Qt.Key_I:
            print "position length:", self.vh.getCurrentPositionLength()
            print "video length:", self.vh.getCurrentVideoLength()
        
        if showFrame:            
            frameNo = self.vh.getCurrentFrameNo()
            self.ui.lv_frames.setCurrentIndex(self.frameList.index(frameNo,0))
        
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
        
    def updateOriginalLabel(self, lbl, img):
        qi = array2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lbl.setScaledContents(False)
        lbl.setPixmap(px)
        
        lbl.update()
        
    
    def showNextFrame(self, increment=1):
        if increment > 0:
            frames = self.vh.getNextFrame(increment)
        elif increment < 0:
            frames = self.vh.getPrevFrame(-increment)
        else:
            frames = self.vh.getCurrentFrame()            
        
        self.updateLabel(self.ui.lbl_v0, frames[0][0], frames[1][0])
        self.updateLabel(self.ui.lbl_v1, frames[0][1], frames[1][1])
        self.updateLabel(self.ui.lbl_v2, frames[0][2], frames[1][2])
        self.updateLabel(self.ui.lbl_v3, frames[0][3], frames[1][3])
        
        self.updateOriginalLabel(self.ui.lbl_v0_full, frames[1][0])
        self.updateOriginalLabel(self.ui.lbl_v1_full, frames[1][1])
        self.updateOriginalLabel(self.ui.lbl_v2_full, frames[1][2])
        self.updateOriginalLabel(self.ui.lbl_v3_full, frames[1][3])
        
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
        
        self.ui.label.setScaledContents(True)
        self.ui.label.setPixmap(px)
        
    def startVideo(self):
        self.play = True
        self.setBackground("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        fps = 25.0
        updateRate = 33.0 * 12
        
        print "start Video"
        
        i = 0
        while self.play:
            self.showNextFrame()
            if (i % 10) == 0:
                frameNo = self.vh.getCurrentFrameNo()
                self.ui.lv_frames.setCurrentIndex(self.frameList.index(frameNo,0))
                QApplication.processEvents()
                    
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
        if not self.play:
            i = self.frameIdx
            img = self.jumpToFrame(self.vEs[0], self.ui.lbl_v0, self.pos[i][0],i)
            img = self.jumpToFrame(self.vEs[1], self.ui.lbl_v1, self.pos[i][1],i)
            img = self.jumpToFrame(self.vEs[2], self.ui.lbl_v2, self.pos[i][2],i)
            img = self.jumpToFrame(self.vEs[3], self.ui.lbl_v3, self.pos[i][3],i)
            self.ui.lv_frames.setCurrentIndex(self.frameList.index(i,0))
            

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
        print "start computing the distances..."
        self.dists = computeDistancesFromPosList(self.posList, self.fileList)
        print "finished computing distances"
        
        print "start computing the jumps..."
        self.filterList = filterJumps(self.posList, self.dists, 25)
        print "finished computing jumps"
        
    def loadNewVideo(self):
        self.videoList[self.fileList[0]] = VideoLoader(self.fileList[0])
        #self.prefetchVideo(self.fileList[0])
    
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
    finished = pyqtSignal()
    
    videoLength = -1
    frameList = []
    
    def __init__(self, posPath):
        BaseThread.__init__(self)
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
        
        results = []
        for i in range(4):
            f = self.posPath.split('.pos')[0] + '.v{0}.{1}'.format(i, 'avi')
            results += [lbview.apply_async(loadVideo, f, i)]
        
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
                
            time.sleep(0.001)
        
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
        
        self.pos = np.load(self.posPath)
        
        print "finished computing, emiting signal"
        
        self.videoLength = len(self.frameList[0])
        self.loading = False
        self.finished.emit()   
        
    def getVideoLength(self):
        if not self.loading:
            return self.videoLength
        else:
            raise RuntimeError("calling length, before video finished")
        
    def getPositionLength(self):
        if not self.loading:
            return len(self.pos)
        else:
            raise RuntimeError("calling length, before video finished")
            
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

class VideoHandler(QObject):    
    videoDict = dict()
    posList = []
    idx = 0
    pathIdx = 0
    dictLength = 7         # should be odd, otherwise fix checkBuffers()!
    
    
    changedFile = pyqtSignal(str)
    
    def __init__(self, posList):
        super(VideoHandler, self).__init__()
        self.posList = sorted(posList)
        self.posPath = posList[0]
        self.checkBuffer()
    
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
        
    def getCurrentFrame(self):      
        try:
            frame = self.videoDict[self.posPath].getFrame(self.idx)
        except KeyError:
            print "accessing video out of scope, fetching..."
            self.fetchVideo(self.posPath)
            #self.getFrame(self.posPath, idx)
            self.getCurrentFrame()
        except RuntimeError:
            print "something went wrong during the fetching procedure"
        
        self.checkBuffer()
        return frame
                
    def getNextFrame(self, increment=1):
        self.idx += increment
        if self.idx >= self.videoDict[self.posPath].getVideoLength():
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != self.dictLength:
                        self.idx -= self.videoDict[self.posPath].getVideoLength()                                         
                        self.posPath = pos[i+1]                  
                        self.changedFile.emit(self.posPath)  
                        break
                    else:
                        self.idx = self.videoDict[self.posPath].getVideoLength()
                        print "This is the very first frame, cannot go back further"
                        
        return self.getCurrentFrame()
        
    def getPrevFrame(self, decrement=1):
        self.idx -= decrement
        if self.idx < 0:
            pos = sorted(self.videoDict.keys())
            for i in range(len(pos)):
                if pos[i] == self.posPath:
                    if i != 0:
                        self.idx += self.videoDict[self.posPath].getVideoLength() 
                        self.posPath = pos[i-1]                        
                        self.changedFile.emit(self.posPath)
                        break
                    else:
                        self.idx = 0
                        print "This is the very first frame, cannot go back further"
                        
        return self.getCurrentFrame()
                
    def checkBuffer(self):
        #~ pos = sorted(self.videoDict.keys())
        #~ # half size of buffer length
        #~ hS = (self.dictLength + 1 / 2.0)
        #~ for i in range(len(pos)):
            #~ if pos[i] == self.posPath:
                #~ diff = i - hS
                #~ if diff == 0:
                    #~ # self.posPath is still in the middle
                    #~ return
                #~ elif diff < 0:
                    #~ # we need to prefetch earlier video
                    #~ currIdx = self.posList.index(self.posPath)
                    #~ fetchPos = currIdx - hS
                    #~ if fetchPos >= 0:
                        #~ self.fetchVideo(self.posList[fetchPos])
                        #~ # delete last video from buffer
                        #~ del self.videoDict[sorted(self.videoDict.keys())[-1]]
                #~ else:
                    #~ # we need to prefetch later video
                    #~ currIdx = self.posList.index(self.posPath)
                    #~ fetchPos = currIdx + hS
                    #~ if fetchPos < len(self.posList):
                        #~ self.fetchVideo(self.posList[fetchPos])
                        #~ # delete first video from buffer
                        #~ del self.videoDict[sorted(self.videoDict.keys())[0]]
                        #~ 
                #~ return
        #~ # if we reach here, we completely reinitalized
        
        hS = ((self.dictLength + 1) / 2.0)
        currIdx = self.posList.index(self.posPath)
        
        s = int(currIdx - hS)
        e = int(currIdx + hS +1)
        if s < 0:
            s = 0
        if e > len(self.posList):
            e = len(self.posList)            
        fetchRng = slice(s, e) 
        
        s -= 1
        e += 1
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
                del self.videoDict[vidPath]
                
        
        # prefetch all videos that are not prefetched yet
        for vidPath in self.posList[fetchRng]:
            try:
                self.videoDict[vidPath]
            except KeyError:
                self.fetchVideo(vidPath)
        
        
    def fetchVideo(self, path):
        print "fetching", path
        self.videoDict[path] = VideoLoader(path)
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    path = '/run/media/peter/Elements/peter/data/tmp-20130506'
    w = videoPlayer(path, videoFormat='avi')
    
    sys.exit(app.exec_())
