import json
import copy
import os
from collections import namedtuple
import numpy as np

AnnotationFilter = \
        namedtuple("AnnotationFilter", ["vials", "annotators", "behaviours"])

class Annotation():
    
    def __init__(self, frameNo=0, vialNames=['','','',''], empty=False):

        if empty:
            self.dataFrame = None
        else:
            self.dataFrame = pd.DataFrame(data=[[frameNo,
                                                 'automatic placeholder',
                                                 'video length',
                                                 None, None, None, None,
                                                 None]],
                                          columns=['frame', 'annotator',
                                                   'label',
                                                      'boundingbox x1',
                                                      'boundingbox y1',
                                                      'boundingbox x2',
                                                      'boundingbox y2',
                                                      'confidence'])


            self.dataFrame.set_index(['frame', 'annotator', 'label'],
                                inplace=True)
            self.dataFrame.sortlevel(inplace=True)

        # self.annotators = []
        # self.behaviours = []
        # self.children = []
        self.hasChanged = True


    def setDataframe(self, df):
        self.hasChanged = True
        self.dataFrame = df

    def getPureDataframe(self):
        return self.dataFrame.drop(self.dataFrame.index[-1])
            
    def setFrameList(self, frameList):
        """
        Sets frameList and updates internal lists of annotators and behaviours
        """
        self.hasChanged = True
        self.dataFrame = convertFrameListToDataframe(frameList)
            
    def getFrame(self, frameNo):
        # return filterDataframe(self.dataFrame, frames=[frameNo])
        # out = Annotation(frameNo=self.getLength())
        try:
            out = self.dataFrame.xs(frameNo, drop_level=False)#.reset_index()
            # out.set_index(['frame', 'annotator', 'label'],
            #             inplace=True)
            if out.empty:
                out = None
        except KeyError:
            out = None

        return out

    def getLength(self):
        return self.dataFrame.iloc[-1].name[0]

    def setLength(self, length):
        self.dataFrame.iloc[-1].name[0] = length

    def saveToFile(self, filename):
        if not os.path.exists(os.path.realpath(os.path.dirname(filename))):
            os.makedirs(os.path.realpath(os.path.dirname(filename)))

        saveAnnotation(self.dataFrame, filename)
        self.hasChanged = False
        
    def saveToTmpFile(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        saveAnnotation(self.dataFrame, filename)
        
    def loadFromFile(self, filename):
        self.dataFrame = loadAnnotation(filename)
        self.hasChanged = False
    
    def getFramesWithBehaviour(self, behaviourName):
        """
        Returns index of all frames that were labelled with
        the string *behaviourName*
        """
        
        return filterDataframe(self.dataFrame, label=behaviourName)

    def behaviourMatch(self, bhvrName, bhvrList, exactMatch=True):
        1/0
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
                        exactMatch=True,
                        update_behaviour_indeces=True):
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
        try:
            out = Annotation(empty=True)
            df = filterDataframe(self.dataFrame,
                                   frames=frameRange,
                                   annotator=[filterTuple.annotators[0],
                                              "automatic placeholder"],
                                   label=[filterTuple.behaviours[0],
                                          'video length'],
                                   exact_match=exactMatch,
                                   update_behaviour_indeces=update_behaviour_indeces)
            out.setDataframe(df)
        except ValueError:
            out = Annotation(frameNo=self.getLength())
        except KeyError:
            out = Annotation(frameNo=self.getLength())
        except TypeError:
            out = Annotation(frameNo=self.getLength())

        return out

    def filterFrameListMultiple(self, filterTuples, frameRange=None,
                        exactMatch=True):

        try:
            out = Annotation(frameNo=self.getLength(), empty=True)
            df = filterDataframe(self.dataFrame,
                               frames=frameRange,
                               annotator=[ft.annotators[0]
                                          for ft in filterTuples] +
                                             ["automatic placeholder"],
                               label=[ft.behaviours[0] for ft in filterTuples] +
                                     ['video length'],
                               exact_match=exactMatch)
            out.setDataframe(df)
        except ValueError:
            out = Annotation(frameNo=self.getLength())
        except KeyError:
            out = Annotation(frameNo=self.getLength())

        return out

    def mergeFrameLists(self, dfs):
        totalLength = 0
        for df in dfs:
            totalLength += df.iloc[-1].name[0]

        out = concatenateDataframes(dfs)
        out = changeLength(out, totalLength)

        return out


    def filterFrameLists(self, filterTuples, frameRange=None, exactMatch=True):
        try:
            out = filterDataframe(self.dataFrame,
                               frames=frameRange,
                               annotator=[ft.annotators[0]
                                          for ft in filterTuples] +
                                             ["automatic placeholder"],
                               label=[ft.behaviours[0] for ft in filterTuples] +
                                             ["automatic placeholder"],
                               exact_match=exactMatch)
        except ValueError:
            out = Annotation(frameNo=self.getLength())
        except KeyError:
            out = Annotation(frameNo=self.getLength())

        return out

    def filterFrameListBool(self, filterTuples, frameRange=None, exactMatch=True): #vialNo=None, behaviourName=None, annotator=None):
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
        try:
            out = filterFrameListBool(self.dataFrame,
                               frames=frameRange,
                               annotator=[ft.annotators[0]
                                          for ft in filterTuples] +
                                             ["automatic placeholder"],
                               label=[ft.behaviours[0] for ft in filterTuples] +
                                             ["video length"],
                               exact_match=exactMatch)
            return out[:-1]

        except ValueError:
            out = Annotation(frameNo=self.getLength())
        except KeyError:
            out = Annotation(frameNo=self.getLength())

        return out

    def addAnnotation(self, vial, frames, annotator, behaviour, metadata=None):
        """
        frames list of ints
        """
        self.dataFrame = addAnnotation(self.dataFrame,
                                       frames=frames,
                                       annotator=annotator,
                                       label=behaviour,
                                       metadata=metadata)
                                                                    
    def removeAnnotation(self, vial, frames, annotator, behaviour):
        """
        frames list of ints
        """
        self.dataFrame = removeAnnotation(self.dataFrame,
                                          frames=frames,
                                          annotator=annotator,
                                          label=behaviour)

    def renameAnnotation(self, vial, frames, annotatorOld, behaviourOld,
                         annotatorNew, behaviourNew):
        renameAnnotation(self.dataFrame,
                         frames=frames,
                         annotatorOld=annotatorOld,
                         annotatorNew=annotatorNew,
                         labelOld=behaviourOld,
                         labelNew=behaviourNew)

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
        return findConsequtiveAnnotationFrames(
                                        self.dataFrame,
                                        annotator=filterTuple.annotators[0],
                                        label=filterTuple.behaviours[0],
                                        frameIdx=frameIdx,
                                        exactMatch=exactMatch,
                                        direction=direction)


    def editMetadata(self, vials, frame, annotator, behaviour,
                     metaKey, newMetaValue):
        self.dataFrame = editMetadata(self.dataFrame,
                                      frames=frame,
                                      annotator=annotator,
                                      label=behaviour,
                                      metaKey=metaKey,
                                      newMetaValue=newMetaValue)

    def getPropertyFromFrameAnno(self, metaKey):
        return getPropertyFromFrameAnno(self.dataFrame[:-1], metaKey)

    def extractAllFilterTuples(self, frameRange=None):
        """
        Returns all annotation filters that can be applied to the annotation
        """
        return extractAllFilterTuples(self.dataFrame,
                                      frames=frameRange)

    def getExactBehaviours(self):
        labels = getExactBehavioursFromFrameAnno(self.dataFrame)

        out = set(labels) - {'video length'}

        return list(out)

    def getAnnotatedFrames(self):
        return getFramesFromFrameAnno(self.dataFrame)[:-1]


    def countAnnotationsPerFrame(self):
        try:
            cnt = countAnnotationsPerFrame(self.dataFrame)[:-1]
        except ValueError:
            cnt = []

        return cnt


