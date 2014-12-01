from PySide import QtGui
from PySide import QtCore


import pyTools.system.videoExplorer as VE
import pyTools.videoProc.annotation as Annotation
import pyTools.misc.basic as bsc 
import pyTools.misc.config as cfg
import pyTools.misc.Cache as Cache
import pyTools.videoTagger.dataLoader as DL
import numpy as np
import time
import os




import json




class VideoHandler(QtCore.QObject):       
    newVideoLoader = QtCore.Signal(list)
    deleteVideoLoader = QtCore.Signal(list)

    newFullResVideoLoader = QtCore.Signal(list)
    
    newAnnotationLoader = QtCore.Signal(list)
    deleteAnnotationLoader = QtCore.Signal(list)
    
    changedFile = QtCore.Signal(str)
    
    @cfg.logClassFunction
    def __init__(self, posList, fileChangeCb, selectedVials=[0], startIdx=0,
                 videoExtension='.avi', bufferWidth=300, bufferLength=4,
                 patchesFolder='', positionsFolder='', behaviourFolder=''):
        super(VideoHandler, self).__init__()        
        
        self.videoDict = dict()
        self.annoDict = dict()
        self.posList = []
        self.annoViewList = []
        self.posPath = ''
        self.idx = 0
        self.pathIdx = 0
        self.videoEnding = videoExtension
        self.patchesFolder = patchesFolder
        self.positionsFolder = positionsFolder
        self.bhvrFolder = behaviourFolder
        
        ### old stuff ?
        self.dictLength = 3         # should be odd, otherwise fix checkBuffers()!
        self.delBuffer = 5
        ### old stuff ?

        self.bufferWidth  = bufferWidth     # width of each buffer
        self.bufferLength = bufferLength    # number of buffers on EITHER SIDE
        self.bufferJut = 2          # number of buffers outside of the core 
                                    # buffer area on EITHER SIDE that are not
                                    # deleted immediately
        self.videoLengths = dict()  # lengths of each video chunk
        
        
        self.posList = sorted(posList)
        self.posPath = posList[startIdx]
        
        
        self.annoAltStart = None
        
        ## video loading
        self.vLL = DL.VideoLoaderLuncher(eofCallback=self.endOfFileNotice,
                                         bufferLength=bufferLength * 2 +
                                                      self.bufferJut * 2 + 3)

        self.videoLoaderLuncherThread = DL.MyThread("videoLuncher")
        self.vLL.moveToThread(self.videoLoaderLuncherThread)
        
        self.videoLoaderLuncherThread.start()
        self.videoLoaderLuncherThread.wrapUp.connect(self.vLL.aboutToQuit)

        self.vLL.createdVideoLoader.connect(self.linkToAnnoview)
        self.newVideoLoader.connect(self.vLL.lunchVideoLoader)
        self.deleteVideoLoader.connect(self.vLL.deleteVideoLoader)


        ## full resolution video loading
        # self.fVLL = DL.VideoLoaderLuncher(eofCallback=self.endOfFileNotice)
        # self.fullResVideoLoaderLuncherThread = DL.MyThread("fullResVideoLuncher")
        # self.fVLL.moveToThread(self.fullResVideoLoaderLuncherThread)
        #
        # self.fullResVideoLoaderLuncherThread.start()
        # self.fullResVideoLoaderLuncherThread.wrapUp.connect(self.fVLL.aboutToQuit)
        # self.newFullResVideoLoader.connect(self.fVLL.lunchVideoLoader)

        
        ## annotation loading
        self.aLL = DL.AnnotationLoaderLuncher(self.endOfFileNotice, videoExtension,
                                              self.patchesFolder, self.bhvrFolder,
                                              bufferLength=bufferLength * 2 +
                                                           self.bufferJut * 2
                                                           + 3)

        self.annotationLoaderLuncherThread = DL.MyThread("annotationLuncher")
        self.aLL.moveToThread(self.annotationLoaderLuncherThread)
        
        self.annotationLoaderLuncherThread.start()
        self.annotationLoaderLuncherThread.wrapUp.connect(self.aLL.aboutToQuit)

        self.aLL.createdAnnotationLoader.connect(self.updateNewAnnotation)
        self.newAnnotationLoader.connect(self.aLL.lunchAnnotationLoader)
        self.deleteAnnotationLoader.connect(self.aLL.deleteAnnotationLoader)
        
        self.posCache = Cache.PosFileCache(size=300)
        
        
        
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

        if len(self.patchesFolder) > 0:
            dirname = os.path.dirname(posList[0])[:-len(self.patchesFolder)]
        else:
            dirname = os.path.dirname(posList[0])
        
        tmpFilename = os.path.join(dirname, "videoTagger.bhvr~")
        
        self.tmpFile = tmpFilename
        

        # always do that at the end
#         self.checkBuffer()
        
        self.vE = VE.videoExplorer()       
        

    def maxOfSelectedVials(self):
        if self.selectedVials is None:
            return 0
        else:
            return max(self.selectedVials)#4#0
