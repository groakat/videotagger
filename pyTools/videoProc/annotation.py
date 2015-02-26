import json
import copy
import os
from collections import namedtuple
import numpy as np

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



    def filterFrameList(self, filterTuple, frameRange=None,
                        exactMatch=True, recycleAnno=None): #vialNo=None, behaviourName=None, annotator=None):
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
        if frameRange is None:
            frameRange = range(len(self.frameList))

        if recycleAnno is None:
            out = Annotation(frameNo=len(frameRange), vialNames=[''])
        else:
            out = recycleAnno

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
                                    newFrameNo = frameNo - frameRange[0]
                                    out.addAnnotation(vIdx,
                                                      [newFrameNo],
                                                      anName,
                                                      bhvrMatch,
                                                      {newFrameNo: bhvr[anName]})


        return out

    def filterFrameListMultiple(self, filterTuples, frameRange=None,
                        exactMatch=True, recycleAnno=None):

        out = Annotation(frameNo=len(self.frameList), vialNames=[''])

        for filterTuple in filterTuples:
            out = self.filterFrameList(filterTuple, frameRange,
                                       exactMatch, out)

        return out

    def mergeFrameLists(self, frameLists):
        mergedList = []
        for frameList in frameLists:
            mergedList += zip(*frameList)

        return zip(*mergedList)


    def filterFrameLists(self, filterTuples, frameRange=None, exactMatch=True):
        frameLists = []
        for filterTuple in filterTuples:
            anno = self.filterFrameList(filterTuple, frameRange, exactMatch)
            frameLists += [anno.frameList]

        frameList = self.mergeFrameLists(frameLists)

        return frameList



    def filterFrameListBool(self, filterTuple, frameRange=None, exactMatch=True): #vialNo=None, behaviourName=None, annotator=None):
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

        filteredList = np.zeros((max(frameRange) + 1,), dtype=np.bool)
        for frameNo in frameRange:
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
                filteredList[frameNo] = True
            else:
                filteredList[frameNo] = False

        return filteredList

    def addAnnotation(self, vial, frames, annotator,behaviour, metadata=1.0):
        """
        frames list of ints
        """
        if vial == None:
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
        if vial == None:
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
        if vial is None:
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
                if not 'behaviour' in match[0][0]:
                    break

                endFrame += 1

        startFrame = frameIdx - 1
        if direction == "both" or direction == "left":
            while startFrame >= 0:
                match = self.filterFrameList(filterTuple,
                                             [startFrame],
                                             exactMatch).frameList
                if not 'behaviour' in match[0][0]:
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



    def extractAllFilterTuples(self, frameRange=None):
        """
        Returns all annotation filters that can be applied to the annotation
        """
        annotationFilterSet = set()

        if frameRange is None:
            frameRange = range(len(self.frameList))

        for frameNo in frameRange:
            for vIdx in range(len(self.frameList[0])):
                v = self.frameList[frameNo][vIdx]

                if "behaviour" in v:
                    bhvrList = v["behaviour"].keys()

                    for bhvrName in bhvrList:
                        bhvr = v["behaviour"][bhvrName]
                        anList = bhvr.keys()

                        for anName in anList:
                            annotationFilterSet |= {
                                    AnnotationFilter(vials=(vIdx,),
                                                     behaviours=(bhvrName,),
                                                     annotators=(anName,))}

        return annotationFilterSet

# pandas functions


import itertools
import pandas as pd

def convertFrameListToDataframe(frameList):
#     print frameList[:10]
    dataList = []
    for frame, bhvrDict in enumerate(frameList):
        try:
            for bhvr, annoDict in bhvrDict[0]['behaviour'].items():
                if annoDict is not None:
                    for annotator, meta in annoDict.items():
                        bb = meta['boundingBox']
                        conf = meta['confidence']
                        dataList += [[frame, annotator, bhvr,
                                      bb[0], bb[1], bb[2], bb[3], conf]]
        except KeyError:
            pass


    # add one empty row to mark the length of the video
    dataList += [[len(frameList), 'automcatic placeholder', 'video length',
                  None, None, None, None, None]]

    df = pd.DataFrame(data=dataList, columns=['frame', 'annotator', 'label',
                                              'boundingbox x1',
                                              'boundingbox y1',
                                              'boundingbox x2',
                                              'boundingbox y2',
                                              'confidence'])

    df.set_index(['frame', 'annotator', 'label'],
                        inplace=True)
    df.sortlevel(inplace=True)

    return df

