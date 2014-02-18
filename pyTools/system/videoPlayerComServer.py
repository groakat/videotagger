import zerorpc
import numpy as np
import datetime
from collections import OrderedDict
from collections import namedtuple



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
    
    elif not isinstance(o, dict):    
        return hash(o)
    
    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)
    
    return hash(tuple(frozenset(sorted(new_o.items()))))


Query = namedtuple("Query", ['id', 'rank', "type", "query", "reply"])

class QueryTuple(Query):
    def __new__(cls, id, rank, type, query, reply):
        self = super(QueryTuple, cls).__new__(cls, id, rank, type, query, reply)
        self._hash = hash(self.id) * hash(self.rank) * hash(self.type) * \
                        make_hash(self.query) * make_hash(self.reply)
        return self
    
    def __hash__(self):
        return self._hash
    
    def convertToDict(self):
        return {'id': self.id, 'rank': self.rank, "type":self.type, 
                "query":self.query, "reply":self.reply}
        

class ComServer(object):
    
    def __init__(self):
        self.queryQueue = dict()
        self.replyQueue = dict()

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
                
    
    def pushQuery(self, queryDict):
        """ pushes a new query in the queue """
        queryTpl = QueryTuple(**queryDict)
        
        if not queryTpl.rank in self.queryQueue.keys():
            self.queryQueue[queryTpl.rank] = OrderedDict()
                     
        self.queryQueue[queryTpl.rank][queryTpl.id] = queryTpl
        
        print "inserted queryDict"
    
    def nextReply(self):
        """ request the next query which has a reply """
        for r in sorted(self.replyQueue.keys(), reverse=True):
            try:
                query = self.replyQueue[r].popitem(last=False)[1]
                return query.convertToDict()
            except KeyError:
                pass
            
        return None
    
    def pushReply(self, queryDict):
        """ pushes the reply to a query into the queue """
        queryTpl = QueryTuple(**queryDict)
        
        if not queryTpl.rank in self.replyQueue.keys():
            self.replyQueue[queryTpl.rank] = OrderedDict()
                    
        self.replyQueue[queryTpl.rank][queryTpl.id] = queryTpl
        
        
if __name__ == "__main__":    
    s = zerorpc.Server(ComServer())
    s.bind("tcp://0.0.0.0:4244")
    s.run()