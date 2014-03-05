from PySide import QtGui
from PySide import QtCore


import pyTools.system.videoExplorer as VE
import pyTools.videoProc.annotation as Annotation
import pyTools.misc.config as cfg

import numpy as np
import time
import copy





class BaseThread(QtCore.QThread):
    @cfg.logClassFunction
    def __init__(self, name):
        super(BaseThread, self).__init__()
        self.setObjectName(name)
        self.exiting = False

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
        
    def run(self):
        self.exec_()
        
    @cfg.logClassFunction
    def delay(self, secs):
        dieTime = QtCore.QTime.currentTime().addSecs(secs)
        while(QtCore.QTime.currentTime() < dieTime ):
            self.processEvents(QtCore.QEventLoop.AllEvents, 100)
        
from IPython.parallel import Client, dependent
# Subclassing QObject and using moveToThread
# http://labs.qt.nokia.com/2007/07/05/qthreads-no-longer-abstract/
class VideoLoader(QtCore.QObject):        
    loadedVideos = QtCore.Signal(list) 
    loadedAnnotation = QtCore.Signal(list)
    eof = QtCore.Signal(list)
    finished = QtCore.Signal()   
    startLoading = QtCore.Signal()

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
    
    @cfg.logClassFunction
    def __init__(self, posPath, idxSlice, selectedVials=[1], 
                 thread=None, eofCallback=None):
        super(VideoLoader, self).__init__(None)        
        self.init(posPath, idxSlice, selectedVials, thread)
        
    def init(self, posPath, idxSlice, selectedVials=[1], 
             thread=None):
        self.loading = False
        
        self.videoLength = -1
        self.frameList = []

        self.posPath = copy.copy(posPath)      
        
        self.selectedVials = selectedVials

        
        self.thread = thread
        
        self.videoEnding = '.mp4'
        
        self.imTransform = lambda x: x
        
        self.endOfFile = [] 
        self.idxSlice = idxSlice

    def maxOfSelectedVials(self):
        return 0

    @QtCore.Slot()
    def loadVideos(self):
        self.exiting = False
        self.loading = True
        
        #####################################################################   TODO: fix properly!!
        # quick-fix of file extension dilemma
#         self.posPath = self.posPath.split(self.videoEnding)[0] + '.pos.npy'

        cfg.log.info("loadVideos: {0} @ {1}".format(self.posPath, QtCore.QThread.currentThread().objectName()))
        #         print "RUN", QThread.currentThread().objectName(), QApplication.instance().thread().objectName(), '\n'

        
        #@lbview.parallel(block=True)
        def loadVideo(f, idxSlice, vialNo, imTransform=None):    
#             from qimage2ndarray import array2qimage
            import sys
            from pyTools.system.videoExplorer import videoExplorer
            import numpy as np    
            from PySide.QtGui import QImage
            from scipy.misc import imresize 
            
            
            vE = videoExplorer()        
            
            if imTransform is None:
                imTransform = lambda x: imresize(x, [64, 64])
#             else:
#                 imTransform = lambda x: imresize(x)
                
            
            im = dict()#np2qimage(np.rot90(vE.getFrame(f, info=False, 
            #                              frameMode='RGB')) * 255)]
            endOfFile = None
            try:
                frame = vE.getFrame(f, idxSlice.start, info=False, 
                                    frameMode='RGB')
                im[idxSlice.start] = [frame, imTransform(frame)]
            except StopIteration:
                endOfFile = idxSlice.start
                           
            
            for idx in range(idxSlice.start+1, idxSlice.stop):
                if endOfFile is not None:
                    break
#                 im += [np2qimage(np.rot90(frame) * 255)]
#                 im += [[imresize(frame, 0.5), imresize(frame, [64,64])]]
                try:
                    frame = vE.next()
                    im[idx] = [frame, imTransform(frame)]
                except StopIteration:
                    endOfFile = idx
                        
            ret = dict()
            
            ret["vialNo"] = vialNo
            ret["qi"] = im
            ret['endOfFile'] = endOfFile
            
            del vE
            
            return ret     
            
            
        results = []
        
        if self.selectedVials is None:
            f = self.posPath# self.posPath.split(self.videoEnding)[0] + self.videoEnding#.v{0}.{1}'.format(i, 'avi')
            results = loadVideo(f, self.idxSlice, 0, self.imTransform)
            self.frameList = [copy.copy(results["qi"])] 
            self.endOfFile = [copy.copy(results['endOfFile'])]
            
        else:                
            f = self.posPath# self.posPath.split(self.videoEnding)[0] + self.videoEnding#.v{0}.{1}'.format(i, 'avi')
            results = loadVideo(f, self.idxSlice, self.selectedVials[0], self.imTransform)
            self.frameList = [copy.copy(results["qi"])] 
            self.endOfFile = [copy.copy(results['endOfFile'])]
            
                    
        if True:#not self.exiting:
            # using max(self.selectedVials) to make sure that the list entry
            # has actually some frames and is no dummy
            self.videoLength = len(self.frameList[self.maxOfSelectedVials()])
            
            cfg.log.debug("videoLoader: load positions")
            try:
                self.pos = np.load(self.posPath.split(self.videoEnding)[0] + 
                                   '.pos.npy')[self.idxSlice]
            except IOError:
                # create dummy positions to keep stuff internally going
                self.pos = np.zeros((self.videoLength, 
                                     self.maxOfSelectedVials() + 1,
                                     2))
        
        
        cfg.log.info("finished loading, emiting signal {0} {1} {2}".format(self.posPath, self.videoLength, self.idxSlice))
