import numpy as np
import os
import warnings
import pyTools.misc.basic as bsc
import pyTools.videoProc.annotation as Annotation
import pyTools.videoTagger.dataLoader as DL

import pyTools.misc.config as cfg

def filename2Time(f):
    timestamp = f.split('/')[-1]
    day, timePart = timestamp.split('.')[:2]
    hour, minute, second = timePart.split('-')

    return day, hour, minute, second


def filename2TimeRunningIndeces(f):
    timestamp = f.split('/')[-1].split('.')[0]
    rawMinutes = timestamp.split('_')[-1]
    day, hour, minute, second = minutes2Time(int(rawMinutes))

    return day, hour, minute, second

def minutes2Time(rawMinutes):
    days = rawMinutes // (60 * 24)
    hours = rawMinutes // 60
    minutes = rawMinutes % 60
    second = 0
    return days, hours, minutes, second

def provideFileList(baseFolder, featFolder, vial, ending='.pos.npy'):
    fileList  = []
    posList = []
    print("scaning files...")
    for root,  dirs,  files in os.walk(baseFolder):
        # if os.path.split(root)[1] == featFolder:
        if root[-len(featFolder):] == featFolder:
            for f in files:
                if f.endswith(ending):
                    if int(f[-(len(ending) + 1)]) == vial:
                        fullPath = root + '/' + f
                        fileList.append(fullPath)

    fileList = sorted(fileList)
    print("scaning files done")
    return fileList


