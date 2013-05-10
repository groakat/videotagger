import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import * 
from videoPlayer_auto import Ui_Form

from pyTools.system.videoExplorer import *

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
        
        self.posList = sorted(self.providePosList(path))        
        
        self.lm = MyListModel(self.posList, self)        
        self.ui.lv_paths.setModel(self.lm)
        
        self.ui.sldr_paths.setMaximum(len(self.posList))
        
        self.videoFormat = videoFormat
        self.idx = 0       
        self.play = False
        
        self.vEs = []
        for i in range(4):
            self.vEs.append(videoExplorer())
        
        self.setVideo(self.posList, 0)
        
        
        self.configureUI()
        
    def connectSignals(self):
        self.ui.pb_startVideo.clicked.connect(self.startVideo)
        self.ui.pb_stopVideo.clicked.connect(self.stopVideo)
        self.ui.sldr_paths.valueChanged .connect(self.selectVideo)
        #self.ui.lv_paths.clicked.connect(self.selectVideo)
        
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
        
    def updateVial(self, vE, lbl, p):       
        
        #img = vE.next()[:,:,0:3]
        frame = vE.vs.next()
        
        
        #print frame.frameno
        
        img = frame.ndarray()
        
        qi = array2qimage(img)
        pixmap = QPixmap()
        px = QPixmap.fromImage(qi)
        
        lblOrigin = self.ui.label.pos()
        
        #print(lblOrigin)            
        
        newX = lblOrigin.x() + p[1] * self.xFactor + self.xOffset
        newY = lblOrigin.y() + (p[0] * self.yFactor) + self.yOffset
                    
        #print(newX, newY)
        
        lbl.move(newX,newY)
        
        lbl.setScaledContents(True)
        lbl.setPixmap(px)
        
        lbl.update()
        
        return img
        
    def stopVideo(self):
        self.play = False
        
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
            self.setVideo(self.posList, k)
            
            for i in range(1, len(self.pos)):
                if self.ui.lv_paths.selectionModel().currentIndex().row() \
                 != k or not self.play:
                    print ("skip to ", self.ui.lv_paths.selectionModel().currentIndex().row())
                    wasSkipped = True
                    break
                idx = i
                img = self.updateVial(self.vEs[0], self.ui.lbl_v0, self.pos[idx][0])
                img = self.updateVial(self.vEs[1], self.ui.lbl_v1, self.pos[idx][1])
                img = self.updateVial(self.vEs[2], self.ui.lbl_v2, self.pos[idx][2])
                img = self.updateVial(self.vEs[3], self.ui.lbl_v3, self.pos[idx][3])
                
                            
                if (i % 30) == 0:
                    QApplication.processEvents()
                
                time.sleep(0.0001)# / updateRate)
            print time.time()-t
            
            if not wasSkipped:
                self.ui.lv_paths.setCurrentIndex(self.lm.index(k+1,0))
        
    def providePosList(self, path):
        posList = []
        bgList = []
        for root,  dirs,  files in os.walk(path):
            for f in files:
                if f.endswith('pos'):
                    posList.append(root + '/' + f)
                    
                if f.endswith('png'):
                    bgList.append(root + '/' + f)
                    #dt = vE.fileName2DateTime(f, 'npy')
                    
                    ##fl = open(root + '/' + f, 'r')
                    #pos = np.load(root + '/' + f)
                                
                    #hour = dt.hour
                    #if hour < 10 or hour >= 23:
                        #nightPosList.append(pos)
                    #else:
                        #dayPosList.append(pos)
        
        self.bgList = bgList
        return posList
        
    def generatePatchVideoPath(self, posPath, vialNo):
        """
        strips pos path off its postfix and appends it with the vial + video
        format postfix
        """
        return posPath.split('.pos')[0] + '.v{0}.{1}'.format(vialNo, 
                                                            self.videoFormat)
                                                            
    def setVideo(self, posList, idx):
        self.ui.lv_paths.setCurrentIndex(self.lm.index(idx,0))
        self.ui.sldr_paths.setSliderPosition(idx)
        for i in range(len(self.vEs)):
            f = self.generatePatchVideoPath(posList[idx], i)
            self.vEs[i].setVideoStream(f, info=False, frameMode='RGB')
            
        fl = open(self.posList[idx])
        self.pos = eval(fl.read())
        fl.close()
        
    def selectVideo(self, idx):
        self.idx = idx
        self.setVideo(self.posList, self.idx)
        
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    path = '/run/media/peter/Elements/peter/data/tmp-20130506'
    w = videoPlayer(path, videoFormat='avi')
    
    sys.exit(app.exec_())
