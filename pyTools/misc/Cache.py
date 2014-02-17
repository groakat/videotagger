from collections import OrderedDict
import numpy as np

class CacheBase:
    
    def __init__(self, size=100):
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
    
    
class PosFileCache(CacheBase):
    def loadDatum(self, key):
        return np.load(key)