#         return maxOfSelectedVials(self.selectedVials)
    
    def aboutToQuit(self):
        try:
            self.videoLoaderLuncherThread.quit()
        except RuntimeError:
            # thread already deleted
            pass
    
    @cfg.logClassFunction
    def setFrameIdx(self, idx):
        self.idx = idx
        
        
    @cfg.logClassFunction
    def getCurrentKey_idx(self):
        return self.posPath, self.idx
    
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
    
#     @cfg.logClassFunction
#     def getCurrentVideoLength(self):
#         return self.videoDict[self.posPath].getVideoLength()
        
    @cfg.logClassFunction
    def getCurrentPositionLength(self):
        return self.videoDict[self.posPath].getPositionLength()
        
    @cfg.logClassFunction
    def getCurrentFrameNo(self):
        return self.idx

    def generateFullResolutionVideoPath(self):
        # split _small.avi / _small.mp4
        corePath = self.posPath[:-10]
        # append _full.avi / _full.mp4
        fullResPath = corePath + '_full.{suf}'.format(suf=self.posPath[-3:])
        return fullResPath

    def getFullResolutionFrame(self):
        fullResPath = self.generateFullResolutionVideoPath()

        pos = self.getPosition(self.posPath, self.idx)

        img = self.vE.getFrame(fullResPath, frameNo=self.idx, frameMode='RGB')
        frame =  [[img]  * (self.maxOfSelectedVials() + 1)]

        annotation = self.getCurrentAnnotation()

        return [pos, frame, annotation]

    def alignFullResVideo(self):
        pass

    def serveFullResVideo(self):
        pass

    def alignAndServeFullResVideo(self):
        self.alignFullResVideo()
        self.serveFullResVideo()


    def getFullResolutionFrames(self, left=10, right=50):
        path = self.posPath
        idx  = 0
        if self.idx - left < 0:
            start = 0
        else:
            start = self.idx - left

        if self.idx + right > self.getVideoLength(self.posPath):
            stop = self.getVideoLength(self.posPath)
        else:
            stop = self.idx + right

        idxSlice = slice(start, stop)

        lst = list()
        lst[0] = path
        lst[1] = self
        lst[2] = self.selectedVials
        lst[3] = idx
        lst[4] = idxSlice

        self.newFullResVideoLoader.emit(lst)

        #############################################

        self.fullResVideoLoaderThread = DL.MyThread("fullResVideoLuncher")

        self.fullResVL = DL.VideoLoader(path, idxSlice=idxSlice,
                         thread=self.fullResVideoLoaderThread,
                         selectedVials=self.selectedVials)



        self.fullResVL.moveToThread(self.fullResVideoLoaderThread)
        self.fullResVideoLoaderThread.start()

        self.fullResVL.startLoading.connect(self.fullResVL.loadVideos)
        self.fullResVL.eof.connect(self.eofCallback)
        self.fullResVL.finished.connect(self.alignAndServeFullResVideo)

        cfg.log.debug("finished thread coonecting signal create new VideoLoader {0}".format(path))
        self.fullResVL.startLoading.emit()
        # cfg.log.debug("finished thread emit create new VideoLoader {0}".format(path))
        # self.threads[self.fullResVL] = [self.fullResVideoLoaderThread, self.fullResVL.startLoading]




    
    @cfg.logClassFunction
    def getFrame(self, posPath, idx, checkBuffer=False):        
        self.idx = idx
        self.posPath = posPath
        self.checkBuffer(checkBuffer)
        return self.getCurrentFrame()
        
        
    @cfg.logClassFunction
    def getTempFrame(self, increment, posOnly=False):      
        idx = self.idx
        path = self.posPath
        
        try:
            if increment > 0:
                frame = self.getNextFrame(increment, doBufferCheck=False, 
                                          emitFileChange=False, posOnly=posOnly)
            else:
                frame = self.getPrevFrame(-increment, doBufferCheck=False, 
                                          emitFileChange=False, posOnly=posOnly)
        except KeyError:
            frame = self.getCurrentFrameNull()
        except RuntimeError:
            cfg.log.debug("something went wrong during the fetching procedure")
                
        self.idx = idx
        self.posPath = path
        
        return frame


    def getCurrentAnnotation(self):
        if self.posPath in self.annoDict.keys():
            if self.annoDict[self.posPath] is not None:
                annotation = self.annoDict[self.posPath].annotation.frameList[self.idx]
            else:
                annotation = [[{'confidence': 0}]
                                for i in range(self.maxOfSelectedVials() + 1)]
        else:
            annotation = [[{'confidence': 0}]
                                for i in range(self.maxOfSelectedVials() + 1)]

        return annotation

    @cfg.logClassFunction
    def getCurrentFrame(self, doBufferCheck=True, updateAnnotationViews=True,
                        posOnly=False):
        while self.videoDict[self.posPath] is None:
            cfg.log.info("waiting for videopath")   
            QtGui.QApplication.processEvents()
            time.sleep(0.05)
        
        frameList = []
        
        # get position