class FrameDataVisualizationTreeBase(object):

    def __init__(self):
        self.data = dict()          # tree of data
        self.hier = dict()          # summarized information
                                    # max, mean, sampleN
        self.meta = dict()          # classes, etc

        self.FDVT = {'data': self.data,
                     'hier': self.hier,
                     'meta': self.meta}

        self.meta['isCategoric'] = False
        self.meta['singleFileMode'] = True     # if True, only one file (key) is used
                                        # to save the entire annotation
        self.meta['totalNoFrames'] = 0
        self.addedNewData = True
        # self.ranges = dict()


    def resetAllSamples(self):
        self.data = dict()          # tree of data
        self.hier = dict()          # summarized information
                                    # max, mean, sampleN
        self.meta = dict()          # classes, etc

        self.FDVT = {'data': self.data,
                     'hier': self.hier,
                     'meta': self.meta}
        self.meta['totalNoFrames'] = 0
        self.addedNewData = True
        # self.ranges = dict()


    def save(self, filename):
        np.save(filename, np.asarray(self.FDVT))

    def load(self, filename):
        self.FDVT = np.load(filename).item()
        self.data = self.FDVT['data']
        self.hier = self.FDVT['hier']
        self.meta = self.FDVT['meta']

    def getStandardHierDatum(self):
        return {'max': -np.Inf,
                'mean': 0,
                'sampleN': 0}

    def getHierarchicalData(self, day, hour, minute):
        res = []
        try:
            res += [self.hier[day]['meta']]
        except KeyError:
            res += [self.getStandardHierDatum()]

        try:
            res += [self.hier[day][hour['meta']]]
        except KeyError:
            res += [self.getStandardHierDatum()]

        try:
            res += [self.hier[[day][hour][minute]['meta']]]
        except KeyError:
            res += [self.getStandardHierDatum()]

        return res

    def getValue(self, day, hour, minute, frame):
        return self.data[day][hour][minute][frame]

    def getValueFilename(self, filename, frame):
        return self.getValue(*filename2Time(filename)[:3], frame=frame)


    def generateRandomSequence(self, dayRng, hourRng, minuteRng, frameRng):
        for day in dayRng:
            for hour in hourRng:
                for minute in minuteRng:
                    minMax = np.random.rand(1)[0]
                    for frame in frameRng:
                        if np.random.rand(1)[0] > 1.9:
                            data = 0.999999
                        else:
                            data = np.random.rand(1)[0] * minMax
                        self.addSample(day, hour, minute, frame, data)

        self.addedNewData = True


    def verifyStructureExists(self, day, hour, minute):
        try:
            self.hier['meta']
        except KeyError:
            self.hier['meta'] = self.getStandardHierDatum()
            
        if day not in self.data.keys():
            self.data[day] = dict()
            self.hier[day] = dict()
            self.hier[day]['meta'] = self.getStandardHierDatum()
            
        if hour not in self.data[day].keys():
            self.data[day][hour] = dict()
            self.hier[day][hour] = dict()
            self.hier[day][hour]['meta'] = self.getStandardHierDatum()
            
        if minute not in self.data[day][hour].keys():
            self.data[day][hour][minute] = dict()
            self.hier[day][hour][minute] = dict()
            self.hier[day][hour][minute]['meta'] = self.getStandardHierDatum()

    def incrementMean(self, prevMean, data, n):
        return prevMean + (1.0/n) * (data - prevMean)


    def addSampleToStumpMean(self, stump, data, n=1):
        """

        :param key: (day) or (day, hour) or (day, hour, minute)
        :param data:
        :return:
        """
        if stump['meta']['sampleN'] + n == 0:
            stump['meta']['mean'] = 0
        else:
            stump['meta']['mean'] = self.incrementMean(stump['meta']['mean'],
                                                   data,
                                                   stump['meta']['sampleN'] +n)
        stump['meta']['sampleN'] += n


    def addSampleToMean(self, day, hour, minute, data, n=1):
        self.addSampleToStumpMean(self.hier[day][hour][minute], data, n)
        self.addSampleToStumpMean(self.hier[day][hour], data, n)
        self.addSampleToStumpMean(self.hier[day], data, n)
        self.addSampleToStumpMean(self.hier, data, n)


    def addSample(self, day, hour, minute, frame, data):
        self.verifyStructureExists(day, hour, minute)
        # using try, except because its much fast than looking up the keys
        try:
            self.replaceSample(day, hour, minute, frame, data)
        except KeyError:
            self.insertSample(day, hour, minute, frame, data)

        self.addedNewData = True

    def insertSample(self, day, hour, minute, frame, data):
        self.data[day][hour][minute][frame] = data
        self.updateMax(day, hour, minute, data)
        self.addSampleToMean(day, hour, minute, data)
        self.meta['totalNoFrames'] += 1
        self.addedNewData = True

    def removeSample(self, day, hour, minute, frame):
        oldData = self.getValue(day, hour, minute, frame)

        if oldData == self.hier[day][hour][minute]['meta']['max']:
            newMax = np.max([self.data[day][hour][minute][k] \
                        for k in self.data[day][hour][minute].keys()])
            self.updateMax(day, hour, minute, newMax)

        self.addSampleToMean(day, hour, minute, -oldData, -1)
        self.meta['totalNoFrames'] -= 1
        self.addedNewData = True


    def replaceSample(self, day, hour, minute, frame, data):
        # oldData = self.getValue(day, hour, minute, frame)
        # self.data[day][hour][minute][frame] = data
        #
        # if oldData == self.hier[day][hour][minute]['meta']['max']:
        #     newMax = np.max([self.data[day][hour][minute][k] \
        #                 for k in self.data[day][hour][minute].keys()])
        #     self.updateMax(day, hour, minute, newMax)
        # else:
        #     self.updateMax(day, hour, minute, data)
        self.removeSample(day, hour, minute, frame)
        self.insertSample(day, hour, minute, frame, data)
        self.addedNewData = True


    def updateMax(self, day, hour, minute, data):
        if self.hier[day][hour][minute]['meta']['max'] < data:
            self.hier[day][hour][minute]['meta']['max'] = data

            if self.hier[day][hour]['meta']['max'] < data:
                self.hier[day][hour]['meta']['max'] = data

                if  self.hier[day]['meta']['max'] < data:
                    self.hier[day]['meta']['max'] = data

                    if self.hier['meta']['max'] < data:
                        self.hier['meta']['max'] = data

    def generateConfidencePlotData(self, day, hour, minute, frame, frameResolution=1):
        self.plotData = dict()
        self.generatePlotDataDays(day, hour, minute, frame)
        self.generatePlotDataHours(day, hour, minute, frame)
        self.generatePlotDataMinutes(day, hour, minute, frame)
        self.generatePlotDataFrames(day, hour, minute, frame, frameResolution)


    def generatePlotDataDays(self, day, hour, minute, frame):
        self.plotData['days'] = dict()
        self.plotData['days']['data'] = []
        self.plotData['days']['weight'] = []
        self.plotData['days']['tick'] = []
        if self.data == dict():
            self.plotData['days']['data'] += [0]
            self.plotData['days']['weight'] += [0]
            self.plotData['days']['tick'] += [0]
            return

        for key in sorted(self.meta['rangeTemplate']['days']):
            if key in self.hier.keys():
                if key in ['meta']:
                    continue

                self.plotData['days']['data'] += [self.hier[key]['meta']['max']]
                self.plotData['days']['weight'] += [self.hier[key]['meta']['mean']]
                self.plotData['days']['tick'] += [key]
            else:
                self.plotData['days']['data'] += [0]
                self.plotData['days']['weight'] += [0]




    def generatePlotDataHours(self, day, hour, minute, frame):
        self.plotData['hours'] = dict()
        self.plotData['hours']['data'] = []
        self.plotData['hours']['weight'] = []
        self.plotData['hours']['tick'] = []
        if self.data == dict():
            self.plotData['hours']['data'] += [0]
            self.plotData['hours']['weight'] += [0]
            self.plotData['hours']['tick'] += [0]
            return

        try:
            keys = self.hier[day].keys()
        except KeyError:
            return

        for key in sorted(self.meta['rangeTemplate']['hours']):
            if key in keys:
                if key in ['meta']:
                    continue

                self.plotData['hours']['data'] += \
                                                [self.hier[day][key]['meta']['max']]
                self.plotData['hours']['weight'] += \
                                               [self.hier[day][key]['meta']['mean']]
                self.plotData['hours']['tick'] += [key]
            else:
                self.plotData['hours']['data'] += [0]
                self.plotData['hours']['weight'] += [0]


    def generatePlotDataMinutes(self, day, hour, minute, frame):
        self.plotData['minutes'] = dict()
        self.plotData['minutes']['data'] = []
        self.plotData['minutes']['weight'] = []
        self.plotData['minutes']['tick'] = []
        if self.data == dict():
            self.plotData['minutes']['data'] += [0]
            self.plotData['minutes']['weight'] += [0]
            self.plotData['minutes']['tick'] += [0]
            return

        try:
            keys = self.hier[day][hour].keys()
        except KeyError:
            return

        for key in sorted(self.meta['rangeTemplate']['hours']):
            if key in keys:
                if key in ['meta']:
                    continue

                self.plotData['minutes']['data'] += \
                                        [self.hier[day][hour][key]['meta']['max']]
                self.plotData['minutes']['weight'] += \
                                        [self.hier[day][hour][key]['meta']['mean']]
                self.plotData['minutes']['tick'] += [key]
            else:
                self.plotData['minutes']['data'] += [0]
                self.plotData['minutes']['weight'] += [0]



    def generatePlotDataFrames(self, day, hour, minute, frame,
                               frameResolution=1):
        self.plotData['frames'] = dict()
        self.plotData['frames']['data'] = []
        self.plotData['frames']['weight'] = []
        self.plotData['frames']['tick'] = []
        if self.data == dict():
            self.plotData['frames']['data'] += [0]
            self.plotData['frames']['weight'] += [0]
            self.plotData['frames']['tick'] += [0]
            return

        try:
            keys = self.hier[day][hour][minute].keys()
        except KeyError:
            return

        cnt = 0
        tmpVal = []
        tmpKeys = []
        for key in sorted(self.meta['rangeTemplate']['frames']):
            if key in keys:
                if key in ['meta']:
                    continue

                tmpVal += [self.data[day][hour][minute][key]]
                tmpKeys += [key]
            else:
                tmpVal += [0]

            cnt += 1

            if not (cnt < frameResolution):
                self.plotData['frames']['data'] += [max(tmpVal)]
                self.plotData['frames']['weight'] += [sum(tmpVal) / frameResolution]
                self.plotData['frames']['tick'] += [tmpKeys]
                cnt = 0
                tmpVal = []
                tmpKeys = []



        if cnt != 0:
            self.plotData['frames']['data'] += [max(tmpVal)]
            self.plotData['frames']['weight'] += [sum(tmpVal) / cnt]
            self.plotData['frames']['tick'] += [tmpKeys]


    def createFDVTTemplateFromHierarchy(self):
        """
        It is recommended to use `createFDVTTemplateFromVideoList`

        :param days:
        :param hours:
        :param minutes:
        :return:
        """
        days = set()
        hours = set()
        minutes = set()
        frames = list(np.arange(1800), dtype=float)

        days = days.union(self.hier.keys()).difference(['meta'])
        for day in self.hier.keys():
            if day == 'meta':
                continue

            hours = hours.union(self.hier[day].keys()).difference(['meta'])
            for hour in self.hier[day].keys():
                if hour == 'meta':
                    continue

                minutes = minutes.union(self.hier[day][hour].keys()).difference(['meta'])

        self.rangeTemplate =  {'days': sorted(days),
                               'hours': sorted(hours),
                               'minutes': sorted(minutes),
                               'frames': frames}

