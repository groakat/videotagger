import math
from collections import namedtuple

def chunks(l, n):
    """ Yield successive n-sized chunks from l
        as described in:
        http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    if n != math.ceil(n):
        n = math.ceil(n)
    
    n = int(n)

    for i in range(0, len(l), n):
        yield l[i:i+n]

FramePosition = namedtuple('FramePosition', ['dicnry', 'key', 'idx'])

def generateRangeValuesFromKeys(start, end):
        """        
        It generates a range ranging over several files. I.e. 
        Generates a dict with ranges for each key. T
        Args:
            start (FramePosition)
            end (FramePosition)
        """        
        c = [start,end]
        if start.key != end.key:
            c.sort(key=lambda x: x.key)
        else:
            c.sort(key=lambda x: x.idx)
        s = c[0]
        e = c[1]
            
        
        rng = dict()
        isWithinRange = False
        for key in sorted(s.dicnry.keys()):
            rngS = None
            rngE = None
            
            if key == s.key:
               isWithinRange = True
               rngS = s.idx
            else:
                rngS = 0
               
            if key == e.key:
                isWithinRange = False
                rngE = e.idx
                rng[key] = range(rngS, rngE)
                return rng
            else:
                rngE = len(s.dicnry[key].frameList)
            
            if isWithinRange:
                rng[key] = range(rngS, rngE)
                
        return rng
        
if __name__ == "__main__":
    """ testing chunks function """
    import pprint
    pprint.pprint(list(chunks(range(10, 75), 10)))
    pprint.pprint(list(chunks(range(1,100), 100/3.0)))
    


