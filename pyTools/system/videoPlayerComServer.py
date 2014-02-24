import zerorpc
import numpy as np
import datetime
from collections import OrderedDict
from collections import namedtuple

import pyTools.misc.FrameDataVisualization as FDVT 


import copy

DictProxyType = type(object.__dict__)

def make_hash(o):

    """
    Makes a hash from a dictionary, list, tuple or set to any level, that 
    contains only other hashable types (including any lists, tuples, sets, and
    dictionaries). In the case where other kinds of objects (like classes) need 
    to be hashed, pass in a collection of object attributes that are pertinent. 
    For example, a class can be hashed in this fashion:
    
    make_hash([cls.__dict__, cls.__name__])
    
    A function can be hashed like so:
    
    make_hash([fn.__dict__, fn.__code__])
    
    (taken from:
     http://stackoverflow.com/questions/5884066/hashing-a-python-dictionary)
    """
    
    if type(o) == DictProxyType:
        o2 = {}
        for k, v in o.items():
            if not k.startswith("__"):
                o2[k] = v
        o = o2  
    
    if isinstance(o, (set, tuple, list)):    
        return tuple([make_hash(e) for e in o])
    
    if isinstance(o, (slice)):    
        return tuple([make_hash(o.start), make_hash(o.stop), make_hash(o.step)])    
    
    elif not isinstance(o, dict):    
        return hash(o)
    
    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)
    
    return hash(tuple(frozenset(sorted(new_o.items()))))


Query = namedtuple("Query", ['qid', 'cid', 'priority', "job", "query"])
class QueryTuple(Query):
    def __new__(cls, qid, cid, priority, job, query):
        """
        Args:
            qid  -- unique query id (assigned by server)
            cid  -- client id (assigned by client)
            priority -- 0: info (update when you like)
                        1: normal request
                        2: immediate request
                        
            job  -- 0: transmitting new FDVT (update FDVT)
                    1: requesting specific frame label
                    2: requesting frame range
                    
            query -- data
        """
        self = super(QueryTuple, cls).__new__(cls, qid, cid, priority, job, query)
        self._hash = hash(self.qid) * hash(qid) * hash(self.priority) * \
                     hash(self.job) * make_hash(self.query)
        return self
    
    def __hash__(self):
        return self._hash
    
    def convertToDict(self):
        return {'qid': self.qid, 'cid': self.cid, 'priority': self.priority, 
                "job":self.job, "query":self.query}        
    
    def __str__(self):
        return "QueryTuple: qid: {qid}, cid: {cid}, priority: {priority}, job: {job}, query (hash): {query}".format(
                qid=self.qid, cid=self.cid, priority=self.priority, 
                job=self.job, query=make_hash(self.query))
    
        

Reply = namedtuple("Reply", ['qid', 'cid','priority', "job", "reply"])
class ReplyTuple(Reply):
    def __new__(cls, qid, cid, priority, job, reply):
        """
        Args:
            qid  -- unique query id (assigned by client) / each client has its 
                    own full query id space
            cid  -- client id (assigned by client)
            priority -- 0: info (update when you like)
                        1: normal request
                        2: immediate request
                        
            job  -- 0: transmitting new FDVT (update FDVT)
                    1: requesting specific frame label
                    2: requesting frame range
                    
            reply -- data
        """
        self = super(ReplyTuple, cls).__new__(cls, qid, cid, priority, job, reply)
        self._hash = hash(self.qid) * hash(qid) * hash(self.priority) * \
                     hash(self.job) * make_hash(self.reply)
        return self
    
    def __hash__(self):
        return self._hash
    
    def convertToDict(self):
        return {'qid': self.qid, 'cid': self.cid, 'priority': self.priority, 
                "job":self.job, "reply":self.reply}
    
    def __str__(self):
        return "QueryTuple: qid: {qid}, cid: {cid}, priority: {priority}, job: {job}, reply (hash): {reply}".format(
                qid=self.qid, cid=self.cid, priority=self.priority, 
                job=self.job, reply=make_hash(self.reply))
        


class ComServerBase(object):    
    def __init__(self):
        self.queryQueue = dict()
        self.replyQueue = dict()
        self.replyList = dict()
        self.clientIDs = []
        
    def requestClientID(self):
        if self.clientIDs:
            cid = max(self.clientIDs) + 1
            self.clientIDs += [cid]
            print self.clientIDs
            print cid
            return cid
        else:
            self.clientIDs = [0]
            return 0

    def nextQuery(self):
        """ requests the next open query """
        for r in sorted(self.queryQueue.keys(), reverse=True):            
            print "retrieving ", r
            try:
                query = self.queryQueue[r].popitem(last=False)[1]
                return query.convertToDict()
            except KeyError:
                print "KeyError ", r
                pass
            
        print "return None"
        return None
    
    
    def newQueriesInQueue(self):
        """ requests if a new query exists on the server """
        for r in sorted(self.queryQueue.keys(), reverse=True):            
            if self.queryQueue[r].keys():
                return True
            
        return False
                
    
    def pushQuery(self, queryDict):
        """ pushes a new query in the queue """
        queryTpl = QueryTuple(**queryDict)
        
        if not queryTpl.priority in self.queryQueue.keys():
            self.queryQueue[queryTpl.priority] = OrderedDict()
                     
        self.queryQueue[queryTpl.priority][queryTpl.qid] = queryTpl
        
        print "inserted queryDict"
    
    
    def nextReply(self, qid=None):
        """ request the next query which has a reply 
        Args:
            qid -- if None, the next replay on the list will be served
        """
        if qid is None:                
            for p in sorted(self.replyQueue.keys(), reverse=True):
                try:
                    query = self.replyQueue[p].popitem(last=False)[1]
                    return query.convertToDict()
                except KeyError:
                    pass
                
            return None
        else:
            # first remove this qid from the reply queue then serve it
            p = self.replyList[qid].priority
            if qid in self.replyQueue[p].keys():
                del self.replyQueue[p][qid]
                
            return self.replyList[qid].convertToDict()
        
    
    def pushReply(self, replyDict):
        """ pushes the reply to a query into the queue """
        replyTpl = ReplyTuple(**replyDict)
        
        if not replyTpl.priority in self.replyQueue.keys():
            self.replyQueue[replyTpl.priority] = OrderedDict()
                    
        self.replyQueue[replyTpl.priority][replyTpl.qid] = replyTpl
        self.replyList[replyTpl.qid] = replyTpl
        
    
    
    def newRepliesInQueue(self):
        """ requests if a new reply exists on the server """
        for r in sorted(self.replyQueue.keys(), reverse=True):            
            if self.replyQueue[r].keys():
                return True
            
        return False
        
        
        
    def pushTestData(self, data):
        print data
        
        
class ComServerFDVT(ComServerBase):
    def __init__(self):
        super(ComServerFDVT, self).__init__()
        # __serialized__ FDVT
        self.baseFDVT = None
        
    def pushBaseLabelTree(self, replyDict):
        self.baseFDVT = replyDict
        print "received base label tree"
        
    def requestBaseLabelTree(self):
        return self.baseFDVT
        
        
        
if __name__ == "__main__":    
    s = zerorpc.Server(ComServerFDVT())
    s.bind("tcp://0.0.0.0:4242")
    s.run()