# pandas functions


import itertools
import pandas as pd



def saveAnnotation(df, filename):
    df.to_csv(filename)


def loadAnnotation(filename):
    df = pd.DataFrame.from_csv(filename, parse_dates=False)
    df = df.reset_index()
    df.set_index(['frame', 'annotator', 'label'],
                        inplace=True)
    df.sortlevel(inplace=True)

    return df


def alignVideoLengthToRest(root_folder, pos_folder, anno_folder,
                                   video_extension='mp4'):
    import pyTools.system.videoExplorer as VE
    import numpy as np
    import yaml

    vE = VE.videoExplorer()
    anno = Annotation()

    for root, dirs, files in sorted(os.walk(root_folder)):
        for filename in sorted(files):
            if filename.endswith(video_extension):
                anno_filename = filename[:-len(video_extension)] + 'csv'
                pos_filename = filename[:-len(video_extension)] + 'pos.npy'

                af = os.path.join(os.path.dirname(root),
                                  anno_folder,
                                  anno_filename)

                pf = os.path.join(os.path.dirname(root),
                                  pos_folder,
                                  pos_filename)

                videoLength = vE.retrieveVideoLength(os.path.join(root,
                                                                  filename))


                try:
                    pos = np.load(pf)
                    posLength = len(pos)
                    if posLength != (videoLength):
                        newPos = pos[:videoLength, :]
                        np.save(pf, newPos)
                except IOError:
                    print "No posfile for {}".format(pf)
                    continue


                try:
                    anno.loadFromFile(af)

                    annoLength = anno.getLength()

                    if annoLength != videoLength:
                        print "anno fuck:\nfile: {}\nvL: {}\naL: {}".format(filename,
                                                                videoLength,
                                                                annoLength)

                        anno.removeAnnotation(vial=None,
                                              frames=annoLength,
                                              annotator='automatic placeholder',
                                              behaviour='video length')
                        anno.addAnnotation(vial=None,
                                           frames=[videoLength],
                                           annotator='automatic placeholder',
                                           behaviour='video length')
                        anno.saveToFile(af)

                except IOError:
                    continue


