import zerorpc
import pyTools.misc.FrameDataVisualization as FDVT
import pyTools.system.videoPlayerComServer as comServer
from time import time


class videoPlayerComClientBase(zerorpc.Client):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(videoPlayerComClientBase, self).__init__()
        
        self.connect(address)
        self.cid = self.requestClientID()
        

class FDVTComClientRequester(videoPlayerComClientBase):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(FDVTComClientRequester, self).__init__(address=address)
        
        self.fdvt = None
        self.qid = 0
        
        
    def generateFDVT(self):
        dayRng = range(2)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)
        
        self.fdvt = FDVT.FrameDataVisualizationTreeArrayBase()
        self.fdvt.generateRandomArraySequence(dayRng, hourRng, minuteRng, 
                                              frameRng)
        
    def getNewId(self):
        qid = self.id
        self.qid += 1
        return qid
        
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
        
    def replyServer(self):
        pass


###############################################################################


class GUIComBase(object):
    def __init__(self, address="tcp://127.0.0.1:4242", comServer=None, 
                 debug=False):
        self.fdtv = FDVT.FrameDataVisualizationTreeArrayBase()
        
        if debug:
            self.generateRandomFDVT()
                
        if comServer is not None:
            self.bus = comServer
        else:
            self.bus = FDVTComClientReplier(address)
            
        self.cid = self.bus.requestClientID()
        
    
    def generateRandomFDVT(self):
        dayRng = range(2)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)

        self.fdtv.generateRandomArraySequence(dayRng, hourRng, minuteRng, 
                                              frameRng)
    
    def sendLabelTree(self):
        data = self.fdvt.serializeData()        
        query = comServer.ReplyTuple(None, None, None, "baseFDVT", data)             
        self.bus.pushBaseTree(query.convertToDict())
        
    
    def requestNewJob(self):
        query = comServer.QueryTuple(**self.bus.nextQuery())
        if query.job == 0:
            self.updateFDVT(query)
        elif query.job == 1:
            self.labelFrame(query)
        elif query.job == 2:
            self.labelFrameRange(query)
        else:
            self.rejectJob(query, ValueError('Cannot identify the job task'))
            
    def rejectJob(self, query, error):
        self.sendCompletedJob(query, error)
    
    def sendCompletedJob(self, query, data):
        """
        Args:
            data (either data requested by job or any standard python Error if job completion failed)
        
        """
        reply = dict()
        reply['qid'] = query.cid
        reply['cid'] = self.cid
        reply['priority'] = query.priority
        reply['job'] = query.job
        reply['reply'] = data
        
        self.bus.pushReply(reply)     
        
        
    def labelFrame(self, query):
        print "GUIComBase: labelFrame"
        
    def updateFDVT(self, query):
        print "GUIComBase: updateFDVT"
        
    def labelFrameRange(self, query):
        print "GUIComBase: labelFrameRange"
    
    
class ALComBase(object):
    def __init__(self, address="tcp://127.0.0.1:4242", comServer=None):
        self.fdtv = FDVT.FrameDataVisualizationTreeArrayBase()
        
        if comServer is not None:
            self.bus = comServer
        else:
            self.bus = FDVTComClientReplier(address)
            
        self.cid = self.bus.requestClientID()
        
        
    def queryNextCompletedJob(self):
        reply = comServer.ReplyTuple(**self.bus.nextReply())
        
        if isinstance(reply.reply, Exception):
            self.jobFailed(reply)
        
        if reply.job == 0:
            self.updatedFDVT(reply)
        elif reply.job == 1:
            self.updateFrame(reply)
        elif reply.job == 2:
            self.updateFrameRange(reply)
        else:
            self.rejectJob(reply, ValueError('Cannot identify the job task'))
            
        
        
    def updatedFDVT(self, query):
        print "ALComBase: updatedFDVT"
        
    def updateFrame(self, query):
        print "ALComBase: updateFrame"
        
    def updateFrameRange(self, query):
        print "ALComBase: updateFrameRange"
            
            
    def jobFailed(self, reply):
        raise reply.reply
    
    def requestBaseTree(self):
        reply = comServer.ReplyTuple(**self.bus.requestBaseTree())
        self.fdvt.deserialize(reply.reply)
        
        
###############################################################################






















if __name__ == "__main__":
    c = zerorpc.Client("tcp://127.0.0.1:4244")
    testArray = []
    for i in range(10):
        testArray += [[i, i*2]]
        
    c.pushTestData(testArray)

# if __name__ == "__main__":
#     req = FDVTComClientRequester("tcp://127.0.0.1:4244")
#     rep = FDVTComClientReplier("tcp://127.0.0.1:4244")
#     
#     req.generateFDVT()
#     
#     t1 = time()
#     req.pushFDVT()
#     rep.queryServer()
#     print "message passing took {0} sec".format(time() - t1)
#     
#     print rep.fdvt.tree.keys()