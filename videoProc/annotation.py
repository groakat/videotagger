import json
import os
from collections import namedtuple


AnnotationFilter = \
        namedtuple("AnnotationFilter", ["vials", "annotators", "behaviours"])

class Annotation():
    
    def __init__(self, frameNo=0, vialNames=['','','','']):
        
        self.frameList = []
        self.annotators = []
        self.behaviours = []
        self.children = []
        self.hasChanged = True # will be a new one until
        
        for frame in range(frameNo):
            v = []
            for vial in range(len(vialNames)):
                d = dict()
                d["name"] = vialNames[vial]
                v += [d]
                
            self.frameList += [v]
            
        self.setFrameList(self.frameList)
            
    def setFrameList(self, frameList):
        """
        Sets frameList and updates internal lists of annotators and behaviours
        """
        self.hasChanged = True
        self.frameList = frameList
        annotators = set()
        behaviours = set()
        
        # TODO: also create list of annotators per behaviour and behaviours per annotator        
        for fN in range(len(frameList)):
            if frameList[fN] is None:
                continue
                
            for vN in [i for i in range(len(frameList[fN])) if frameList[fN][i] is not None]:
                if "behaviour" in frameList[fN][vN]:
                    bhvr = frameList[fN][vN]["behaviour"].keys()
                    behaviours = behaviours.union(bhvr)
                    for bhvrName in bhvr:
                        anno = frameList[fN][vN]["behaviour"][bhvrName].keys()
                        annotators = annotators.union(anno)
                        
        self.annotators = list(annotators)
        self.behaviours = list(behaviours)
            
    def getFrame(self, frameNo):
        return self.frameList[frameNo]
    
    def getVialAt(self, frameNo, vialNo):
        return self.frameList[frameNo][vialNo]
        
    def saveToFile(self, filename):
        f = open(filename, 'w')
        json.dump(self.frameList, f, sort_keys=True,indent=4, separators=(',', ': '))
        f.close()
        
    def loadFromFile(self, filename):
        f = open(filename, 'r')
        self.setFrameList(json.load(f))
        self.hasChanged = False
        f.close()
    
    def getFramesWithBehaviour(self, behaviourName, vialNo=None):
        """
        Returns index of all frames that were labelled with
        the string *behaviourName*
        """
        
        if vialNo is None:
            vials = range(len(self.frameList[0]))
        elif type(vialNo) == int:
            vials = [vialNo]
        else:
            # asuming vialNo to be a list
            vials = vialNo
            
        frames = []
        for frameNo in range(len(self.frameList)):
            behaviourPresent = False
            for vN in vials:
                v = self.frameList[frameNo][vN]
                if "behaviour" in v:
                    if behaviourName in v["behaviour"]:
                        behaviourPresent = True
                        
            if behaviourPresent:
                frames += [frameNo]
        
        return frames
    
    def filterFrameList(self, filterTuple): #vialNo=None, behaviourName=None, annotator=None):
        """
        Returns a new annotation object that contains only annotations that 
        satisfy all filter criteria.
        
        Args:
            vialNo (None, int or list of int):
                                defines the vials that will be filtered. Possible
                                values are
                                
                                None:
                                    do not filter any specific vial
                                int:
                                    search only in this single vial
                                list of int:
                                    search in all vials given in the list
            behaviourName (None or list of strings):
                                defines the behaviours that will be filtered.
                                Possible values are
                                
                                None:
                                    do not filter any specific behaviour
                                list of string:
                                    behaviours to filter
            annotator (None or list of strings):
                                defines the annotators that will be filtered.
                                Possible values are
                                
                                None:
                                    do not filter any specific annotator
                                list of strings:
                                    annotators to be filtered for
                                    
        Returns:
            new annotator object satisfying the filter criteria
        """
        
        vialNo = filterTuple.vials
        behaviourName = filterTuple.behaviours
        annotator = filterTuple.annotators
        
        if vialNo is None:
            vials = range(len(self.frameList[0]))
        elif type(vialNo) == int:
            vials = [vialNo]
        else:
            # asuming vialNo to be a list
            vials = vialNo
            
        filteredList = []
        for frameNo in range(len(self.frameList)):
            behaviourPresent = False
            newVials = []
            
            for vIdx in vials:
                v = self.frameList[frameNo][vIdx]
                
                vNew = dict()
                
                if "behaviour" in v:
                    bNew = dict()
                    
                    if behaviourName == None:
                        bhvrList = v["behaviour"].keys()
                    else:
                        bhvrList = behaviourName
                    
                    for bhvrName in bhvrList:                        
                        if bhvrName in v["behaviour"]:
                            bhvr = v["behaviour"][bhvrName]   
                            an = dict()
                            
                            if annotator is None:
                                anList = bhvr.keys()
                            else:
                                anList = annotator
                                
                            for anName in anList:
                                if anName in bhvr:
                                    an[anName] = bhvr[anName]
                            
                            if an:
                                bNew[bhvrName] = an
                                
                    if bNew:
                        if "name" in v:
                            vNew['name'] = v['name']
                            
                        vNew['behaviour'] = bNew
                        newVials += [vNew]
                        behaviourPresent = True
                    else:
                        newVials += [None]  
                else:
                    newVials += [None]                            
                        
            if behaviourPresent:
                filteredList += [newVials]
            else:
                filteredList += [[None for i in range(len(vials))]]
        
        out = Annotation()
        out.setFrameList(filteredList)
        self.children += [out]
        
        return out

    def addAnnotation(self, vial, frames, annotator,behaviour, confidence=1.0):
        """
        frames list of ints
        """
        self.hasChanged = True
        if len(self.frameList) < max(frames):
            raise ValueError("Trying to add annotation to frame that" +
                             " exceeds length of existing annotation")
        
        for frame in frames:
            if self.frameList[frame][vial] is None:
                self.frameList[frame][vial] = dict()
            
            if not ("behaviour" in self.frameList[frame][vial]):
                self.frameList[frame][vial]["behaviour"] = dict()
                
            if not (behaviour in self.frameList[frame][vial]["behaviour"]):
                a = dict()
                self.frameList[frame][vial]["behaviour"][behaviour] = a
                
            self.frameList[frame][vial]["behaviour"][behaviour][annotator] = \
                                                                    confidence
        
        #~ for child in self.children:
            #~ child.addAnnotation(vial, frames, behaviour, annotator, 
                                                                    #~ confidence)
                                                                    
    def removeAnnotation(self, vial, frames, annotator, behaviour):
        """
        frames list of ints
        """
        self.hasChanged = True
        if len(self.frameList) < max(frames):
            raise ValueError("Trying to remove annotation to frame that" +
                             " exceeds length of existing annotation")
        
        v = vial
        b = behaviour
        a = annotator
        
        for frame in frames:
            if "behaviour" in self.frameList[frame][vial]:
                if b in self.frameList[frame][v]["behaviour"]:
                    if a in self.frameList[frame][v]["behaviour"][b]:
                        del self.frameList[frame][v]["behaviour"][b][a]
                        if self.frameList[frame][v]["behaviour"][b] == {}:
                            del self.frameList[frame][v]["behaviour"][b]
        
        #~ for child in self.children:
            #~ child.removeAnnotation(v, frames, b, a)
            
