from collections import OrderedDict
import numpy as np
from PySide import QtCore


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
        datum = self.loadDatum(key)
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
        self.fetchObj = FileFetcher()

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
        key = sorted(self.cache.keys())[-1]
        self.checkNeighbours(key, rng)

    def getItem(self, key, checkNeighbours=False):
        data = super(CachePrefetchBase, self).getItem(key)

        if checkNeighbours:
            self.checkNeighbours(key)

        return data

class FileFetcher(QtCore.QObject):
    fetchedFile = QtCore.Signal(list)

    @QtCore.Slot(str)
    def fetchFile(self, file):
        data = np.load(file)
        self.fetchedFile.emit([file, data])

class PosFileCache(CachePrefetchBase):
    def loadDatum(self, key):
        return np.load(key)