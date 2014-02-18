import zerorpc
import pyTools.misc.FrameDataVisualization as FDVT
import pyTools.system.videoPlayerComServer as comServer
from time import time


class videoPlayerComClientBase(zerorpc.Client):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(videoPlayerComClientBase, self).__init__()
        
        self.connect(address)
        

class FDVTComClientRequester(videoPlayerComClientBase):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(FDVTComClientRequester, self).__init__(address=address)
        
        self.fdvt = None
        self.id = 0
        
        
    def generateFDVT(self):
        dayRng = range(2)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        
        self.fdvt = FDVT.FrameDataVisualizationTreeArrayBase()
        self.fdvt.generateRandomArraySequence(dayRng, hourRng, minuteRng, 
                                              frameRng)
        
    def getNewId(self):
        id = self.id
        self.id += 1
        return id
        
    def pushFDVT(self):
        qid = self.getNewId()
        rank = 0
        qtype = "FDVTT"
        data = self.fdvt.serializeData()
        
        query = comServer.QueryTuple(qid, rank, qtype, data, None)        
        self.pushQuery(query.convertToDict())


class FDVTComClientReplier(videoPlayerComClientBase):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(FDVTComClientReplier, self).__init__(address=address)
        
        self.fdvt = FDVT.FrameDataVisualizationTreeArrayBase()
        self.id = 0

    def queryServer(self):
        query = comServer.QueryTuple(**self.nextQuery())
        self.fdvt.deserialize(query.query)


if __name__ == "__main__":
    req = FDVTComClientRequester("tcp://127.0.0.1:4244")
    rep = FDVTComClientReplier("tcp://127.0.0.1:4244")
    
    req.generateFDVT()
    
    t1 = time()
    req.pushFDVT()
    rep.queryServer()
    print "message passing took {0} sec".format(time() - t1)
    
    print rep.fdvt.tree.keys()