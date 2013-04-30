from pyTools.system.videoExplorer import videoExplorer
from pyTools.videoProc.backgroundImage import *
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
import warnings
import re
import os
import dateutil.parser
from skimage.color import *

class backgroundModel(object):
    colorModeLst = [['gray', rgb2gray ], 
                       ['rgb',  lambda x: x], 
                       ['hsv',  rgb2hsv], 
                       ['lab',  rgb2lab], 
                       ['xyz',  rgb2xyz]]
    
    
    def __init__(self,  verbose=False, colorMode='gray'):
        """
            INPUT:
            verbose     bool        switch verbosity
            colorMode   String      get available colourModes with 
                                    getcolorModes()
        """
        self.startDate = 0
        self.endDate = 0
        self.rootPath = 0
        self.nightPaths = 0
        self.dayPaths = 0
        self.verbose = verbose
        self.modelDay = []
        self.modelNight = []
        
        self.bgModelList = [None]*2      # [bgImg, startTime, endTime]
                
        self.colorIdx = self.getcolorModes().index(colorMode)
        
    def setData(self, startDate,  endDate):
        self.startDate = startDate
        self.endDate = endDate
        
    def setPath(self,  rootPath):
        self.rootPath = rootPath
        
    def getVideoPaths(self, rootPath, start, end,  sampleSize=200):        
        self.rootPath = rootPath
        self.startDate = start
        self.endDate = end
        
        self.vE = videoExplorer(verbose=self.verbose, rootPath=rootPath)
        self.vE.setTimeRange(self.startDate,  self.endDate)
        
        self.vE.parseFiles()
        
        self.dayPaths = self.vE.getPathsOfList(self.vE.dayList)
        self.nightPaths = self.vE.getPathsOfList(self.vE.nightList)
        
    def createModelFromListMean(self, pathList, sampleSize=200):
        mean = np.float32(self.vE.getRandomFrame(pathList))
        for i in range(2, sampleSize + 1):     
            if self.verbose:
                print "sample no. {0}".format(i - 1)
            frame = self.vE.getRandomFrame(pathList)            
            mean += (frame - mean) / i            
        return mean
        
        
    def createModelFromListMedian(self, pathList,  sampleSize=20):
        if sampleSize > 255:
            warnings.warn("createModelFromListMedian: sampleSize has to be between 0..255", RuntimeWarning)
            sampleSize = 255
        
        refFrame = self.getRandomFrame(pathList)
        
        
        if sampleSize > len(pathList):
            stepSize = 1
            sampleSize = len(pathList)
        else:
            stepSize = len(pathList) / sampleSize
            
        ## framebuffer a list with one element per dimension of reference image
        if len(refFrame.shape) > 2:
            frameBuffer = [None] * refFrame.shape[2]
            
            for i in range(len(frameBuffer)):
                frameBuffer[i] = np.empty([ refFrame.shape[0],  
                                            refFrame.shape[1],  sampleSize],
                                            dtype=np.uint8)
                frameBuffer[i][:, :, 0] = refFrame[:, :, i]
            
            for s in range(1, sampleSize):
                frame = self.getFrame(pathList[stepSize * s], 0)
                for i in range(len(frameBuffer)):
                    frameBuffer[i][:, :, s] = frame[:, :, i]
            
            medianImage = np.zeros(refFrame.shape,  np.uint8)
            
            for i in range(len(frameBuffer)):
                medianImage[:, :, i] = np.median(frameBuffer[i], axis=2)
            
        else:
            frameBuffer = np.empty([ refFrame.shape[0],  
                                            refFrame.shape[1],  sampleSize],
                                            dtype=np.uint8)
            frameBuffer[:, :, 0] = refFrame
        
            for s in range(1, sampleSize):
                frame = self.getFrame(pathList[stepSize * s], 0)
                frameBuffer[:, :, s] = frame
            
            medianImage = np.median(frameBuffer, axis=2)
                
        return medianImage
        
    def getRandomFrame(self, pathList,  info=False):
        if self.colorModeLst[self.colorIdx][0] == 'gray':
            fM = 'L'
        else:
            fM = 'RGB'
        
        return self.vE.getRandomFrame(pathList, frameMode=fM, info=info)
        
    def getFrame(self, path,  info=False):
        if self.colorModeLst[self.colorIdx][0] == 'gray':
            fM = 'L'
        else:
            fM = 'RGB'
        
        return self.vE.getFrame(path, frameMode=fM, info=info)
                        
    def createNightModel(self, sampleSize=20):
        if self.verbose:
            print "creating night model.."
        self.modelNight = backgroundImage(
                                self.createModelFromListMedian(self.nightPaths, 
                                                         sampleSize))
        times = [a.time() for a in self.vE.getDatesOfList(self.vE.nightList)]
        # get beginning and end of time range (inverted to dayModel, because
        # the night range starts in the evening and ends in the morning
        startTime = max([i for i in times if i < dt.time(12)])
        endTime = min([i for i in times if i > dt.time(12)])
        
        self.bgModelList[1] = [self.modelNight, startTime, endTime]
        
    def createDayModel(self, sampleSize=20):
        if self.verbose:
            print "creating day model.."
        self.modelDay = backgroundImage(
                                self.createModelFromListMedian(self.dayPaths,  
                                                       sampleSize))
        times = [a.time() for a in self.vE.getDatesOfList(self.vE.dayList)]
        startTime = min(times)
        endTime = max(times)
        self.bgModelList[0] = [self.modelDay, startTime, endTime]
        
    def getBgImg(self, time, debug=False):
        if debug:
            print time
        if time >= self.bgModelList[0][1] and time <= self.bgModelList[0][2]:
            if debug:
                print "choose day model"
            return self.bgModelList[0][0]
        elif time <= self.bgModelList[1][1] or time >= self.bgModelList[1][2]:
            if debug:
                print "choose night model"
            return self.bgModelList[1][0]
        else:
            raise ValueError("given time not covered by computed background Models")
    
    def saveModels(self, path=''):
        if path == '':
            path = self.rootPath
        
        if self.modelDay != []:
            plt.imsave(fname=root + "backgroundModel_day_" + 
                       start.isoformat() + "--" + end.isoformat(), 
                       arr=self.modelDay, cmap=mpl.cm.gray)
        
        if self.modelNight != []:
            plt.imsave(fname=root + "backgroundModel_night_" + 
                       start.isoformat() + "--" + end.isoformat(), 
                       arr=self.modelNight, cmap=mpl.cm.gray)
                       
    def loadModel(self, path):
        img = plt.imread(path)
        
        names = re.split("[_]",  os.path.basename(path))
        
        if len(names) < 3:
            warnings.warn("model filename does not contain model information." + 
                          " Setting image both modelDay and modelNight", 
                          RuntimeWarning)
            self.modelDay = img
            self.modelNight = img
            return
                
        data = re.split("--",  re.split("[.]", names[2])[0])
        
        self.startDate = dateutil.parser.parse(data[0])
        self.endDate = dateutil.parser.parse(data[1])
        
        if names[0] == "backgroundModel" and names[1] == "day":
            self.modelDay = img[:, :, 1]
            
        if names[0] == "backgroundModel" and names[1] == "night":
            self.modelNight = img[:, :, 1]
        
    def getcolorModes(self):
        """
            returns available colour spaces
        """
        return [row[0] for row in self.colorModeLst]

if __name__ == "__main__":
    bgModel = backgroundModel(verbose=True)
    
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 21)
    root = "/run/media/peter/Elements/peter/data/"
    
    bgModel.getVideoPaths(root,  start,  end)
    
    bgModel.createDayModel(sampleSize=20)    
    bgModel.createNightModel(sampleSize=20)
    
    plt.imshow(bgModel.modelDay)
    plt.show()
    
    plt.imshow(bgModel.modelNight)
    plt.show()
    
    bgModel.saveModels()    