def convertDataframeToFrameList(df):
    ar = np.asarray(df)


def getPropertiesFromDataframe(df, properties):
    """
    properties: single string or list of strings of the headers in the dataframe
    """
    return df[properties]

def generateFramesIndexer(df, frames, indexer=None):
    """
    frames: single int or list of ints
    """
    if type(frames) == int:
        frames = [frames]

    if indexer is None:
        indexer = [slice(None)]*len(df.index.names)

    indexer[df.index.names.index('frame')] = frames
    return indexer

def generateAnnotatorIndexer(df, annotator, indexer=None):
    if type(annotator) == str:
        annotator = [annotator]

    if indexer is None:
        indexer = [slice(None)]*len(df.index.names)

    indexer[df.index.names.index('annotator')] = annotator
    return indexer

def generateLabelIndexer(df, filterLabel, exact_match=True, indexer=None):
    if type(filterLabel) == str:
        filterLabel = [filterLabel]

    if exact_match:
        filt = filterLabel
    else:
        labels = df.index.levels[2]
        filt = []
        for l in labels:
            for fl in filterLabel:
                if l == fl \
                or l.startswith(fl + "_"):
                    filt += [l]

    if indexer is None:
        indexer = [slice(None)]*len(df.index.names)

    indexer[df.index.names.index('label')] = filt
    return indexer

def filterFramesFromDataframe(df, frames, indexer=None):
    """
    frames: single int or list of ints
    """
    if type(frames) == int:
        frames = [frames]

    indexer = generateFramesIndexer(df, frames, indexer)
    return df.loc[tuple(indexer),:]

def filterAnnotatorFromDataframe(df, annotator, indexer=None):
    if type(annotator) == str:
        annotator = [annotator]

    indexer = generateAnnotatorIndexer(df, annotator, indexer)
    return df.loc[tuple(indexer),:]

def filterLabelFromDataframe(df, filterLabel, exact_match=True, indexer=None):
    if type(filterLabel) == str:
        filterLabel = [filterLabel]

    indexer = generateLabelIndexer(df, filterLabel, exact_match=True,
                                   indexer=indexer)
    return df.loc[tuple(indexer),:]


def filterDataframe(df, frames=None, annotator=None, label=None,
                    exact_match=True):
    indexer = [slice(None)]*len(df.index.names)

    if frames is not None:
        indexer = generateFramesIndexer(df, frames, indexer=indexer)

    if annotator is not None:
        indexer = generateAnnotatorIndexer(df, annotator, indexer=indexer)

    if label is not None:
        indexer = generateLabelIndexer(df, label, exact_match, indexer=indexer)

    return df.loc[tuple(indexer),:]

def concatenateDataframes(dfs):
    out = pd.concat([df[:-1] for df in dfs])
    return out.append(dfs[0][-1:]).reset_index(drop=True)

def addAnnotation(df, frames, annotator, label, metadata=None):
    if metadata is None:
        tmpVal = metadata
        metadata = dict()
        for frame in frames:
            metadata[frame] = {u'boundingBox': [None, None, None, None],
                               u'confidence': 1}

    else:
        testMeta = metadata.values()[0].keys()
        if 'boundingBox' not in testMeta:
            for frame, meta in metadata.items():
                metadata[frame]['boundingBox'] = [None, None, None, None]

        if 'confidence' not in testMeta:
            for frame, meta in metadata.items():
                metadata[frame]['confidence'] = 1.0


    dataList = np.zeros((len(frames), 8), dtype=np.object)
    dataList[:, 0] = np.asarray(frames)
    dataList[:, 1:] = np.asarray([[annotator, label] + x['boundingBox'] +
                                    [x['confidence']]
                                      for x in metadata.values()])


    newDf = pd.DataFrame(data=dataList, columns=['frame', 'annotator', 'label',
                                                  'boundingbox x1',
                                                  'boundingbox y1',
                                                  'boundingbox x2',
                                                  'boundingbox y2',
                                                  'confidence'])

    newDf.set_index(['frame', 'annotator', 'label'],
                        inplace=True)

    df = pd.concat((df, newDf))
    df.sortlevel(inplace=True)

    return df

def removeAnnotation(df, frames, annotator, label):
    """
    frames: single int or list of ints

    slowish but the best I could find
    http://stackoverflow.com/a/12451149
    """
    selection = filterDataframe(df, frames, annotator, label)

    return df.drop(selection.index)