########### formerly in arrayBase

    def insertFrameArray(self, day, hour, minute, frames):
        self.addedNewData = True
        self.verifyStructureExists(day, hour, minute)
        for i, frame in enumerate(frames):
            self.data[day][hour][minute][i] = frame

        self.addFrameArrayToMean(day, hour, minute, frames)
        self.updateMax(day, hour, minute, np.max(frames))
        self.meta['totalNoFrames'] += frames.shape[0]
        self.addedNewData = True


    def insertDeltaValue(self, deltaValue):
        idx = deltaValue[0]
        data = deltaValue[1]
        self.updateValue(*self.idx2key(idx), data=data)
        self.addedNewData = True


    def insertDeltaVector(self, deltaVector):
        """
        Args:
            deltaVector (list of delta values)
                deltaValue ([idx, data])
        """
        for deltaValue in deltaVector:
            self.insertDeltaValue(deltaValue)


    def updateValue(self, day, hour, minute, frame, data):
        pMean =self.hier[day][hour][minute]['mean']
        N = len(self.data[day][hour][minute].keys())
        self.propagateMean(day, hour, minute, pMean, -N)

        self.data[day][hour][minute][frame] = data

        mean = np.mean(self.tree[day][hour][minute]['data'])
        self.propagateMean(day, hour, minute, mean, N)
        self.addedNewData = True
        # self.addSampleToMean(day, hour, minute, data)


    def addFrameArrayToMean(self, day, hour, minute, frames):
        mean = np.mean(frames)
        N = frames.shape[0]
        self.propagateMean(day, hour, minute, mean, N)


    def propagateMean(self, day, hour, minute, mean, N):
        self.addFrameArrayToStumpMean(self.hier[day][hour][minute], mean, N)
        self.addFrameArrayToStumpMean(self.hier[day][hour], mean, N)
        self.addFrameArrayToStumpMean(self.hier[day], mean, N)
        self.addFrameArrayToStumpMean(self.hier, mean, N)


    def addFrameArrayToStumpMean(self, stump, mean, N):
        M = stump['meta']['sampleN']
        if M+N == 0:
            newMean = 0
        else:
            newMean = (stump['meta']['mean'] * M + mean * N) / np.float(M+N)

        stump['meta']['mean'] = newMean
        stump['meta']['sampleN'] += N


    def generateRandomArraySequence(self, dayRng, hourRng, minuteRng, frameRng):
        self.resetAllSamples()
        for day in dayRng:
            for hour in hourRng:
                for minute in minuteRng:
                    minMax = np.random.rand(1)[0]

                    frames = np.random.rand(len(frameRng))  * minMax
                    frames[np.random.rand(len(frameRng)) > 0.98] = 1
                    self.insertFrameArray(day, hour, minute, frames)


    def getDeltaPositionMultipleFiles(self, key, frame):
        treeKey = filename2Time(key)
        day = treeKey[0]
        hour = treeKey[1]
        minute = treeKey[2]
        return day, hour, minute, frame

    def getDeltaPositionSingleFile(self, key, frame):
        framerate = 30

        day = int(np.ceil(frame / (24 * 60 * 60 * framerate)))
        frame -= (24 * 60 * 60 * framerate) * day
        hour = int(np.ceil(frame / (60 * 60 * framerate)))
        frame -= (60 * 60 * framerate) * hour
        minute = int(np.ceil(frame / (60 * framerate)))
        frame -= 60 * framerate * minute

        return day, hour, minute, frame


    def serializeData(self):
        return np.asarray(self.FDVT).tostring()


    def deserialize(self, msg):
        self.FDVT = np.fromstring(msg['data']).item()


    def test_Serialization(self):
        tmp = self.serializeData()
        tmpFDVT = type(self)()
        tmpFDVT.deserialize(tmp)

        isSame = True
        for day in self.data.keys():
            for hour in self.data[day].keys():
                for minute in self.data[day][hour].keys():
                    framesA = [self.data[day][hour][minute][k] \
                                for k in sorted(self.data[day][hour][minute].keys())]
                    framesB = [tmpFDVT.data[day][hour][minute][k] \
                                for k in sorted(tmpFDVT.data[day][hour][minute].keys())]

                    isSame = isSame and np.allclose(np.asarray(framesA),
                                                    np.asarray(framesB))

        return isSame