# 
        
        
        lastFrameNo = None
        for eof in self.endOfFile:
            if eof is not None:
                if lastFrameNo is None:
                    lastFrameNo = eof
                elif lastFrameNo is not eof:
                    raise ValueError("two video files in the same minute have different lengths!")
        
        if lastFrameNo is not None:
            self.eof.emit([self.posPath, lastFrameNo])
                
        self.loading = False
#         self.finished.emit()  
#         self.loadedAnnotation.emit([self.annotation, self.posPath])
        
        cfg.log.debug("finsihed loadVideos: {0} [{1}] @ {2}".format(self.posPath, self.idxSlice, QtCore.QThread.currentThread().objectName()))
        
        
    @cfg.logClassFunction
    def getVideoLength(self):        
        while self.loading:
            cfg.log.warning("(getVideoLength)------------------- waiting for frame because its not buffered yet")
            time.sleep(0.5)
            
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
            return False
            

#         if self.exiting:
#             return
        
        if idx in self.frameList[0].keys():
            out = []
            for i in range(len(self.frameList)):
#                 if not idx >= len(self.frameList[i]):
                out += [self.frameList[i][idx]]
#                 else:
#                     out += []
                
            return out
        else:
            cfg.log.error("error in fetching key {0}, idx {1}".format(self.posPath, idx))
            raise RuntimeError("Video frame was not available (index out of range (requested {0} of {1} @ {2})".format(idx, len(self.frameList), self.posPath))
            
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
        
        
        
        
class VideoLoaderLuncher(QtCore.QObject):        
    createdVideoLoader = QtCore.Signal(list)  
    loadVideos = QtCore.Signal() 
    
    @cfg.logClassFunction
    def __init__(self, eofCallback):
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
        super(VideoLoaderLuncher, self).__init__(None)
            
        self.availableVLs = []
        self.dumpingPlace = []
        self.threads = dict()
        self.eofCallback = eofCallback
            
    
    
#     @cfg.logClassFunction
    @QtCore.Slot(list)
    def lunchVideoLoader(self, lst):
        """
        Args:
            lst ([string, callback])
        """
#         print "RUN", QThread.currentThread().objectName(), QApplication.instance().thread().objectName(), '\n'
        path = lst[0]
        vH = lst[1]
        selectedVials = lst[2]
        idx = lst[3]
        idxSlice = lst[4]
        
        if len(self.availableVLs) == 0:
            cfg.log.debug("create new VideoLoader {0} {1}".format(path,
                                                        idxSlice))     
            
#             vL = VideoLoader(path, vH, selectedVials=selectedVials) 
                                     
            videoLoaderThread = MyThread("videoLoader {0}".format(len(
                                                        self.threads.keys())))
            
            vL = VideoLoader(path, idxSlice=idxSlice, 
                             thread=videoLoaderThread, 
                             selectedVials=selectedVials)     
            
            
                        
            vL.moveToThread(videoLoaderThread)         
            videoLoaderThread.start()

            vL.startLoading.connect(vL.loadVideos)
            vL.eof.connect(self.eofCallback)
            
            cfg.log.debug("finished thread coonecting signal create new VideoLoader {0}".format(path)) 
            vL.startLoading.emit()
            cfg.log.debug("finished thread emit create new VideoLoader {0}".format(path)) 
            self.threads[vL] = [videoLoaderThread, vL.startLoading]
            
            cfg.log.debug("finished create new VideoLoader {0}".format(path))  
        else:
            vL = self.availableVLs.pop()
            cfg.log.debug("recycle new VideoLoader {0}, was previous: {1}".format(path, vL.posPath))
            thread, signal = self.threads[vL]
            vL.init(path, idxSlice=idxSlice, thread=thread, 
                    selectedVials=selectedVials)     
            signal.emit()

        self.createdVideoLoader.emit([path, idx, vL])
