from collections import OrderedDict
import numpy as np
from PySide import QtCore, QtGui
import qimage2ndarray as QI2A
import pylab as plt
import scipy.misc as msc


import pyTools.misc.config as cfg



class CacheBase(QtCore.QObject):
    def __init__(self, size=100):
        super(CacheBase, self).__init__()
        self.size = size
        self.cache = OrderedDict()
        
    def getItem(self, key):
        try:
            datum = self.cache[key]
            del self.cache[key]
            self.cache[key] = datum
        except KeyError:
            datum = self.retrieveDatum(key)
            
        return datum
    
    def retrieveDatum(self, key):
        try:
            datum = self.loadDatum(key)
        except IOError:
            datum = None
            
        if  len(self.cache.keys()) >= self.size:
            self.cache.popitem(last=False)
            
        self.cache[key] = datum
        
        return datum
    
    def loadDatum(self, key):
        return key
    

class CachePrefetchBase(CacheBase, QtCore.QObject):
    fetchSignal = QtCore.Signal(str)

    def __init__(self, sortedFileList, size=100):
        super(CachePrefetchBase, self).__init__(size)
        self.fileList = sortedFileList
        self.fetchThread = QtCore.QThread()
        self.fetchObj = FileFetcher(self.loadDatum)

        self.fetchObj.moveToThread(self.fetchThread)
        self.fetchThread.start()

        self.fetchSignal.connect(self.fetchObj.fetchFile)
        self.fetchObj.fetchedFile.connect(self.insertNewData)
        self.prefetchList = []

    def prefetch(self, key):
        if not key in self.prefetchList:
            self.prefetchList += [key]
            self.fetchSignal.emit(key)

    @QtCore.Slot(list)
    def insertNewData(self, lst):
        key = lst[0]
        data = lst[1]
        if  len(self.cache.keys()) >= self.size:
            self.cache.popitem(last=False)

        self.cache[key] = data
        del self.prefetchList[self.prefetchList.index(key)]

    def checkNeighbours(self, key, rng=10):
        if len(self.fileList) == 0:
            return

        idx = self.fileList.index(key)
        for i in range(rng):
            try:
                datum = self.cache[self.fileList[idx + i]]
            except KeyError:
                self.prefetch(self.fileList[idx + i])
            except IndexError:
                pass

        for i in range(rng):
            try:
                datum = self.cache[self.fileList[idx - i]]
            except KeyError:
                self.prefetch(self.fileList[idx - i])
            except IndexError:
                pass

    def checkNeighboursRight(self, rng=10):
        try:
            key = sorted(self.cache.keys())[-1]
        except IndexError:
            # cache is empty, probably because self.fileList is []
            return

        self.checkNeighbours(key, rng)

    def getItem(self, key, checkNeighbours=False):
        data = super(CachePrefetchBase, self).getItem(key)

        if checkNeighbours:
            self.checkNeighbours(key)

        return data

class FileFetcher(QtCore.QObject):
    fetchedFile = QtCore.Signal(list)

    def __init__(self, loadingFunc):
        super(FileFetcher, self).__init__()
        self.loadingFunc = loadingFunc

    @QtCore.Slot(str)
    def fetchFile(self, file):
        data = self.loadingFunc(file)
        self.fetchedFile.emit([file, data])

class PosFileCache(CachePrefetchBase):
    def loadDatum(self, key):
        return np.load(key)

class BackgroundFileCache(CachePrefetchBase):
    def __init__(self, vialROI, sortedFileList, size=100):
        super(BackgroundFileCache, self).__init__(
                                        sortedFileList=sortedFileList,
                                        size=size)

        self.vialROI = vialROI

    def loadDatum(self, key):
        img = QtGui.QImage()
        img.load(key)

        rawImg = QI2A.recarray_view(img)

        background = np.zeros((rawImg.shape[0], rawImg.shape[1], 4),
                              dtype=rawImg['r'].dtype)

        background[:,:,0] = rawImg['r']
        background[:,:,1] = rawImg['g']
        background[:,:,2] = rawImg['b']
        background[:,:,3] = rawImg['a']

        # crop and rotate background image to show only one vial
        rng = slice(*self.vialROI)
        background = np.rot90(background[:, rng]).astype(np.uint32)

        h = background.shape[0]
        w = background.shape[1]

        # grey conversion
        b = background[:,:,0] * 0.2126 + \
            background[:,:,1] * 0.7152 + \
            background[:,:,2] * 0.0722
        background[:,:,0] = b
        background[:,:,1] = b
        background[:,:,2] = b

        im = QI2A.array2qimage(background)
        im = im.convertToFormat(QtGui.QImage.Format_RGB32)

        return im