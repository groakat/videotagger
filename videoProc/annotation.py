import json
import os

class Annotation():
    frameList = []
    annotators = []
    behaviours = []
    children = []
    
    def __init__(self, frameNo=0, vialNames=['','','','']):
        
        frameList = []
        
        for frame in range(frameNo):
            v = []
            for vial in range(len(vialNames)):
                d = dict()
                d["name"] = vialNames[vial]
                v += [d]
                
            frameList += [v]
            
        self.setFrameList(frameList)
            
    def setFrameList(self, frameList):
        """
        Sets frameList and updates internal lists of annotators and behaviours
        """
        self.frameList = frameList
        annotators = set()
        behaviours = set()
        
        # TODO: also create list of annotators per behaviour and behaviours per annotator        
        for fN in range(len(frameList)):
            if frameList[fN] is None:
                continue
                
            for vN in range(len(frameList[fN])):
                if "behaviour" in  frameList[fN][vN]:
                    bhvr = frameList[fN][vN]["behaviour"].keys()
                    behaviours = behaviours.union(bhvr)
                    for bhvrName in bhvr:
                        anno = frameList[fN][vN]["behaviour"][bhvrName].keys()
                        annotators = annotators.union(anno)
                        
        self.annotators = list(annotators)
        self.behaviours = list(behaviours)
            
    def getFrame(self, frameNo):
        return frameList[frameNo]
    
    def getVialAt(self, frameNo, vialNo):
        return frameList[frameNo][vialNo]
        
    def saveToFile(self, filename):
        f = open(filename, 'w')
        json.dump(self.frameList, f, sort_keys=True,indent=4, separators=(',', ': '))
        f.close()
        
    def loadFromFile(self, filename):
        f = open(filename, 'r')
        self.setFrameList(json.load(f))
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
    
    def filterFrameList(self,  vialNo=None, behaviourName=None, annotator=None):
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
                        
            if behaviourPresent:
                filteredList += [newVials]
            else:
                filteredList += [None]
        
        out = Annotation()
        out.setFrameList(filteredList)
        self.children += [out]
        
        return out

    def addAnnotation(self, vial, frames, behaviour, annotator, confidence=1.0):
        """
        frames list of ints
        """
        if len(self.frameList) < max(frames):
            raise ValueError("Trying to add annotation to frame that" +
                             " exceeds length of existing annotation")
        
        for frame in frames:
            if not (behaviour in self.frameList[frame][vial]["behaviour"]):
                a = dict()
                self.frameList[frame][vial]["behaviour"][behaviour] = a
                
            self.frameList[frame][vial]["behaviour"][behaviour][annotator] = \
                                                                    confidence
        
        for child in self.children:
            child.addAnnotation(vial, frames, behaviour, annotator, 
                                                                    confidence)
                                                                    
    def removeAnnotation(self, vial, frames, behaviour, annotator):
        """
        frames list of ints
        """
        if len(self.frameList) < max(frames):
            raise ValueError("Trying to remove annotation to frame that" +
                             " exceeds length of existing annotation")
        
        v = vial
        b = behaviour
        a = annotator
        
        for frame in frames:
            if b in self.frameList[frame][v]["behaviour"]:
                if a in self.frameList[frame][v]["behaviour"][b]:
                    del self.frameList[frame][v]["behaviour"][b][a]
                    if self.frameList[frame][v]["behaviour"][b] == {}:
                        del self.frameList[frame][v]["behaviour"][b]
        
        for child in self.children:
            child.removeAnnotation(v, frames, b, a)


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