#         posKey = "".join(self.posPath.split(self.videoEnding)[:-1]) + '.pos.npy'
# #         posKey += 
#         
#         pos = self.posCache.getItem(posKey)[self.idx]
#         self.getPositionArray(self.posPath)[self.idx]
        pos = self.getPosition(self.posPath, self.idx)
        
        frameList += [pos]
        
        if posOnly:
            return frameList
            
        try:
            bufferIdx = self.idx / self.bufferWidth
            frame = self.videoDict[self.posPath][bufferIdx].getFrame(self.idx)
            
            if not frame:
                frame = self.getCurrentFrameUnbuffered(doBufferCheck, 
                                                       updateAnnotationViews)
                    
        except KeyError:
            cfg.log.warning("accessing video out of scope, fetching...")
#             self.fetchVideo(self.posPath)
            frame = self.getCurrentFrameUnbuffered(doBufferCheck, 
                                                   updateAnnotationViews)
                    
        except AttributeError:
            cfg.log.warning("accessing video out of scope, fetching...")
            frame = [np.zeros((64,64,3))] * (self.maxOfSelectedVials() + 1)
#             frame = self.getCurrentFrameUnbuffered(doBufferCheck,
#                                                    updateAnnotationViews)
#             print pos, posOnly
#             print frameList
            
        if doBufferCheck:
            self.checkBuffer(updateAnnotationViews)            
        
            if updateAnnotationViews:
                self.updateAnnoViewPositions()
            
            cfg.logGUI.debug(json.dumps({"key":self.posPath, 
                                     "idx":self.idx}))

        annotation = self.getCurrentAnnotation()

        frameList += [frame]
            
        frameList += [annotation]
        
        return [pos, frame, annotation]
    



    @cfg.logClassFunction#Info
    def getCurrentFrameUnbuffered(self, doBufferCheck=False, 
                                  updateAnnotationViews=False,
                                  posOnly=False):
        
#         frameList = []
#         
#         cfg.log.warning("{0}".format(self.idx))
#         # get position
#         posKey = "".join(self.posPath.split(self.videoEnding)[:-1]) + '.pos.npy'
# #         posKey += 
#         
#         pos = self.posCache.getItem(posKey)[self.idx]
#         
#         frameList += [pos]
#         
#         if posOnly:
#             return frameList
        
        
        img = self.vE.getFrame(self.posPath, frameNo=self.idx, frameMode='RGB')
        frame = [img]  * (self.maxOfSelectedVials() + 1)
        
        if doBufferCheck:
            self.checkBuffer(updateAnnotationViews)            
        
            if updateAnnotationViews:
                self.updateAnnoViewPositions()
            
        return frame
    
    @cfg.logClassFunction#Info
    def getCurrentFrameNull(self):
        frame = [[[0,0] 
                        for i in range(self.maxOfSelectedVials() + 1)], 
                 [[np.zeros((10,10))]  * \
                             (self.maxOfSelectedVials() + 1)],
                 [[]]
                 ]
        return frame
    
        
    @cfg.logClassFunction
    def getBufferFrame(self, posPath, idx):    
        frame = []  
        try:
            frame = self.videoDict[posPath].getFrame(idx)
            
        except KeyError:
            pass
            
        return frame
    
    def getPositionArray(self, bhvrPath):
        videoFolder = os.path.dirname(bhvrPath)
        videoName = os.path.basename(bhvrPath)
        posFolder = videoFolder[:-len(self.patchesFolder)] + \
                    self.positionsFolder
        posKey = posFolder + '/' + ".".join(videoName.split('.')[:-1]) + '.pos.npy'

        try:
            pos = self.posCache.getItem(posKey)
        except:
            pos = None
            
        return pos
        
        
    def getPosition(self, bhvrPath, idx):
        posA = self.getPositionArray(bhvrPath)
        if posA == None:
            pos = [np.ones((2,1)) * -1]
        else:
            pos = [posA[idx]]

        return pos
        
        
    @cfg.logClassFunction#Info
    def getVideoLength(self, posPath):
        vidLength = 0
        if self.videoLengths[self.posPath] != None:
            vidLength = self.videoLengths[self.posPath]
        else:
            res = self.getPositionArray(self.posPath)
            if res == None:
                # hack will probably break if video is longer than 300 frames
                vidLength = 300
            else:
                vidLength = res.shape[0]
            
        return vidLength
        
        
                
    @cfg.logClassFunction
    def getNextFrame(self, increment=1, doBufferCheck=True, emitFileChange=True,
                     unbuffered=False,  posOnly=False):

#         if self.videoLengths[self.posPath] is None:
#             return self.getCurrentFrameNull()
            
        cfg.log.debug("self.idx: {2}, increment: {0}, doBufferCheck: {1}".format(increment, doBufferCheck, self.idx))
        self.idx += increment

        if self.idx >= self.getVideoLength(self.posPath):
            keys = self.posList #sorted(self.videoDict.keys())
            pos = [i for i,k in enumerate(keys) if k==self.posPath][0]
            changedFile = False
            while self.idx >= self.getVideoLength(self.posPath): 