def renameAnnotation(df, frames, annotatorOld, labelOld, annotatorNew,
                     labelNew):
    """
    not the fastest
    http://stackoverflow.com/a/14110955/2156909
    """
    if type(frames) == int:
        frames = [frames]

    index = df.index
    indexlst = index.tolist()

    for i, item in enumerate(indexlst):
        if item[0] in frames        \
        and item[1] == annotatorOld \
        and item[2] == labelOld:
            indexlst[i] = (item[0], annotatorNew, labelNew)

    df.index = pd.MultiIndex.from_tuples(indexlst, names = index.names)



def copyAnnotation(df, frames, annotatorOld, labelOld, annotatorNew, labelNew):
    selectedDf = filterDataframe(df, frames, annotatorOld, labelOld)

    for idx in selectedDf.index.tolist():
        df.loc[(idx[0], annotatorNew, labelNew), :] = selectedDf.loc[idx, :]


def editMetadata(df, frames, annotator, label,
                 metaKey, newMetaValue):
    """
    takes far too long
    """
    if type(frames) == int:
        frames = [frames]

    selectedDf = filterDataframe(df, frames, annotator, label)


    if metaKey == 'confidence':
        df.loc[selectedDf.index, 'confidence'] = newMetaValue
    elif metaKey == 'boundingBox':
        df.loc[selectedDf.index, 'boundingbox x1'] = newMetaValue[0]
        df.loc[selectedDf.index, 'boundingbox y1'] = newMetaValue[1]
        df.loc[selectedDf.index, 'boundingbox x2'] = newMetaValue[2]
        df.loc[selectedDf.index, 'boundingbox y2'] = newMetaValue[3]

    return df


def getPropertyFromFrameAnno(a, metaKey):
    if metaKey == 'confidence':
        np.asarray(b['confidence'])
    elif metaKey == 'boundingBox':
        return np.asarray(b[['boundingbox x1', "boundingbox y1",
                             'boundingbox x2', "boundingbox y2"]])


def findConsequtiveAnnotationFrames(df, annotator, label, frameIdx,
                                        exactMatch=True, direction='both'):
    """
    using
    http://stackoverflow.com/a/7353335
    and
    http://stackoverflow.com/questions/7088625/what-is-the-most-efficient-way-to-check-if-a-value-exists-in-a-numpy-array
    """

    endFrame = frameIdx + 1
    prefilteredDF = filterDataframe(df, annotator=annotator,
                                    label=label, exact_match=exactMatch)

    # split frames into continuous ranges
    ar = np.sort(np.asarray(prefilteredDF.index.tolist())[:,0].astype(int))
    ranges = np.array_split(ar, np.where(np.diff(ar)!=1)[0]+1)

    # search in which range the frameIdx is locsted
    for rng in ranges:
        if frameIdx in rng:
            return rng

    return None

def extractAllFilterTuples(df, frames=None):
    if frames is not None:
        df = filterDataframe(frames=frames)

    idx = zip(*df.index.tolist())[1:]

    return list(itertools.product(set(idx[0]), set(idx[1])))

def splitDataframeIntoMinutes(df):
    indices = np.asarray(df.index.levels[0])
    lastS = 0
    lastE = 0

    lst = []

    for i in range(180):
        s = i * 1800
        e = s + 1800

        relIndices = indices[lastE:lastE + 1800]
        corrS = np.searchsorted(relIndices, s)
        if corrS >= len(relIndices):
            # corrS > e
            # happens if relIndices is len == 1
            continue

        if relIndices[corrS] > e:
            continue

        corrE = np.searchsorted(relIndices, e)
        if corrE == len(relIndices):
            corrE -= 1

        if relIndices[corrE] > e:
            corrE -= 1

        lst += [[s,e, df.loc[relIndices[corrS]: relIndices[corrE]]]]

        lastE += corrE

    return lst

def countAnnotationsPerFrame(df):
    idc = zip(*df.index.tolist())[0]
    cnt = np.bincount(idc)

    return cnt

def createFDVTInsertionArray(df, filterTuples):
    maxFrame = df.index.levels[0][-1]
    out = np.zeros((maxFrame, len(filterTuples)))

    for i, ft in enumerate(filterTuples):
        annotator = ft.annotators[0]
        label = ft.behaviours[0]

        tmpDF = filterDataframe(df, frames=None, annotator=annotator,
                                label=label, exact_match=False)

        cnt = countAnnotationsPerFrame(tmpDF)
        out[:len(cnt), i] = cnt

    return out






# end pandas functions




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