def getPropertyFromFrameAnno(a, prop):
    """
    Returns the requested property from a filtered frame annotation.
    
    If the filtered frame has multiple entries with the same property,
    all of them are returned.
    
    Args:
        a (frame from annotation.frameList)
        
        prop (String)
        
    Returns:
        List containing values of the properties
    """
    out = []
    for bk in a[0]:
        if bk != 'name':
            for bnk in a[0][bk]:
                for ak in a[0][bk][bnk]:
                    if type(a[0][bk][bnk][ak]) == int:
                        if prop == "confidence":
                            out += [a[0][bk][bnk][ak]]
                    elif prop in a[0][bk][bnk][ak].keys():
                        out += [a[0][bk][bnk][ak][prop]]
                        
    return out

if __name__ == "__main__":
    vid = []

    for frame in range(2):
        v = []
        for vial in range(4):
            d = dict()
            if vial == 0:
                d["name"] = "Abeta +RU"
                b = dict()            
                b["falling"] = {"peter": 1.0}
                d["behaviour"] = b
            if vial == 1:
                d["name"] = "Abeta -RU"
                b = dict()            
                b["rest"] = {"peter": 1.0}
                d["behaviour"] = b
            if vial == 2:
                d["name"] = "dilp"
                b = dict()            
                b["feeding"] = {"peter": 0.5, "matt": 1.0}
                b["walking"] = {"peter": 0.5}
                d["behaviour"] = b
            if vial == 3:
                d["name"] = "wDah"
                b = dict()            
                b["walking"] = {"peter": 1.0}
                d["behaviour"] = b
            v += [d]
        vid += [v]
        
        a = Annotation()
        a.setFrameList(vid)
        a.addAnnotation(1, [0,1], "falling", "peter", 0.5)
        res = a.filterFrameList(vialNo=None, behaviourName=None, annotator=['peter'])