#         cfg.log.debug("finish")
            
#     @cfg.logClassFunction
    @QtCore.Slot(list)
    def deleteVideoLoader(self, lst):
        for vL in self.dumpingPlace:
            if vL is not None and not vL.loading:                 
                self.availableVLs += [vL]
                self.dumpingPlace.remove(vL)
                
        vL = lst[0]
#         vidPath = lst[1]
        
        # TODO is this potential memory leak?
        if vL is not None and not vL.loading:             
            self.availableVLs += [vL]
        else:
            self.dumpingPlace += [vL]
        
    @QtCore.Slot()    
    def aboutToQuit(self):
        print "video-launcher, about to quit"
        for key in self.threads:
            self.threads[key].quit()
            
class AnnotationLoaderLuncher(QtCore.QObject):      
    createdAnnotationLoader = QtCore.Signal(list)  
    loadAnnotations = QtCore.Signal()
    
    def __init__(self, loadedCallback, videoEnding): 
        super(AnnotationLoaderLuncher, self).__init__(None)
            
        self.availableALs = []
        self.dumpingPlace = []
        self.threads = dict()
        self.loadedCallback = loadedCallback
        self.videoEnding = videoEnding
    
    @QtCore.Slot(list)
    def lunchAnnotationLoader(self, lst):
        path = lst[0]
        aL = None
        
        videoPath = copy.copy(path)
        
        path = '.'.join(path.split(self.videoEnding)[:1]) + '.bhvr'
        
        if len(self.availableALs) == 0:
            cfg.log.debug("create new AnnotationLoader {0}".format(path))     
            
#             vL = VideoLoader(path, vH, selectedVials=selectedVials) 
                                     
            annotationLoaderThread = MyThread("AnnotationLoader {0}".format(len(
                                                        self.threads.keys())))
            
            aL = AnnotationLoader(path, annotationLoaderThread)                 
            aL.moveToThread(annotationLoaderThread)         
            annotationLoaderThread.start()

            aL.startLoading.connect(aL.loadAnnotation)
            aL.loadedAnnotation.connect(self.loadedCallback)
            
            cfg.log.debug("finished thread coonecting signal create new AnnotationLoader {0}".format(path)) 
            aL.startLoading.emit()
            cfg.log.debug("finished thread emit create new AnnotationLoader {0}".format(path)) 
            self.threads[aL] = [annotationLoaderThread, aL.startLoading]
            
            cfg.log.info("finished create new AnnotationLoader {0}".format(path))  
        else:
            aL = self.availableALs.pop()
            cfg.log.info("recycle new AnnotationLoader {0}, was previous: {1}".format(path, aL.path))
            thread, signal = self.threads[aL]
            aL.init(path, thread)     
            signal.emit()

        self.createdAnnotationLoader.emit([aL, videoPath])
        
#     @cfg.logClassFunction
    @QtCore.Slot(list)
    def deleteAnnotationLoader(self, lst):
        for aL in self.dumpingPlace:
            if aL is not None and not aL.loading:  
                if aL.annotation.hasChanged:
                    cfg.log.info("saving {0}".format(aL))     
                    aL.annotation.saveToFile(aL.path)    
                cfg.log.info("making {0} available again".format(aL))           
                self.availableALs += [aL]
                self.dumpingPlace.remove(aL)
                
        aL = lst[0]
#         vidPath = lst[1]
        
        # TODO is this potential memory leak?
        if aL is not None and not aL.loading:  
            if aL.annotation.hasChanged:
                aL.annotation.saveToFile(aL.path)
                
            cfg.log.info("making {0} available again".format(aL))   
            self.availableALs += [aL]
        else:
            self.dumpingPlace += [aL]
        
    @QtCore.Slot()    
    def aboutToQuit(self):
        print "annotation-launcher, about to quit"
        for key in self.threads:
            self.threads[key].quit()
            
class AnnotationLoader(QtCore.QObject):        
    loadedAnnotation = QtCore.Signal(list) 
    startLoading = QtCore.Signal()

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wait()
                
        if self.annotation is not None:
            self.annotation.saveToFile('.'.join(self.posPath.split('.')[:-1]) + '.bhvr')
    
    @cfg.logClassFunction
    def __init__(self, path, thread, vialNames=None):
        super(AnnotationLoader, self).__init__(None)        
        self.init(path, thread, vialNames=None)
        
    def init(self, path, thread, vialNames=None):
        if vialNames is None:
            self.vialNames = [None]
        else:
            self.vialNames = vialNames
        
        self.loading = False
        
        self.annotation = None
        
