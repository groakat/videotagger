import json

class annotation():
    frameList = []
    
    def __init__(self, frameNo=1000, vialNames=['','','','']):
        self.frameList = []
        
        for frame in range(frameNo):
            v = []
            for vial in range(len(vialNames)):
                d = dict()
                d["name"] = vialNames[vial]
                v += [d]
                
            self.frameList += [v]
            
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
        self.frameList = json.load(f)
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
        Returns frameList with frames that were labelled with
        the string *behaviourName*, excluding all other behaviours
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
        
        return filteredList
