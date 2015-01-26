import json
import copy
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
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        s = json.dumps(self.frameList, sort_keys=True,indent=4, separators=(',', ': '))
        with open(filename, 'w') as f:
            f.write(s)

        self.hasChanged = False
        
    def saveToTmpFile(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

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

    def behaviourMatch(self, bhvrName, bhvrList, exactMatch=True):
        if exactMatch:
            if bhvrName in bhvrList:
                return [bhvrName]
            else:
                return []
        else:
            res = []
            for bhvr in bhvrList:
                if bhvrName in bhvr:
                    res += [bhvr]

            return res



    def filterFrameList(self, filterTuple, frameRange=None, exactMatch=True): #vialNo=None, behaviourName=None, annotator=None):
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

            frameRange (list of int):
                                frames in which the filterTuple is searched for
                                    
        Returns:
            new annotator object satisfying the filter criteria
        """
        
        vialNo = filterTuple.vials
        behaviourName = filterTuple.behaviours
        annotator = filterTuple.annotators
        
        if vialNo is None\
        or vialNo == [None]:
            vials = range(len(self.frameList[0]))
        elif type(vialNo) == int:
            vials = [vialNo]
        else:
            # asuming vialNo to be a list
            vials = vialNo

        if frameRange is None:
            frameRange = range(len(self.frameList))
            
        filteredList = []
        for frameNo in frameRange:
            behaviourPresent = False
            newVials = []
            
            for vIdx, vial in enumerate(vials):
                v = self.frameList[frameNo][vIdx]
                
                vNew = dict()
                
                if "behaviour" in v:
                    bNew = dict()
                    
                    if behaviourName == None:
                        bhvrList = v["behaviour"].keys()
                    else:
                        bhvrList = behaviourName
                    
                    for bhvrName in bhvrList:
                        matchList = self.behaviourMatch(bhvrName, v["behaviour"].keys(),
                                               exactMatch=exactMatch)

                        for bhvrMatch in matchList:
                        # if bhvrName in v["behaviour"]:
                            bhvr = v["behaviour"][bhvrMatch]
                            an = dict()
                            
                            if annotator is None:
                                anList = bhvr.keys()
                            else:
                                anList = annotator
                                
                            for anName in anList:
                                if anName in bhvr:
                                    an[anName] = bhvr[anName]
                            
                            if an:
                                bNew[bhvrMatch] = an
                                
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
        # self.children += [out]
        
        return out

    def addAnnotation(self, vial, frames, annotator,behaviour, metadata=1.0):
        """
        frames list of ints
        """
        # if vial == None:
        # just use first index
        vial = 0
            
        if isinstance(metadata, (int, long, float, complex)):
            tmpVal = metadata     
            metadata = dict()
            for frame in frames:
                metadata[frame] = tmpVal
        
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
                                                                    metadata[frame]
        
        #~ for child in self.children:
            #~ child.addAnnotation(vial, frames, behaviour, annotator, 
                                                                    #~ confidence)
                                                                    
    def removeAnnotation(self, vial, frames, annotator, behaviour):
        """
        frames list of ints
        """
        # if vial == None:
        # just use first index
        vial = 0
            
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

    def renameAnnotation(self, vial, frames, annotatorOld, behaviourOld,
                         annotatorNew, behaviourNew):
        # if vial is None:
        # just use first index
        vial = 0

        self.hasChanged = True
        if len(self.frameList) < max(frames):
            raise ValueError("Trying to add annotation to frame that" +
                             " exceeds length of existing annotation")

        for frame in frames:
            if self.frameList[frame][vial] is None:
                self.frameList[frame][vial] = dict()

            if not ("behaviour" in self.frameList[frame][vial]):
                self.frameList[frame][vial]["behaviour"] = dict()

            if not (behaviourNew in self.frameList[frame][vial]["behaviour"]):
                a = dict()
                self.frameList[frame][vial]["behaviour"][behaviourNew] = a

            print frame
            print self.frameList[frame][vial]
            self.frameList[frame][vial]["behaviour"][behaviourNew][annotatorNew] = \
                copy.copy(self.frameList[frame][vial]["behaviour"][behaviourOld][annotatorOld])

        self.removeAnnotation(vial, frames, annotatorOld, behaviourOld)

    def findConsequtiveAnnotationFrames(self, filterTuple, frameIdx,
                                        exactMatch=True, direction='both'):
        """
        direction (string):
                direction in which the annotation is traced.
                Possible values:
                                'both'
                                'right'
                                'left'

        """
        endFrame = frameIdx + 1
        if direction == "both" or direction == "right":
            while endFrame < len(self.frameList):
                match = self.filterFrameList(filterTuple,
                                             [endFrame],
                                             exactMatch).frameList
                if match == [[None]]:
                    break

                endFrame += 1

        startFrame = frameIdx - 1
        if direction == "both" or direction == "left":
            while startFrame >= 0:
                match = self.filterFrameList(filterTuple,
                                             [startFrame],
                                             exactMatch).frameList
                if match == [[None]]:
                    break

                startFrame -= 1

        startFrame += 1

        return range(startFrame, endFrame)

    def editMetadata(self, vials, frame, annotator, behaviour,
                     metaKey, newMetaValue):
        if vials is None:
            # just use first index
            vials = [0]

        for vial in vials:
            self.frameList[frame][vial]["behaviour"][behaviour]\
                            [annotator][metaKey] = newMetaValue


def getExactBehavioursFromFrameAnno(a):
    return sorted(a['behaviour'].keys())

            
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
    for bk in sorted(a):
        if bk != 'name':
            for bnk in sorted(a[bk]):
                for ak in sorted(a[bk][bnk]):
                    if type(a[bk][bnk][ak]) == int:
                        if prop == "confidence":
                            out += [a[bk][bnk][ak]]
                    elif prop in a[bk][bnk][ak].keys():
                        out += [a[bk][bnk][ak][prop]]
                        
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