class FrameDataVisualizationTreeBehaviour(FrameDataVisualizationTreeBase):
    def __init__(self):
        super(FrameDataVisualizationTreeBehaviour, self).__init__()
        self.resetAllSamples()

    def resetAllSamples(self):
        super(FrameDataVisualizationTreeBehaviour, self).resetAllSamples()
        self.meta['isCategoric'] = True
        self.meta['filtList'] = []
        self.meta['maxClass'] = 0
        self.meta['singleFileMode'] = True
        self.meta['not-initialized'] = True


    def verifyStructureExists(self, day, hour, minute):
        super(FrameDataVisualizationTreeBehaviour, self).verifyStructureExists(day, hour, minute)

        if 'stack' not in  self.hier['meta'].keys():
            self.hier['meta']['stack'] = np.zeros(self.meta['maxClass'])

        if 'stack' not in  self.hier[day]['meta'].keys():
            self.hier[day]['meta']['stack'] = np.zeros(self.meta['maxClass'])

        if 'stack' not in  self.hier[day][hour]['meta'].keys():
            self.hier[day][hour]['meta']['stack'] = np.zeros(self.meta['maxClass'])

        if 'stack' not in  self.hier[day][hour][minute]['meta'].keys():
            self.hier[day][hour][minute]['meta']['stack'] = np.zeros(self.meta['maxClass'])


    def dict2array(self, d):
        if d:
            ar = np.zeros((self.meta['maxClass'],
                           len(self.meta['rangeTemplate']['frames'])))
            # ar = np.zeros((self.meta['maxClass'], max(d.keys()) + 1))
            for k, frame in d.items():
                for c, v in frame.items():
                    ar[c, k] = v
        else:
            ar = np.zeros((self.meta['maxClass'], 1))

        return ar

    def insertDeltaValue(self, deltaValue):
        key = deltaValue[0]
        data = deltaValue[1]
        increment = deltaValue[2]


        self.verifyStructureExists(key[0], key[1], key[2])
        self.insertSampleIncrement(*key, dataKey=data, dataInc=increment)
        frameArray = self.dict2array({key[3]:{data: increment}})
        self.addFrameArrayToStack(key[0], key[1], key[2], frameArray)
        self.addedNewData = True

    def insertFrameArray(self, day, hour, minute, frames):
        # super(FrameDataVisualizationTreeBehaviour, self).insertFrameArray(day, hour, minute, frames)

        self.verifyStructureExists(day, hour, minute)

        for k, i in frames.items():
            self.addSample(day, hour, minute, k, i)

        # frameList = [i for k, i in frames.items()]
        if frames.items():
            frameArray = self.dict2array(frames)
            self.addFrameArrayToStack(day, hour, minute, frameArray)
        self.addedNewData = True


    def addFrameArrayToStack(self, day, hour, minute, frames):
        stack = self.calcStack(frames)
        self.propagateStack(day, hour, minute, stack)


    def propagateStack(self, day, hour, minute, stack):
        self.addFrameArrayToStumpStack(self.hier[day][hour][minute], stack)
        self.addFrameArrayToStumpStack(self.hier[day][hour], stack)
        self.addFrameArrayToStumpStack(self.hier[day], stack)
        self.addFrameArrayToStumpStack(self.hier, stack)


    def addFrameArrayToStumpStack(self, stump, stack):
        if stump['meta']['stack'].shape[0] != self.meta['maxClass']:
            tmp = np.zeros(self.meta['maxClass'])
            tmp[:stump['meta']['stack'].shape[0]] = stump['meta']['stack']
            stump['meta']['stack'] = tmp

        stump['meta']['stack'] += stack


    def updateValue(self, day, hour, minute, frame, data):
        stack = self.calcStack(self.data[day][hour][minute])
        self.propagateStack(day, hour, minute, -stack)

        super(FrameDataVisualizationTreeBehaviour, self).updateValue(day, hour,
                                                                     minute,
                                                                     frame,
                                                                     data)

        stack = self.calcStack(self.data[day][hour][minute])
        self.propagateStack(day, hour, minute, stack)




    def updateMax(self, day, hour, minute, data):
        m = np.sum(data)
        super(FrameDataVisualizationTreeBehaviour, self).updateMax(day,
                                                                   hour,
                                                                   minute,
                                                                   m)

    def insertSampleIncrement(self, day, hour, minute, frame, dataKey, dataInc):
        try:
            if dataInc < 0:
                oldData = self.data[day][hour][minute][frame][dataKey]
                if oldData == self.hier[day][hour][minute]['meta']['max']:
                    newMax = np.max([np.sum(self.data[day][hour][minute][k]) \
                                for k in self.data[day][hour][minute].keys()])
                    self.updateMax(day, hour, minute, newMax)

            self.data[day][hour][minute][frame][dataKey] += dataInc
        except KeyError:
            try:
                self.data[day][hour][minute][frame][dataKey] = dataInc
            except KeyError:
                self.data[day][hour][minute][frame] = {dataKey:dataInc}

        if self.data[day][hour][minute][frame][dataKey] <= 0:
            del self.data[day][hour][minute][frame][dataKey]

        data = self.data[day][hour][minute][frame]
        self.updateMax(day, hour, minute, data)
        # self.addSampleToMean(day, hour, minute, data)
        self.meta['totalNoFrames'] += dataInc

    def insertSample(self, day, hour, minute, frame, data):
        self.data[day][hour][minute][frame] = data
        self.updateMax(day, hour, minute, data)
        # self.addSampleToMean(day, hour, minute, data)
        self.meta['totalNoFrames'] += 1
        self.addedNewData = True

    def calcStack(self, data):
        if np.max(data) > self.meta['maxClass']:
            self.meta['maxClass'] = int(np.max(data))
        # return bsc.countInt(data.astype(np.int),
        #                     minLength=self.meta['maxClass'] + 1)[1:,1]
        return np.sum(data, axis=1)

    # @profile
    def convertFrameListToDatum(self, anno, frameSlc, filtList):
        # data = np.zeros((len(anno.frameList[frameSlc])))
        data = dict()
        for l in xrange(len(filtList)):
            filteredAnno = anno.filterFrameList(filtList[l],
                                                exactMatch=False)

            for i in xrange(frameSlc.start, frameSlc.stop):
                if filteredAnno.frameList[i][0] is not None:
                    try:
                        data[i - frameSlc.start][l] = \
                            len(filteredAnno.frameList[i][0].keys())
                    except KeyError:
                        # data[i - frameSlc.start] = \
                        #     np.zeros((self.meta['maxClass'], 1))
                        # data[i - frameSlc.start][l] = \
                        #     len(filteredAnno.frameList[i][0].keys())

                        data[i - frameSlc.start] = \
                            {l: len(filteredAnno.frameList[i][0].keys())}

                    # if filtList[l].behaviours == ['test']:
                    #     1/0
                    # data[i - frameSlc.start] = l + 1

        return data

    def incrementTime(self, day, hour, minute):
        minute += 1
        if minute > 59:
            minute = 0
            hour += 1
            if hour > 23:
                hour = 0
                day += 1

        return day, hour, minute

    def addNewClass(self, filt):
        self.meta['filtList'] += [filt]
        self.meta['maxClass'] = len(self.meta['filtList'])
        self.addedNewData = True



    def createFDVTTemplateFromVideoList(self, videoList, runningIndeces):
        """
        It is recommended to use `createFDVTTemplateFromVideoList`

        :param days:
        :param hours:
        :param minutes:
        :return:
        """
        days = set()
        hours = set()
        minutes = set()
        frames = list(np.arange(1800, dtype=float))

        for video in videoList:
            if not runningIndeces:
                day, hour, minute, second = filename2Time(video)
            else:
                day, hour, minute, second = filename2TimeRunningIndeces(video)

            days = days.union([day])
            hours = hours.union([hour])
            minutes = minutes.union([minute])

        self.meta['rangeTemplate'] =  {'days': sorted(days),
                                       'hours': sorted(hours),
                                       'minutes': sorted(minutes),
                                       'frames': frames}

    def createFDVTTemplateFromSingleVideoFile(self, videoPath):
        frames = list(np.arange(1800, dtype=float))

        lastFrame = DL.retrieveVideoLength(videoPath)

        maxDay, maxHour, maxMinute, endFrame = \
                        self.getDeltaPositionSingleFile('', lastFrame)

        if maxDay > 0:
            days = range(maxDay + 1)
            hours = range(24)
            minutes = range(60)
        elif maxHour > 0:
            days = [0]
            hours = range(maxHour + 1)
            minutes = range(60)
        elif maxMinute > 0:
            days = [0]
            hours = [0]
            minutes = range(maxMinute + 1)
        else:
            days = [0]
            hours = [0]
            minutes = [0]
            frames = range(endFrame)

        self.meta['rangeTemplate'] =  {'days': sorted(days),
                                       'hours': sorted(hours),
                                       'minutes': sorted(minutes),
                                       'frames': frames}

    def importAnnotation(self, annotation, fps=30):
        day = 0
        hour = 0
        minute = 0

        if len(annotation.frameList) <= fps * 60:
            frameSlc = slice(0, len(annotation.frameList))
            data = self.convertFrameListToDatum(annotation, frameSlc,
                                                self.meta['filtList'])
            self.insertFrameArray(day, hour, minute, data)
            self.meta['not-initialized'] = False
            return

        i = 0
        for k in xrange(fps * 60, len(annotation.frameList), fps * 60):
            print k, day, hour, minute
            frameSlc = slice(i, k)
            data = self.convertFrameListToDatum(annotation, frameSlc,
                                                self.meta['filtList'])
            self.insertFrameArray(day, hour, minute, data)
            day, hour, minute = self.incrementTime(day, hour, minute)
            i = k

            self.meta['not-initialized'] = False


    # @profile
    def importAnnotationsFromSingleFile(self, bhvrFile, annotations,
                                        vials, runningIndeces=False, fps=30):
        # filtList = []
        # self.resetAllSamples()


        anno = Annotation.Annotation()
        anno.loadFromFile(bhvrFile)

        self.importAnnotation(anno, fps)


    def importAnnotations(self, bhvrList, videoList, annotations, vials,
                          runningIndeces=False, fps=30, singleFileMode=None):

        filtList = []
        self.resetAllSamples()

        if len(videoList) == 1:
            self.createFDVTTemplateFromSingleVideoFile(videoList[0])
            self.meta['singleFileMode'] = True
        elif len(videoList) > 1:
            self.createFDVTTemplateFromVideoList(videoList, runningIndeces)
            self.meta['singleFileMode'] = False


        for i in range(len(annotations)):
            annotator = annotations[i]["annot"]
            behaviour = annotations[i]["behav"]
            self.addNewClass(Annotation.AnnotationFilter(vials,
                                                        [annotator],
                                                        [behaviour]))

        if len(bhvrList) == 0:
            return

        if len(videoList) == 1:
            self.importAnnotationsFromSingleFile(bhvrList[0],
                                                 annotations, vials,
                                                 runningIndeces=False, fps=30)
            return

