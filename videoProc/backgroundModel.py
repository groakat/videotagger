from pyTools.system.videoExplorer import videoExplorer
from ffvideo import VideoStream
import datetime as dt
import random
import numpy as np
from matplotlib import pyplot as plt

class backgroundModel(object):
    def __init__(self,  verbose=False):
        self.startDate = 0
        self.endDate = 0
        self.path = 0
        self.nightPaths = 0
        self.dayPaths = 0
        self.verbose = verbose
        
    def setData(self, startDate,  endDate):
        self.startDate = startDate
        self.endDate = endDate
        
    def setPath(self,  path):
        self.path = path
        
    def getVideoPaths(self, path, start, end):        
        self.path = path
        self.startDate = start
        self.endDate = end
        
        self.vE = videoExplorer()
        self.vE.setTimeRange(self.startDate,  self.endDate)
        
        self.vE.parseFiles()
        
        self.dayPaths = self.vE.getPathsOfList(self.vE.dayList)
        self.nightPaths = self.vE.getPathsOfList(self.vE.nightList)
        
    def createModelFromList(self, pathList, sampleSize=200):
        mean = np.float32(self.getRandomFrame(pathList))
        for i in range(2, sampleSize + 1):     
            if self.verbose:
                print "sample no. {0}".format(i - 1)
            frame = self.getRandomFrame(pathList)            
            mean += (frame - mean) / i            
        return mean
        
    def getRandomFrame(self, pathList):
        file = pathList[random.randint(0,  len(pathList))]            
        frameNo = random.randint(0,  1600)
        
        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)
        
        vs = VideoStream(file, frame_mode='L')            
#        return vs.get_frame_no(frameNo).ndarray()       
        return vs.next().ndarray()
        
        
    def createNightModel(self):
        self.modelNight = self.createModelFromList(self.nightPaths)
        
    def createDayModel(self):
        self.modelDay = self.createModelFromList(self.dayPaths)

if __name__ == "__main__":
    bgModel = backgroundModel(verbose=True)
    
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 20)
    
    bgModel.getVideoPaths("/run/media/peter/Elements/peter/data/",  start,  end)
    
    bgModel.createDayModel()
    
#    bgModel.createNightModel()
    
    plt.imshow(bgModel.modelDay)
    plt.show()
    
#    plt.imshow(bgModel.modelNight)
    plt.show()
    
    
    
    