def findInteruptions(root_folder, pos_folder, anno_folder,
                                   video_extension='mp4'):
    import pyTools.system.videoExplorer as VE
    import numpy as np
    import yaml

    vE = VE.videoExplorer()
    anno = Annotation()

    unequalFiles = {}

    day = 1
    month = 2

    minute = 0
    vial = 0

    def incrementTime(day, month, minute, vial):
        vial += 1

        if vial > 3:
            vial = 0

            minute += 1
            if minute > 59:
                minute = 0
                day += 1

                if month == 2 and day > 28:
                    day = 0
                    month = 3
                if month == 3 and day > 31:
                    day = 0
                    month = 4

        return day, month, minute, vial


    for root, dirs, files in sorted(os.walk(root_folder)):
        for filename in sorted(files):
            if not filename.endswith(video_extension):
                continue

            bn = os.path.basename(filename)

            date = bn.split('.')[0]
            cur_day = int(date.split('-')[2])
            cur_month = int(date.split('-')[1])

            time = bn.split('.')[1]
            cur_minute = int(time.split('-')[1])

            cur_vial = int(bn.split('.')[2][1])

            printed = False
            cnt = 0
            while day != cur_day \
            or month != cur_month \
            or minute != cur_minute \
            or vial != cur_vial:
                if not printed:
                    printed = True

                # print day, month, minute, vial
                cnt += 1
                day, month, minute, vial = incrementTime(day, month, minute, vial)

            if printed:
                print filename, 'and next', cnt / 4, 'minutes'

            day, month, minute, vial = incrementTime(day, month, minute, vial)






def findOverlongVideos(root_folder, pos_folder, anno_folder,
                                   video_extension='mp4'):
    import pyTools.system.videoExplorer as VE
    import numpy as np
    import yaml

    vE = VE.videoExplorer()
    anno = Annotation()

    unequalFiles = {}

    for root, dirs, files in sorted(os.walk(root_folder)):
        for filename in sorted(files):
            if filename.endswith(video_extension):
                anno_filename = filename[:-len(video_extension)] + 'csv'
                pos_filename = filename[:-len(video_extension)] + 'pos.npy'

                af = os.path.join(os.path.dirname(root),
                                  anno_folder,
                                  anno_filename)

                pf = os.path.join(os.path.dirname(root),
                                  pos_folder,
                                  pos_filename)

                videoLength = vE.retrieveVideoLength(os.path.join(root,
                                                                  filename))

                try:
                    posLength = len(np.load(pf))
                except IOError:
                    print "No posfile for {}".format(pf)
                    # continue
                if videoLength > 1800:

                    if posLength != (videoLength):
                        print "pos fuck:\nfile: {}\nvL: {}\npL: {}".format(filename,
                                                                videoLength,
                                                                posLength)

                    try:
                        anno.loadFromFile(af)
                    except IOError:
                        continue

                    annoLength = anno.getLength()

                    if annoLength != videoLength:
                        print "anno fuck:\nfile: {}\nvL: {}".format(filename,
                                                                videoLength)


                    unequalFiles[filename] = [videoLength]#, posLength, annoLength]

    yamlStr = yaml.dump(unequalFiles, default_flow_style=False,
                        encoding=('utf-8'))



    with open('/Users/peter/Desktop/files.json', 'w') as f:
        f.writelines(yamlStr)