#
#         for i in range(len(annotations)):
#             annotator = annotations[i]["annot"]
#             behaviour = annotations[i]["behav"]
#             filtList += [Annotation.AnnotationFilter(vials,
#                                                           [annotator],
#                                                           [behaviour])]
#
# #         self.meta['maxClass'] = len(filtList)
#         self.meta['filtList'] = filtList
#         self.meta['maxClass'] = len(filtList)

        if len(filtList) == 0:
            return
            # raise ValueError("no annotations specified!")

        for f in bhvrList:
            # load annotation and filter it #
            anno = Annotation.Annotation()

            anno.loadFromFile(f)

            if not runningIndeces:
                day, hour, minute, second = filename2Time(f)
            else:
                day, hour, minute, second = filename2TimeRunningIndeces(f)

            frameSlc = slice(0, len(anno.frameList))
            data = self.convertFrameListToDatum(anno, frameSlc,
                                                self.meta['filtList'])

            if data != {}:
                self.insertFrameArray(day, hour, minute, data)
                self.meta['not-initialized'] = False


            # self.meta['not-initialized'] = False

            # for l in range(len(filtList)):
            #
            #     filteredAnno = anno.filterFrameList(filtList[l])
            #
            #     if not runningIndeces:
            #         day, hour, minute, second = filename2Time(f)
            #     else:
            #         day, hour, minute, second = filename2TimeRunningIndeces(f)


                # for i in range(len(filteredAnno.frameList)):
                #     if filteredAnno.frameList[i][0] is not None:

                        # self.addSample(day, hour, minute,
                        #                       filteredAnno.frameList[i][0])
            #             if data[i] != 0:
            #                 warnings.warn("Ambigous label of frame {f} in {d}".format(f=i, d=f))
            #             data[i] = l + 1
            #
            # else:
            #     self.insertFrameArray(day, hour, minute, data)



    def getAnnotationFilterCode(self, filt):
        for i in range(len(self.meta['filtList'])):
            if self.meta['filtList'][i] == filt:
                return i

        return None

    def getDeltaValue(self, key, frame, filt, increment=1):
        if self.meta['singleFileMode']:
            return [self.getDeltaPositionSingleFile(key, frame),
                    self.getAnnotationFilterCode(filt),
                    increment]
        else:
            return [self.getDeltaPositionMultipleFiles(key, frame),
                    self.getAnnotationFilterCode(filt),
                    increment]



    def getStackFromStump(self, stump, timeKey):
        stack = []
        for k in sorted(self.meta['rangeTemplate'][timeKey]):
            if k in stump.keys():
                if stump[k]['meta']['stack'].shape[0] != self.meta['maxClass']:
                    tmp = np.zeros(self.meta['maxClass'])
                    tmp[:stump[k]['meta']['stack'].shape[0]] = \
                                                    stump[k]['meta']['stack']
                    stump[k]['meta']['stack'] = tmp

                stack += [stump[k]['meta']['stack']]
            else:
                stack += [np.zeros(self.meta['maxClass'])]

        return stack



    def generatePlotDataFrames(self, day, hour, minute, frame,
                               frameResolution=1):

        # if self.data == dict():
        #     self.plotData['days'] = dict()
        #     self.plotData['days']['data'] = [0]
        #     self.plotData['days']['weight'] = [0]
        #     self.plotData['days']['tick'] = [0]
        #
        #     self.plotData['hours'] = dict()
        #     self.plotData['hours']['data'] = [0]
        #     self.plotData['hours']['weight'] = [0]
        #     self.plotData['hours']['tick'] = [0]
        #
        #     self.plotData['minutes'] = dict()
        #     self.plotData['minutes']['data'] = [0]
        #     self.plotData['minutes']['weight'] = [0]
        #     self.plotData['minutes']['tick'] = [0]
        #
        #     self.plotData['frames'] = dict()
        #     self.plotData['frames']['data'] = [0]
        #     self.plotData['frames']['weight'] = [0]
        #     self.plotData['frames']['tick'] = [0]
        #     return
        cfg.log.info("{0}, {1}, {2}, {3}".format(day, hour, minute, frame))
        self.plotData['days'] = dict()
        stack = self.getStackFromStump(self.hier, 'days')
        self.plotData['days']['data'] = np.asarray(stack)#.T
        self.plotData['days']['weight'] = 0

        self.plotData['hours'] = dict()
        try:
            stump = self.hier[day]
        except KeyError:
            stump = None

        if stump is not None:
            stack = self.getStackFromStump(stump, 'hours')
            self.plotData['hours']['data'] = np.asarray(stack)#.T
        else:
            self.plotData['hours']['data'] = []
        self.plotData['hours']['weight'] = 0

        self.plotData['minutes'] = dict()
        try:
            stump = self.hier[day][hour]
        except KeyError:
            stump = None

        if stump is not None:
            stack = self.getStackFromStump(stump, 'minutes')
            self.plotData['minutes']['data'] = np.asarray(stack)#.T
        else:
            self.plotData['minutes']['data'] = []
        self.plotData['minutes']['weight'] = 0


        self.plotData['frames'] = dict()
        try:
            stump = self.data[day][hour][minute]
        except KeyError:
            stump = None

        if stump is not None:
            self.createStackData(self.plotData['frames'],
                                 stump,
                                 frameResolution)
        else:
            self.plotData['frames']['data'] = np.zeros((
                                    len(self.meta['rangeTemplate']['frames']) /
                                    frameResolution,
                                    self.meta['maxClass']))


    def createStackData(self, plotData, inData, frameResolution):