#         self.annotation = None # annotation object
        
        self.path = copy.copy(path)      
        
        self.thread = thread        
    
    @cfg.logClassFunction
    def loadAnnotation(self):
        from os.path import isfile    
        
        self.loading = True     
                    
        f = '.'.join(self.path.split('.')[:-1]) + '.bhvr'
        if isfile(f):
            cfg.log.debug("AnnotationLoader: f exists create empty Annotation")
            out = Annotation.Annotation()
            cfg.log.debug("AnnotationLoader: created Annotation. try to load..")
            try:
                out.loadFromFile(f)
                cfg.log.info("AnnotationLoader: loaded Annotation {0} {1}".format(self.path, self))                    
            except:
                cfg.log.warning("load annotation of "+f+" failed, reset annotaions")
                videoLength = self.retrieveVideoLength(self.path)
                out = Annotation.Annotation(frameNo=videoLength, vialNames=self.vialNames)
        else:
            cfg.log.warning("AnnotationLoader: f does NOT exist create empty Annotation")
            videoLength = self.retrieveVideoLength(self.path)
            out = Annotation.Annotation(frameNo=videoLength, vialNames=self.vialNames)
            cfg.log.info("new annotation with length {0}".format(videoLength))
            
        self.annotation = out
#         self.loadedAnnotation.emit([self, self.path])

        cfg.log.debug("finished loading annotation {0}".format(self.path))
        self.loadedAnnotation.emit([self.path, len(self.annotation.frameList)])
        self.loading = False
        
        
    @cfg.logClassFunction
    def retrieveVideoLength(self, filename, initialStepSize=10000):
        """
        Finds video length by accessing it bruteforce
        
        """
        idx = 0
        modi = initialStepSize
        vE = VE.videoExplorer()
        
        if self.vialNames == [None]:
            filename = filename.split('.bhvr')[0] + '.avi'
        else:            
            filename = filename.split('.bhvr')[0] + '.v{0}.avi'.format(
                                                            self.vialNames[0])
        
        while modi > 1:
            while True:
                try:
                    vE.getFrame(filename, frameNo=idx, frameMode='RGB')
                except StopIteration:
                    break
                
                idx += modi
                
            idx -= modi
            modi /= 2
            

        return idx + 1
    
    
class VideoLengthQuery(QtCore.QObject):
    # signal ([filename, length])
    videoLength = QtCore.Signal(list)
    startProcess = QtCore.Signal()
    
    def __init__(self, filename, bufferWidth, resultSlot):
        super(VideoLengthQuery, self).__init__(None)
        self.filename = filename
        self.bufferWidth = bufferWidth
        self.length = None
        
        self.vE = VE.videoExplorer()
        
        self.thread = MyThread("VideoLengthQuery")
                             
        self.moveToThread(self.thread)         
        self.thread.start()
        
        self.startProcess.connect(self.retrieveVideoLength) 
        self.videoLength.connect(resultSlot)
        self.startProcess.emit()
        
        
       
    @QtCore.Slot()
    def retrieveVideoLength(self):
        """
        Finds video length by accessing it bruteforce
        
        """
        idx = 0
        modi = self.bufferWidth * 1000
        
        while modi > 1:
            while True:
                try:
                    self.vE.getFrame(self.filename, frameNo=idx, 
                                    frameMode='RGB')
                except StopIteration:
                    break
                
                idx += modi
                
            idx -= modi
            modi /= 2
            
            print modi, idx

        self.videoLength.emit([self.filename, idx])
        self.length = idx
        self.thread.quit()
        
        
        
class MyThread(QtCore.QThread):    
    finished = QtCore.Signal()
    wrapUp = QtCore.Signal()
    
    def __init__(self, name):
        super(MyThread, self).__init__()
        self.setObjectName(name)    
        
        
        self.finished.connect(self.deleteLater)
#         self.finished.connect(self.deleteLater)        
        self.exiting = False

    @cfg.logClassFunction
    def __del__(self):        
        cfg.log.debug("deleting")
        self.exiting = True
        self.wrapUp.emit()
        self.wait()

    def run(self):
        cfg.log.debug("RUN THREAD {0} {1}".format(QtCore.QThread.currentThread().objectName(),
                                                 QtGui.QApplication.instance().thread().objectName()))
        self.exec_()
        print "RUN DONE", QtCore.QThread.currentThread().objectName()        
        self.finished.emit()
        