def checkVideoLenghtsInAnnotations(root_folder, pos_folder, anno_folder,
                                   video_extension='mp4'):
    import pyTools.system.videoExplorer as VE
    import numpy as np
    import yaml

    vE = VE.videoExplorer()
    anno = Annotation()

    unequalFiles = {}

    for root, dirs, files in sorted(os.walk(root_folder)):
        for filename in sorted(files):
            if filename.endswith(video_extension):
                anno_filename = filename[:-len(video_extension)] + 'csv'
                pos_filename = filename[:-len(video_extension)] + 'pos.npy'

                af = os.path.join(os.path.dirname(root),
                                  anno_folder,
                                  anno_filename)

                pf = os.path.join(os.path.dirname(root),
                                  pos_folder,
                                  pos_filename)

                videoLength = vE.retrieveVideoLength(os.path.join(root,
                                                                  filename))

                try:
                    posLength = len(np.load(pf))
                except IOError:
                    print "No posfile for {}".format(pf)
                    continue

                if posLength != (videoLength):
                    print "pos fuck:\nfile: {}\nvL: {}\npL: {}".format(filename,
                                                            videoLength,
                                                            posLength)
                else:
                    print "pos good:\nfile: {}\nvL: {}\npL: {}".format(filename,
                                                            videoLength,
                                                            posLength)

                try:
                    anno.loadFromFile(af)
                except IOError:
                    continue

                annoLength = anno.getLength()

                if annoLength != videoLength:
                    print "anno fuck:\nfile: {}\nvL: {}\naL: {}".format(filename,
                                                            videoLength,
                                                            annoLength)

                    unequalFiles[filename] = [videoLength, posLength, annoLength]

    yamlStr = yaml.dump(unequalFiles, default_flow_style=False,
                        encoding=('utf-8'))



    with open('~/Desktop/files.json', 'w') as f:
        f.writelines(yamlStr)




def copyToNewFolder(root_folder, dst_root, dst_bhvr):
    import shutil
    for root, dirs, files in os.walk(root_folder):
        for filename in files:
            if filename.endswith('.csv'):
                day = ''.join(filename.split('.')[0].split('-'))
                hour = filename.split('.')[1].split('-')[0]

                dst_folder = os.path.join(dst_root,
                                          day,
                                          hour,
                                          dst_bhvr)

                if not os.path.exists(dst_folder):
                    os.makedirs(dst_folder)

                print 'copy {} to {}'.format(os.path.join(root,
                                             filename),
                                            os.path.join(dst_folder,
                                                         filename))

                shutil.copyfile(os.path.join(root,
                                             filename),
                                os.path.join(dst_folder,
                                             filename))




def convertProjectFolder(folder):
    for root, dirs, files in os.walk(folder):
        for filename in files:
            if filename.endswith('.bhvr'):
                with open(os.path.join(root, filename), 'r') as f:
                    frameList = json.load(f)

                df = convertFrameListToDataframe(frameList)
                anno = Annotation(empty=True)
                anno.setDataframe(df)

                outFilename = os.path.join(root, filename[:-4] + 'csv')
                anno.saveToFile(outFilename)




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
    dataList += [[len(frameList), 'automatic placeholder', 'video length',
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
    return indexer, frames

def generateAnnotatorIndexer(df, annotator, indexer=None):
    if type(annotator) == str:
        annotator = [annotator]

    if indexer is None:
        indexer = [slice(None)]*len(df.index.names)

    indexer[df.index.names.index('annotator')] = annotator
    return indexer, annotator

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

    return indexer, filt

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
                    exact_match=True, update_behaviour_indeces=True):
    indexer = [slice(None)]*len(df.index.names)

    idx_lvls = list(df.index.levels)

    if frames is not None:
        indexer, frames = generateFramesIndexer(df, frames, indexer=indexer)
        if update_behaviour_indeces:
            idx_lvls[0] = frames

    if annotator is not None:
        indexer, annotator = generateAnnotatorIndexer(df, annotator,
                                                      indexer=indexer)

        if update_behaviour_indeces:
            idx_lvls[1] = annotator

    if label is not None:
        indexer, labels = generateLabelIndexer(df, label, exact_match,
                                               indexer=indexer)

        if update_behaviour_indeces:
            idx_lvls[2] = labels

    out = df.loc[tuple(indexer),:]

    if update_behaviour_indeces:
        # out.index.set_levels(idx_lvls, inplace=True)
        out.reset_index(inplace=True)
        out.set_index(['frame', 'annotator', 'label'],
                                inplace=True)
        out.sortlevel(inplace=True)


    return out


def filterFrameListBool(df, frames=None, annotator=None, label=None,
                        exact_match=True, update_behaviour_indeces=False):

    df = filterDataframe(df, frames=frames, annotator=annotator, label=label,
                         exact_match=exact_match,
                         update_behaviour_indeces=update_behaviour_indeces)

    cnt = countAnnotationsPerFrame(df).astype(np.bool)

    return cnt




def concatenateDataframes(dfs):
    out = pd.concat([df[:-1] for df in dfs])
    return out.append(dfs[0][-1:])#.reset_index(drop=True)

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
                                  for f, x in sorted(metadata.items())
                                  if f in frames])


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


