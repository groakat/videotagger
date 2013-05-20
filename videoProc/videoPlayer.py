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
        
        #self.posList = sorted(self.providePosList(path))
        #a = self.providePosList(path)
        #1/0
        self.posList = self.providePosList(path)    
        
        self.lm = MyListModel(self.fileList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.posList))
        
        self.videoFormat = videoFormat
        self.idx = 0       
        self.play = False
        self.frameIdx = -1
        
        self.filterList = []
        
        self.vEs = []
        for i in range(4):
            self.vEs.append(videoExplorer())
        
        self.setVideo(0)
        
        
        
        self.updateFrameList(range(100))
        
        self.configureUI() 
        
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.pb_compDist.clicked.connect(self.compDistances)
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
        
    def startVideo(self):
        self.play = True
        a = plt.imread("/run/media/peter/Elements/peter/data/tmp-20130426/2013-02-19.00-43-00-bg-True-False-True-True.png")
        
        qi = array2qimage(a*255)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        self.ui.label.setScaledContents(True)
        self.ui.label.setPixmap(px)
        
        fps = 25.0
        updateRate = 33.0 * 12
        
        print "start Video"
        
        #for k in range(len(self.posList)):
        
        while self.play:
            wasSkipped = False
            k = self.ui.lv_paths.selectionModel().currentIndex().row() 
            print ("show", k)
            t = time.time()
            print("showing", self.posList[k])
            self.setVideo(k)
            
            if self.frameIdx == -1:
                i = 1          
            else:
                i = self.frameIdx
                self.frameIdx = -1
                
            self.updateFrameList(range(len(self.pos)))
            
            while i < len(self.pos):
                if self.ui.lv_paths.selectionModel().currentIndex().row() \
                != k or not self.play:
                    print ("skip to ", self.ui.lv_paths.selectionModel().currentIndex().row())
                    wasSkipped = True
                    break
                if self.frameIdx != -1:
                    i = self.frameIdx
                    self.frameIdx = -1       
                    img = self.jumpToFrame(self.vEs[0], self.ui.lbl_v0, self.pos[i][0],i)
                    img = self.jumpToFrame(self.vEs[1], self.ui.lbl_v1, self.pos[i][1],i)
                    img = self.jumpToFrame(self.vEs[2], self.ui.lbl_v2, self.pos[i][2],i)
                    img = self.jumpToFrame(self.vEs[3], self.ui.lbl_v3, self.pos[i][3],i)
                else:
                    idx = i
                    img = self.updateVial(self.vEs[0], self.ui.lbl_v0, self.pos[idx][0])
                    img = self.updateVial(self.vEs[1], self.ui.lbl_v1, self.pos[idx][1])
                    img = self.updateVial(self.vEs[2], self.ui.lbl_v2, self.pos[idx][2])
                    img = self.updateVial(self.vEs[3], self.ui.lbl_v3, self.pos[idx][3])
                
                
                
                if (i % 30) == 0:
                    #self.ui.lv_frames.setCurrentIndex(self.frameList.index(i,0))
                    QApplication.processEvents()
                
                i += 1
                
                    
                
                time.sleep(0.0001)# / updateRate)
            print time.time()-t
            
            if not wasSkipped:
                self.ui.lv_paths.setCurrentIndex(self.lm.index(k+1,0))
        
    def providePosList(self, path):
        fileList  = []
        posList = []
        for root,  dirs,  files in os.walk(path):
#            for f in files:
#                if f.endswith('pos'):
#                    posList.append(root + '/' + f)
#                    
#                if f.endswith('png'):
#                    bgList.append(root + '/' + f)
            files = files
            for f in files:
                if f.endswith('npy'):
                    path = root + '/' + f
                    fileList.append(path)
                    posList.append(np.load(path))  
                            
        #sort both lists based on the file name
        posList = [x for y, x in sorted(zip(fileList, posList))]
        self.fileList = sorted(fileList)
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
        self.setVideo(self.idx)
        
    def selectVideoLV(self, mdl):
        self.idx = mdl.row()   
        self.setVideo(self.idx)
        
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
        
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    path = '/run/media/peter/Elements/peter/data/tmp-20130506'
    w = videoPlayer(path, videoFormat='avi')
    
    sys.exit(app.exec_())