#                 if self.videoLengths[self.posPath] != None:
#                     vidLength = self.videoLengths[self.posPath]
#                 else:
#                     vidLength  = self.getPositionArray(self.posPath).shape[0]
                
                vidLength = self.getVideoLength(self.posPath)
                    
                if pos != len(keys) - 1:
                    self.idx -= vidLength                                         
                    self.posPath = keys[pos+1]
                    pos += 1 
                    changedFile = True
                else:
                    self.idx = vidLength -1
                    if doBufferCheck:
                        cfg.log.warning("This is the very last frame, cannot advance further")
                    break
                
                # TODO make better fix
                if self.posPath is None:
                    break
                        
            if changedFile and emitFileChange:
                self.fileChangeCB(self.posPath)  
                        
        if not unbuffered:
            return self.getCurrentFrame(doBufferCheck=doBufferCheck,
                                        posOnly=posOnly)
        else:
            return self.getCurrentFrameUnbuffered(doBufferCheck=doBufferCheck,
                                                  posOnly=posOnly)
        
    @cfg.logClassFunction
    def getPrevFrame(self, decrement=1, doBufferCheck=True, emitFileChange=True,
                     unbuffered=False, posOnly=False):
        
#         if self.videoLengths[self.posPath] is None:
#             return self.getCurrentFrameNull()
        
        self.idx -= decrement
        
        if self.idx < 0:
            keys = self.posList #sorted(self.videoDict.keys())
            pos = [i for i,k in enumerate(keys) if k==self.posPath][0]
            changedFile = False
            while self.idx < 0:
#                 if self.videoLengths[self.posPath] != None:
#                     vidLength = self.videoLengths[self.posPath]
#                 else:
#                     vidLength  = self.getPositionArray(self.posPath).shape[0]
                    
                if pos != 0:
                    self.posPath = keys[pos-1] 
                    vidLength = self.getVideoLength(self.posPath)
                    self.idx += vidLength
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
            return self.getCurrentFrame(doBufferCheck=doBufferCheck, 
                                        posOnly=posOnly)
        else:
            return self.getCurrentFrameUnbuffered(doBufferCheck=doBufferCheck, 
                                                  posOnly=posOnly)
    
                
    @cfg.logClassFunction
    def checkBuffer(self, updateAnnoViewPositions=True):       
               
        bufferedKeys = self.checkBuffersRight()
        bufferedKeys = self.checkBuffersLeft(bufferedKeys)

        cfg.log.debug("buffered keys: {0}".format(bufferedKeys))
        self.deleteOldBuffers(bufferedKeys,  updateAnnoViewPositions)
        

    @cfg.logClassFunction
    def deleteOldBuffers(self, bufferedKeys, updateAnnoViewPositions):
        # extend right buffer to account for jut
        curKey = sorted(bufferedKeys.keys())[-1]
        curIdx = sorted(bufferedKeys[curKey])[-1]
        for i in range(self.bufferJut):    
            curKey, curIdx = self.parseBuffersRight(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            bufferedKeys[curKey] += [curIdx]
                    
        # extend left buffer to account for jut
        curKey = sorted(bufferedKeys.keys())[0]
        curIdx = sorted(bufferedKeys[curKey])[0]
        for i in range(self.bufferJut):    
            curKey, curIdx = self.parseBuffersLeft(curKey, curIdx)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            bufferedKeys[curKey] += [curIdx]
            
        # advance and behind buffer key
        advKeyIdx = self.posList.index(sorted(bufferedKeys.keys())[-1]) + 1
        if advKeyIdx > len(self.posList):
            advKeyIdx = None
                    
        behKeyIdx = self.posList.index(sorted(bufferedKeys.keys())[0]) - 1
        if behKeyIdx < 0:
            behKeyIdx = None
            
        # check all buffers if lying within jut, unbuffer otherwise
        for key in self.videoDict.keys():
            if key in bufferedKeys.keys():
                for idx in self.videoDict[key].keys():
                    if idx not in bufferedKeys[key]:
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
                    
                try:
                    self.deleteAnnotationLoader.emit([self.annoDict[key]])
                    self.annoDict[key] = None
                    del self.annoDict[key]
                except:
                    pass
            
            
    @cfg.logClassFunction
    def unbuffer(self, key, idx, updateAnnoViewPositions):        
        cfg.log.info("delete video dict {0}[{1}]".format(key, idx))
        self.deleteVideoLoader.emit([self.videoDict[key][idx]])
        
        # first make sure to not refer anymore to VL
        self.videoDict[key][idx] = None
        # delete key/value pair
        del self.videoDict[key][idx]

        cfg.log.debug("delete finish")
        
        if key not in self.videoDict.keys():
            if updateAnnoViewPositions:
                for aV in self.annoViewList:
                    cfg.log.info("removing annotatation from annoViews {0}".format(key))
                    aV.removeAnnotation(key)
        
        
        
    @cfg.logClassFunction
    def checkBuffersRight(self):        
        # index of current frame in videoDict
        cfg.log.debug("entering curkey: {0}, curIdx: {1}".format(self.bufferWidth, self.idx))
        curIdx = self.idx / self.bufferWidth - 1
        curKey = self.posPath
        
        bufferedKeys = dict()
#         bufferedKeys[curKey] = []
        
        for i in range(-1, self.bufferLength):
            curKey, curIdx = self.parseBuffersRight(curKey, curIdx + 1)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            self.ensureBuffering(curKey, curIdx)
            bufferedKeys[curKey] += [curIdx]
        
        return bufferedKeys
            
    @cfg.logClassFunction
    def parseBuffersRight(self, curKey, curIdx):   
        cfg.log.debug("entering curkey: {0}, curIdx: {1}".format(curKey, curIdx))
        if  curKey in self.videoLengths.keys():
            cfg.log.debug("curKey in videoLengths curkey: {0}, curIdx: {1}".format(curKey, 
                                                                    curIdx))  
            if self.videoLengths[curKey] is not None \
            and (curIdx * self.bufferWidth) >= self.videoLengths[curKey]:
                curIdx = 0
                newKeyIdx = self.posList.index(curKey) + 1
                if newKeyIdx < len(self.posList):
                    curKey = self.posList[newKeyIdx]
                else:
                    curKey = None
                    curIdx = None
                    
        else:
            cfg.log.debug("curKey not in videoLengths curkey: {0}, curIdx: {1}".format(curKey, 
                                                                    curIdx))           
        
        cfg.log.debug("exiting curkey: {0}, curIdx: {1}".format(curKey, curIdx))            
        return curKey, curIdx
                
        
    @cfg.logClassFunction
    def checkBuffersLeft(self, bufferedKeys):
        curIdx = self.idx / self.bufferWidth
        curKey = self.posPath
        
#         bufferedKeys = dict()
#         bufferedKeys[curKey] = []
        
        for i in range(self.bufferLength):
            curKey, curIdx = self.parseBuffersLeft(curKey, curIdx - 1)
            
            if curKey is None:
                break
            
            if curKey not in bufferedKeys.keys():
                bufferedKeys[curKey] = [] 
                
            self.ensureBuffering(curKey, curIdx)
            bufferedKeys[curKey] += [curIdx]
                
        return bufferedKeys
                
    @cfg.logClassFunction
    def parseBuffersLeft(self, curKey, curIdx):
        
        if curIdx < 0:
            newKeyIdx = self.posList.index(curKey) - 1
            if newKeyIdx >= 0:
                curKey = self.posList[newKeyIdx]  
                if  curKey in self.videoLengths.keys():
                    if self.videoLengths[curKey] is not None:
                        curIdx = self.videoLengths[curKey] / self.bufferWidth
                    else:     
                        curIdx = None
                        curKey = None
                else:
                    self.bufferEnding(curKey)       
                    curIdx = None
                    curKey = None             
            else:
                curIdx = None
                curKey = None
        
        return curKey, curIdx
        
    @cfg.logClassFunction
    def ensureBuffering(self, curKey, curIdx):
        try:
            self.videoDict[curKey][curIdx]
        except KeyError:
            self.fetchVideo(curKey, curIdx)
        except IndexError:
            self.fetchVideo(curKey, curIdx)
        
        
    @cfg.logClassFunction
    def bufferEnding(self, key):
        if key in self.videoLengths.keys():            
            idx = self.videoLengths[key] / self.bufferWidth
            self.ensureBuffering(key, idx)
        else:
            self.videoLengths[key] = None
            self.fetchNewAnnotation(key)
            self.bufferEndingQueue += [key]
            
    def fetchNewAnnotation(self, key):
        if key not in self.videoLengths.keys():
            self.videoLengths[key] = None
            
        self.annoDict[key] = None
        
        path = key.split(self.videoEnding)[0] + '.bhvr'
        self.newAnnotationLoader.emit([key, path])
        
    @QtCore.Slot(list)
    def endOfFileNotice(self, lst):
        key = lst[0]
        length = lst[1]
        
        if key.endswith('.bhvr'):
            videokey = "".join(key.split('.bhvr')[:-1]) + self.videoEnding
        else:
            videokey = key
        
        
        self.updateVideoLength(videokey, length)
        
        nextKeyIdx = self.posList.index(videokey) + 1
        if nextKeyIdx < len(self.posList):
            nextKey = self.posList[self.posList.index(videokey) + 1]
        
            # if end of file notice was send, while moving towards the right-hand
            # side
            if videokey in self.videoDict.keys() \
            and len(self.videoDict[videokey]) > 1:
                self.ensureBuffering(nextKey, 0)
        
    @QtCore.Slot(list)
    def updateVideoLengthAndFetchLastBuffer(self, lst):
        key = lst[0]
        length = lst[1]
        
        self.updateVideoLength(key, length)
        self.bufferEnding(key)
        
    def updateVideoLength(self, key, length):
        self.videoLengths[key] = length
        
        
    @cfg.logClassFunction
    def fetchVideo(self, path, idx):
#         vL = VideoLoader(path)
#         vL.loadedAnnotation.connect(self.updateNewAnnotation)
        cfg.log.debug("input: {0} [{1}]".format(path, idx))
        bufferStart = idx * self.bufferWidth
        idxRange = slice(bufferStart, bufferStart + self.bufferWidth)
            
        cfg.log.debug("fetching {0} [{1}]".format(path, idxRange))
        
        if path not in self.videoDict.keys():
            self.videoDict[path] = dict()
            
        self.videoDict[path][idx] = None        
        
        self.newVideoLoader.emit([path, self, self.selectedVials, 
                                  idx, idxRange])        
        
        if path not in self.annoDict.keys():
#             self.newAnnotationLoader.emit([path])
            self.fetchNewAnnotation(path)
        
        
    @cfg.logClassFunction
    @QtCore.Slot(list)
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
    @QtCore.Slot(list)
    def updateNewAnnotation(self, annotationBundle):  
        """
        annotationBundle = [key, path, annotationLoader]
        """
        self.annotationBundle += [annotationBundle]
        self.loadingFinished = True
        
    @cfg.logClassFunction
    def loadAnnotationBundle(self): 
        self.annotationBundle = sorted(self.annotationBundle, key=lambda x: x[1])

        delList = []

        for i, annotationBundle in enumerate(self.annotationBundle):
            key = annotationBundle[0]
#             path = annotationBundle[1]
            aL = annotationBundle[2]
            annotation = aL.annotation

            if annotation is None:
                # annotation not yet loaded
                continue

            if annotation:
                for aV in self.annoViewList:
                    aV.addAnnotation(annotation, key,
                                     addAllAtOnce=(not self.loadProgressive))

            self.annoDict[key] = aL
            # save pathlength and bufferEnding if requested earlier

            self.videoLengths[key] = len(aL.annotation.frameList)
            # if annotation is not None:
            #     self.videoLengths[key] = len(annotation.frameList)
            # else:
            #     self.videoLengths[key] = \
            #                         self.videoDict[key].getPositionLength()

            if key in self.bufferEndingQueue:
                self.bufferEndingQueue.pop(self.bufferEndingQueue.index(key))
                self.bufferEnding(key)

            delList += [i]

        # delete processed items
        self.annotationBundle[:] = [ item \
                                        for i,item in \
                                            enumerate(self.annotationBundle) \
                                            if i not in delList]
        
            
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
        lenFunc = lambda x: len(x.annotation.frameList)#[0])                
        
        newRng = bsc.generateRangeValuesFromKeys(self.annoEnd, 
                                                 curAnnoEnd,
                                                 lenFunc=lenFunc)
        
        for key in newRng:
            for idx in newRng[key]:
                if not key in self.tempValue.keys():
                    self.tempValue[key] = dict()
                    
                self.tempValue[key][idx] =  metadata
                
        self.annoEnd = curAnnoEnd

    def getHighestBehaviourNumber(self, bhvrs):
        maxN = 0

        for bhvr in bhvrs:
            n = bhvr.split("_")[-1]
            try:
                n = int(n)
            except:
                continue

            if maxN < n:
                maxN = n

        return maxN

    @cfg.logClassFunction
    def disambiguateDoubleBehaviourNames(self, vials, annotator, behaviour,
                                         rng):

        filt = Annotation.AnnotationFilter(vials, [annotator], [behaviour])

        annos = []
        for key in rng:
            annos += [self.annoDict[key].annotation.filterFrameList(
                                                            filt,
                                                            rng[key],
                                                            exactMatch=False)]

        maxCounter = -1
        for anno in annos:
            for frame in anno.frameList:
                if frame is None:
                    continue

                for lbl in frame:
                    if lbl is None:
                        continue

                    nMaxBehaviour = self.getHighestBehaviourNumber(
                                            lbl['behaviour'].keys())
                    if maxCounter < nMaxBehaviour:
                        maxCounter = nMaxBehaviour

        if maxCounter > -1:
            return "{bvhr}_{no}".format(bvhr=behaviour, no=maxCounter + 1)

        return behaviour

    def addAnnotationToAnnoViews(self, vial, annotator, behaviour, key):
        v = vial
        # refresh annotation in anno view
        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if v == None and aV.vialNo == None \
                    or v in aV.vialNo:
                        cfg.log.debug("refreshing annotation")
                        aV.addAnnotation(\
                                    self.annoDict[key].annotation,
                                         key)

    def eraseAnnotationFromAnnoViews(self, vial, annotator, behaviour, key):
        v = vial
        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if v == None and aV.vialNo == None \
                    or v in aV.vialNo:
                        cfg.log.debug("refreshing annotation")
                        aV.addAnnotation(\
                                    self.annoDict[key].annotation,
                                         key)


    def addAnnotationRange(self, rngs, vials, annotator, behaviour):
        if type(vials) is not list:
            vials = [vials]

        for key in rngs:
            for v in vials:
                self.annoDict[key].annotation.addAnnotation(v, rngs[key],
                                        annotator, behaviour,
                                        self.tempValue[key])

            cfg.log.info("add annotation vials {v}| range {r}| annotator {a}| behaviour {b}| confidence {c}".format(
                        v=vials, r=rngs[key], a=annotator,
                          b=behaviour, c=self.tempValue[key]))

            cfg.log.info("check annodict {0}".format(self.annoDict[key].annotation.hasChanged))


            # refresh annotation in anno view
            self.addAnnotationToAnnoViews(v, annotator, behaviour, key)
            
            cfg.logGUI.info(json.dumps({"vials":vials,
                                   "key-range":rngs,
                                   "annotator":annotator,
                                   "behaviour":behaviour,
                                   "metadata":self.tempValue[key]}))


        self.saveTempAnnotationEdit(rngs, vials, annotator, behaviour, 'add')

    def saveTempAnnotationEdit(self, rng, vials, annotator, behaviour, mode):
        if os.path.exists(self.tmpFile):
            with open(self.tmpFile, "r") as f:
                annos = json.load(f)
        else:
            annos = []

        annos += [{"mode":mode,
                   "vials":vials,
                   "key-range":rng,
                   "annotator":annotator,
                   "behaviour":behaviour,
                   "metadata":self.tempValue}]

        with open(self.tmpFile, 'w') as f:
            json.dump(annos, f)


    @cfg.logClassFunction
    def addAnnotation(self, vials, annotator, behaviour, metadata):

        # if vials == None:
        #     vials = [None]
            
        rng = None
        curFilter = None
            
        if self.annoAltStart is None:
            self.annoAltStart = bsc.FramePosition(self.annoDict, self.posPath, 
                                                                    self.idx)
            
            self.annoEnd = bsc.FramePosition(self.annoDict, self.posPath, 
                                             self.idx)
             
            self.annoAltFilter = Annotation.AnnotationFilter(vials, [annotator], 
                                                                    [behaviour])
            
            self.tempValue = dict()
            self.updateAnnotationProperties(metadata)
            
            
        else:
            curFilter = Annotation.AnnotationFilter(vials, [annotator], 
                                                    [behaviour])
            # sameAnnotationFilter = \
            #         all((sorted(curFilter[i]) == sorted(self.annoAltFilter[i]) \
            #                             for i in range(len(curFilter))))
            # if not sameAnnotationFilter:
            if not curFilter == self.annoAltFilter:
                return
                # self.escapeAnnotationAlteration()
            else:
                annoEnd = bsc.FramePosition(self.annoDict, self.posPath, self.idx)    
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.annotation.frameList)#[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
                behaviour = self.disambiguateDoubleBehaviourNames(vials, annotator, behaviour, rng)

                self.addAnnotationRange(rng, vials, annotator, behaviour)
                
                self.annoAltStart = None

        # if vials == [None]:
        #     vials = None

        for aV in self.annoViewList:
            if (aV.behaviourName == None) \
            or (behaviour == aV.behaviourName) \
            or (behaviour in aV.behaviourName):
                if (aV.annotator == None) \
                or (annotator == aV.annotator) \
                or (annotator in aV.annotator):
                    if vials == aV.vialNo:
                        cfg.log.debug("calling aV.addAnno()")
                        aV.addAnno(self.posPath, self.idx, metadata)
                
        return rng, curFilter

    def eraseAnnotationRange(self, rngs, vials, annotator, behaviour):
        if type(vials) is not list:
            vials = [vials]

        for key in rngs:
            for v in vials:
                self.annoDict[key].annotation.removeAnnotation(v,
                                        rngs[key],
                                        annotator, behaviour)
                # tmpFilename = '.'.join(key.split(".")[:-1]) + ".bhvr~"
                # self.annoDict[key].annotation.saveToTmpFile(tmpFilename)

            # refresh annotation in anno view
            self.eraseAnnotationFromAnnoViews(v, annotator, behaviour, key)

        self.saveTempAnnotationEdit(rngs, vials, annotator, behaviour, 'erase')
        
    @cfg.logClassFunction
    def eraseAnnotation(self, vials, annotator, behaviour):
        # if vials == None:
        #     vials = [None]
            
        rng = None
        curFilter = None
             
        if self.annoAltStart == None:
            self.annoAltStart = bsc.FramePosition(self.annoDict, self.posPath, 
                                                                    self.idx)
            
            self.annoEnd = bsc.FramePosition(self.annoDict, self.posPath, 
                                             self.idx)
             
            self.annoAltFilter = Annotation.AnnotationFilter(vials, [annotator], 
                                                                    [behaviour])
        else:
            curFilter = Annotation.AnnotationFilter(vials, [annotator], 
                                                    [behaviour])
            # sameAnnotationFilter = \
            #         all((sorted(curFilter[i]) == sorted(self.annoAltFilter[i]) \
            #                             for i in range(len(curFilter))))

            if not curFilter == self.annoAltFilter:
                # self.escapeAnnotationAlteration()
                return
            else:
                annoEnd = bsc.FramePosition(self.annoDict, self.posPath, self.idx)
                
                ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  ## TODO ## TODO  : make that [0] dynamic
                lenFunc = lambda x: len(x.annotation.frameList)#[0])
                        
                rng = bsc.generateRangeValuesFromKeys(self.annoAltStart, annoEnd, lenFunc=lenFunc)
                self.annoAltStart = None
                
                self.eraseAnnotationRange(rng, vials, annotator, behaviour)
                                    
                cfg.logGUI.info(json.dumps({"vials":vials,
                                       "key-range":rng, 
                                       "annotator":annotator,
                                       "behaviour":behaviour}))
                
                self.annoAltStart = None

        # if vials == [None]:
        #     vials = None

        for aV in self.annoViewList:
            if aV.behaviourName == None \
            or behaviour == aV.behaviourName \
            or behaviour in aV.behaviourName:
                if aV.annotator == None \
                or annotator == aV.annotator \
                or annotator in aV.annotator:
                    if vials == aV.vialNo:
                        cfg.log.debug("eraseAnnotation")
                        aV.eraseAnno(self.posPath, self.idx)
        return rng, curFilter

    def findRangeOfAnnotation(self, frameIdx, posKey, filterTuple,
                              direction='both'):
        """
        direction (string):
                direction in which the annotation is traced.
                Possible values:
                                'both'
                                'right'
                                'left'

        """
        rngs = dict()
        rngs[posKey] = self.annoDict[posKey].annotation.\
                     findConsequtiveAnnotationFrames(filterTuple,
                                                     frameIdx,
                                                     direction=direction)

        # check whether the range extends over the right edge of the current
        # annotation file
        curKey = posKey
        if direction == 'both' or direction == 'right':
            while rngs[curKey][-1] == \
                    len(self.annoDict[curKey].annotation.frameList):
                curKey = sorted(self.annoDict.keys()).index(curKey) + 1
                if curKey >= len(self.annoDict.keys()):
                    break

                a = self.annoDict[curKey].annotation.filterFrameList(
                                                            filterTuple,
                                                            [0],
                                                            exactMatch=True)
                if a.frameList:
                    rngs[curKey] = self.annoDict[curKey].annotation.\
                         findConsequtiveAnnotationFrames(filterTuple,
                                                         0,
                                                         direction=direction)
                else:
                    break

        # check whether the range extends over the left edge of the current
        # annotation file
        curKey = posKey
        if direction == 'both' or direction == 'left':
            while rngs[curKey][0] == 0:
                curKey = sorted(self.annoDict.keys()).index(curKey) - 1
                if curKey < 0:
                    break

                l = len(self.annoDict[curKey].annotation.frameList)
                a = self.annoDict[curKey].annotation.filterFrameList(
                                                            filterTuple,
                                                            [l],
                                                            exactMatch=True)
                if a.frameList:
                    rngs[curKey] = self.annoDict[curKey].annotation.\
                         findConsequtiveAnnotationFrames(filterTuple, 0)
                else:
                    break

        return rngs

    def editAnnotationMetaCurrentFrame(self, selectedVial, annotator,
                                    behaviour, metaKey, newMetaValue):
        self.annoDict[self.posPath].annotation.editMetadata(
                                                    selectedVial, self.idx,
                                                    annotator, behaviour,
                                                    metaKey, newMetaValue)

    def editAnnotationLabel(self, vial, annotatorOld,
                                behaviourOld, annotatorNew, behaviourNew):
        filtOld = Annotation.AnnotationFilter(vial, [annotatorOld],
                                              [behaviourOld])

        rngs = self.findRangeOfAnnotation(self.idx, self.posPath, filtOld)
        if vial is None:
            vial = [None]

        behaviourNew = self.disambiguateDoubleBehaviourNames(vial, annotatorNew,
                                                             behaviourNew, rngs)

        vial = vial[0]
        print "editAnnotationLabel", rngs, behaviourOld, behaviourNew

        for k, rng in rngs.items():
            self.annoDict[k].annotation.renameAnnotation(
                                                vial, rng,
                                                annotatorOld, behaviourOld,
                                                annotatorNew, behaviourNew)
            self.eraseAnnotationFromAnnoViews(vial, annotatorOld, behaviourOld, k)
            self.addAnnotationToAnnoViews(vial, annotatorNew, behaviourNew, k)


    def eraseAnnotationSequence(self, vials, annotator, behaviour,
                                direction='both'):
        filt = Annotation.AnnotationFilter(vials, [annotator],
                                              [behaviour])

        rngs = self.findRangeOfAnnotation(self.idx, self.posPath,
                                          filt, direction)

        if vials is None:
            vials = [None]

        self.eraseAnnotationRange(rngs, vials, annotator, behaviour)


        return rngs, filt

    def eraseAnnotationCurrentFrame(self, vials, annotator, behaviour):
        filt = Annotation.AnnotationFilter(vials, [annotator],
                                              [behaviour])
        rngs = {self.posPath: [self.idx]}

        if vials is None:
            vials = [None]

        self.eraseAnnotationRange(rngs, vials, annotator, behaviour)

        return rngs, filt

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
            if len(self.patchesFolder) > 0:
                dirname = os.path.dirname(key)[:-len(self.patchesFolder)] + \
                            self.bhvrFolder
            else:
                dirname = os.path.join(os.path.dirname(key),
                                        self.bhvrFolder)
            
            basename = '.'.join(os.path.basename(key).split(".")[:-1]) + \
                       ".bhvr"
            tmpFilename = os.path.join(dirname, basename)
            print "saving behaviour files to", tmpFilename
            self.annoDict[key].annotation.saveToFile(tmpFilename)

        if os.path.exists(self.tmpFile):
            os.remove(self.tmpFile)

            
            
            