def getPropertyFromFrameAnno(df, metaKey):
    if metaKey == 'confidence':
        return np.asarray(df['confidence'], dtype=np.float)
    elif metaKey == 'boundingBox':
        return np.asarray(df[['boundingbox x1', "boundingbox y1",
                             'boundingbox x2', "boundingbox y2"]], dtype=np.float)


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
            if direction == 'both':
                return rng
            elif direction == 'right':
                return rng[rng >= frameIdx]
            else:
                return rng[rng <= frameIdx]

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
    idxLst = df.index.tolist()
    if idxLst == []:
        raise ValueError("Dataframe is empty")

    idc = zip(*idxLst)[0]
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

def changeLength(df, length):
    idx = np.asarray(df.index.levels[0])
    idx[-1] = length
    df.set_index(df.index.set_levels(idx, level=0))

    return df

def insertFrameArray(fdv, day, hour, minute, frames):
    # super(FrameDataVisualizationTreeBehaviour, self).insertFrameArray(day, hour, minute, frames)

    fdv.verifyStructureExists(day, hour, minute)

    for i, f in enumerate(frames):
        fdv.addSample(day, hour, minute, i, f)

    fdv.addFrameArrayToStack(day, hour, minute, frames.T)
    fdv.addedNewData = True


def importDataframe(df, fdv, filterTuples, fps=30):
    data = createFDVTInsertionArray(df, filterTuples)

    fdv.resetAllSamples()

    for ft in filterTuples:
        fdv.addNewClass(ft)

    i = 0

    day = 0
    hour = 0
    minute = 0

    for k in range(fps * 60, len(data), fps * 60):
        print k, day, hour, minute
        frameSlc = slice(i, k)
#         data = self.convertFrameListToDatum(annotation, frameSlc,
#                                             self.meta['filtList'])
        insertFrameArray(fdv, day, hour, minute, data[i:k,:])
        day, hour, minute = fdv.incrementTime(day, hour, minute)
        i = k



def getExactBehavioursFromFrameAnno(df):
    return df.index.levels[2]

def getFramesFromFrameAnno(df):
    return df.index.levels[0]

def empty_multiindex(names):
    """
    Creates empty MultiIndex from a list of level names.
    taken from http://stackoverflow.com/q/28289440/2156909
    """
    return pd.MultiIndex.from_tuples(tuples=[(None,) * len(names)], names=names)


# end pandas functions




# def getExactBehavioursFromFrameAnno(a):
#     return sorted(a['behaviour'].keys())

            
# def getPropertyFromFrameAnno(a, prop):
#     """
#     Returns the requested property from a filtered frame annotation.
#
#     If the filtered frame has multiple entries with the same property,
#     all of them are returned.
#
#     Args:
#         a (frame from annotation.frameList)
#
#         prop (String)
#
#     Returns:
#         List containing values of the properties
#     """
#     out = []
#     for bk in sorted(a):
#         if bk != 'name':
#             for bnk in sorted(a[bk]):
#                 for ak in sorted(a[bk][bnk]):
#                     if type(a[bk][bnk][ak]) == int:
#                         if prop == "confidence":
#                             out += [a[bk][bnk][ak]]
#                     elif prop in a[bk][bnk][ak].keys():
#                         out += [a[bk][bnk][ak][prop]]
#
#     return out

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