#         plotData = dict()
        plotData['data'] = []
        plotData['weight'] = []
        plotData['tick'] = []


        if self.data == dict():
            plotData['data'] += [0]
            plotData['weight'] += [0]
            plotData['tick'] += [0]
            return

        data = self.dict2array(inData).T#np.asarray([int(x) for k, x in inData.items()])
        # data = data.astype(np.int) #self.tree[day][hour][minute]['data'].astype(np.int)
        # 1/0

        res = np.zeros((np.ceil(data.shape[0] / np.float(frameResolution)),
                        self.meta['maxClass']))
        rng = slice(0, frameResolution)

        for i in range(res.shape[0]):
            res[i,:] = np.sum(data[rng], axis=0)#self.calcStack(data[rng])
            rng = slice(rng.stop, rng.stop + frameResolution)


        plotData['data'] = res
        plotData['weight'] = np.ones((res.shape[1]))
        plotData['tick'] = range(0, data.shape[0], frameResolution)


    def getClassOccurances(self, classNo):
        occurranceList = []

        isSame = True
        for day in sorted(self.data.keys()):
            for hour in sorted(self.data[day].keys()):
                for minute in sorted(self.data[day][hour].keys()):

                    # print day, hour, minute,
                    frames = [self.data[day][hour][minute][k] \
                                for k in sorted(self.data[day][hour][minute].keys())]
                    idces = np.where(frames == classNo)
                    for i in range(idces[0].shape[0]):
                        occurranceList += [[day, hour, minute, idces[0][i]]]

        return occurranceList
