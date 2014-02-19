import zerorpc
import pyTools.misc.FrameDataVisualization as FDVT
import pyTools.system.videoPlayerComServer as comServer
from time import time


class VideoPlayerComClientBase(zerorpc.Client):
    def __init__(self, address="tcp://127.0.0.1:4242"):
        super(VideoPlayerComClientBase, self).__init__()
        
        self.connect(address)
        self.cid = self.requestClientID()
        

class FDVTComClientRequester(VideoPlayerComClientBase):
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


class FDVTComClientReplier(VideoPlayerComClientBase):
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
        self.fdvt = FDVT.FrameDataVisualizationTreeArrayBase()
        
        if debug:
            self.generateRandomFDVT()
                
        if comServer is not None:
            self.bus = comServer
        else:
            self.bus = VideoPlayerComClientBase(address)
            
        self.cid = self.bus.requestClientID()
        self.qid = 0
        
    
    def generateRandomFDVT(self):
        dayRng = range(2)
        hourRng = range(24)
        minuteRng = range(60)
        frameRng = range(1800)

        self.fdvt.generateRandomArraySequence(dayRng, hourRng, minuteRng, 
                                              frameRng)
    
    def sendLabelTree(self):
        data = self.fdvt.serializeData()        
        query = comServer.ReplyTuple(None, None, None, "baseFDVT", data)             
        self.bus.pushBaseLabelTree(query.convertToDict())
        
    
    def requestNewJob(self):
        msg = self.bus.nextQuery()
        if msg is None:
            self.noNewJob()
            return
        
        query = comServer.QueryTuple(**msg)
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
        
        
    ###### FUNCTIONS TO OVERLOAD ##############################################
        
    def noNewJob(self):
        print "GUIComBase: no more queries in the server"      
        
    def labelFrame(self, query):
        print "GUIComBase: labelFrame -- {0}".format(query)
        
    def updateFDVT(self, query):
        print "GUIComBase: updateFDVT -- {0}".format(query) 
        
    def labelFrameRange(self, query):
        print "GUIComBase: labelFrameRange -- {0}".format(query)
        
    ###### FUNCTIONS TO OVERLOAD ##############################################
    
    
class ALComBase(object):
    def __init__(self, address="tcp://127.0.0.1:4242", comServer=None):
        self.fdtv = FDVT.FrameDataVisualizationTreeArrayBase()
        
        if comServer is not None:
            self.bus = comServer
        else:
            self.bus = VideoPlayerComClientBase(address)
            
        self.cid = self.bus.requestClientID()
        self.qid = 0
        
        
    def queryNextCompletedJob(self):
        msg = self.bus.nextReply()
        if msg is None:
            self.noNewReply()
            return
            
        reply = comServer.ReplyTuple(**msg)
        
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
            
            
    def prepareQuery(self, job, priority, data):
        query = dict()
        query['cid'] = self.cid
        query['qid'] = self.qid
        self.qid += 1
        query['job'] = job
        query['priority'] = priority
        query['query'] = data
        
        return query
            
        
    def pushFDVT(self, fdvt, priority=1):
        query = self.prepareQuery(job=0, priority=priority, data=fdvt)
        self.bus.pushQuery(query)
            
            
    def queryFrameLabel(self, fIdx, priority=1):
        query = self.prepareQuery(job=1, priority=priority, data=fIdx)
        self.bus.pushQuery(query)
            
            
    def queryFrameRangeLabel(self, fRng, priority=1):
        query = self.prepareQuery(job=2, priority=priority, data=fRng)
        self.bus.pushQuery(query)
        
        
    def requestBaseLabelTree(self):
        reply = comServer.ReplyTuple(**self.bus.requestBaseLabelTree())
        self.fdtv.deserialize(reply.reply)
        
        
    ###### FUNCTIONS TO OVERLOAD ##############################################
                    
    def noNewReply(self):
        print "ALComBase: no more replies in the server"          
        
    def updatedFDVT(self, reply):
        print "ALComBase: updatedFDVT -- {0}".format(reply)
        
    def updateFrame(self, reply):
        print "ALComBase: updateFrame -- {0}".format(reply)
        
    def updateFrameRange(self, reply):
        print "ALComBase: updateFrameRange -- {0}".format(reply)
            
        
    def jobFailed(self, reply):
        raise reply.reply
    
    ###### FUNCTIONS TO OVERLOAD ##############################################
    
        
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