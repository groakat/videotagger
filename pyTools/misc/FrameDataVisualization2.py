import numpy as np
import os
import time
import warnings
import pyTools.misc.basic as bsc
import pandas as pd
import pyTools.videoProc.annotation as Annotation
import pyTools.videoTagger.dataLoader as DL
import pyTools.misc.Cache as C

import pyTools.misc.config as cfg

def filename2Time(f):
    timestamp = f.split('/')[-1]
    day, timePart = timestamp.split('.')[:2]
    hour, minute, second = timePart.split('-')

    return day, int(hour), int(minute), int(second)


def filename2TimeRunningIndeces(f):
    # timestamp = f.split('/')[-1].split('.')[0]
    # rawMinutes = timestamp.split('_')[-1]
    # day, hour, minute, second = minutes2Time(int(rawMinutes))
    #
    # return day, int(hour), int(minute), int(second)

    timestamp = f.split('.')[0]

    day, hour, minute = [int(x) for x in timestamp.split('/')[-3:]]

    return day, hour, minute, 0


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


def copytree(src, dst, symlinks=False, ignore=None):
    import shutil
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def loadFDVT(folder):
    """
    Dynamically determines the type of the FDVT and returns the correct type
    :param path:
    :return:
    """
    path = os.path.join(folder, 'fdvt.npy')
    if not os.path.exists(path):
        return None

    FDVT = np.load(path).item()
    root = os.path.dirname(path)
    try:
        if FDVT['meta']['type'].split('.')[-1] == 'FrameDataVisualizationTreeBase':
            fdv = FrameDataVisualizationTreeBase(root)
        elif FDVT['meta']['type'].split('.')[-1] == 'FrameDataVisualizationTreeBehaviour':
            fdv = FrameDataVisualizationTreeBehaviour(root)
    except KeyError:
        # fallback
        fdv = FrameDataVisualizationTreeBehaviour(root)

    fdv.FDVT = FDVT
    fdv.data = FDVT['data']
    fdv.hier = FDVT['hier']
    fdv.meta = FDVT['meta']

    return fdv


class FDVFileCache(C.CachePrefetchBase):
    def loadDatum(self, path):
        if os.path.exists(path):
            df = pd.read_pickle(path)
        else:
            df = pd.DataFrame(columns=('frames', 'classID', 'amount'))
            df.set_index(['frames', 'classID'], inplace=True)
            df.sortlevel(inplace=True)

        return df

    def save(self, path):
        df = self.cache[path]
        df.to_pickle(path)

        del self.cache[path]

    def updateValue(self, path, df):
        self.cache[path] = df

class FrameDataVisualizationTreeBase(object):

    def __init__(self, root):
        self.data = dict()          # tree of data
        self.hier = dict()          # summarized information
                                    # max, mean, sampleN
        self.meta = dict()          # classes, etc

        self.FDVT = {'data': self.data,
                     'hier': self.hier,
                     'meta': self.meta}

        self.root = root
        self.cache = FDVFileCache([])

        self.resetAllSamples()

        self.addedNewData = True
        self.integrityEnsured = True
        self.possibleCorrupted = set()
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
        self.meta['type'] = type(self).__name__

        self.meta['isCategoric'] = False
        self.meta['singleFileMode'] = True     # if True, only one file (key) is used
                                        # to save the entire annotation
        self.meta['totalNoFrames'] = 0

        self.meta['rangeTemplate'] = dict()
        self.meta['rangeTemplate']['frames'] = range(1800)

        self.meta['maxDay'] = 0
        self.meta['maxHour'] = 0
        self.meta['maxMinute'] = 0

        self.addedNewData = True
        self.integrityEnsured = True
        self.possibleCorrupted = set()
        # self.ranges = dict()


    def save(self, dst_folder=None):
        if dst_folder is None:
            dst_folder = self.root

        if dst_folder is not self.root:
            src_folder = self.root

            if not os.path.exists(dst_folder):
                os.makedirs(dst_folder)

            copytree(src_folder, dst_folder)

            self.root = dst_folder
        else:
            if not os.path.exists(self.root):
                os.makedirs(self.root)

        np.save(os.path.join(self.root,
                             'fdvt.npy'), np.asarray(self.FDVT))

    def load(self, folder):
        """ Load from FOLDER
        :param folder: folder
        :return:
        """
        self.FDVT = np.load(os.path.join(folder,
                                         'fdvt.npy')).item()
        self.data = self.FDVT['data']
        self.hier = self.FDVT['hier']
        self.meta = self.FDVT['meta']
        self.root = folder

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

    def updateValues(self, day, hour, minute, df):
        path = self.getFramesFilename(day, hour, minute)
        self.cache.updateValue(path, df)

    def saveValues(self, day, hour, minute):
        path = self.getFramesFilename(day, hour, minute)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        self.cache.save(path)


    def getValues(self, day, hour, minute):
        path = self.getFramesFilename(day, hour, minute)
        return self.cache.getItem(path)
        # if os.path.exists(path):
        #     df = pd.load(path)
        # else:
        #     df = pd.DataFrame(columns=('frames', 'classID', 'amount'))
        #     df.set_index(['frames', 'classID'], inplace=True)
        #     df.sortlevel(inplace=True)
        #
        # return df

    # def getValueFilename(self, filename, frame):
    #     return self.getValues(*filename2Time(filename)[:3], frame=frame)


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



    def computeTemplateRange(self):
        frames = list(np.arange(1800, dtype=float))
        multipleDays = False

        if not isinstance(self.meta['maxDay'], basestring):
            if self.meta['maxDay'] > 0:
                days = range(self.meta['maxDay'] + 1)
                hours = range(24)
                minutes = range(60)
                multipleDays = True
            else:
                days = [0]
        else:
            try:
                if self.meta['rangeTemplate']['days'] == [0]:
                    self.meta['rangeTemplate']['days'] = []
            except KeyError:
                # 'days' do not exist yet
                self.meta['rangeTemplate']['days'] = []

            if self.meta['maxDay'] not in self.meta['rangeTemplate']['days']:
                days = self.meta['rangeTemplate']['days'] + \
                       [self.meta['maxDay']]
            else:
                days = self.meta['rangeTemplate']['days']

            if len(self.meta['rangeTemplate']['days']) > 1:
                hours = range(24)
                minutes = range(60)
                multipleDays = True

        if multipleDays:
            pass
        elif self.meta['maxHour'] > 0:
            hours = range(self.meta['maxHour'] + 1)
            minutes = range(60)
        elif self.meta['maxMinute'] > 0:
            hours = [0]
            minutes = range(self.meta['maxMinute'] + 1)
        else:
            hours = [0]
            minutes = [0]
            frames = range(max(self.hier[0][0][0]))

        self.meta['rangeTemplate'] =  {'days': sorted(days),
                                       'hours': sorted(hours),
                                       'minutes': sorted(minutes),
                                       'frames': sorted(frames)}


    def verifyStructureExists(self, day, hour, minute):
        try:
            self.hier['meta']
        except KeyError:
            self.hier['meta'] = self.getStandardHierDatum()

        recomputeTemplate = False

        if day not in self.data.keys():
            self.data[day] = dict()
            self.hier[day] = dict()
            self.hier[day]['meta'] = self.getStandardHierDatum()
            if isinstance(day, basestring):
                try:
                    if day not in self.meta['rangeTemplate']['days']:
                        self.meta['maxDay'] = day
                        recomputeTemplate = True
                except KeyError:
                    self.meta['maxDay'] = day
                    recomputeTemplate = True

            elif day > self.meta['maxDay']:
                self.meta['maxDay'] = day
                recomputeTemplate = True

            
        if hour not in self.data[day].keys():
            self.data[day][hour] = dict()
            self.hier[day][hour] = dict()
            self.hier[day][hour]['meta'] = self.getStandardHierDatum()
            if int(hour) > self.meta['maxHour']:
                self.meta['maxHour'] = int(hour)
                recomputeTemplate = True
            
        if minute not in self.data[day][hour].keys():
            self.data[day][hour][minute] = dict()
            self.hier[day][hour][minute] = dict()
            self.hier[day][hour][minute]['meta'] = self.getStandardHierDatum()
            if int(minute) > self.meta['maxMinute']:
                self.meta['maxMinute'] = int(minute)
                recomputeTemplate = True

        if recomputeTemplate:
            self.computeTemplateRange()

    def incrementMean(self, prevMean, prevN, mean, n):
        # return prevMean + (1.0/n) * (data - prevMean)
        return (1.0 / (prevN + n)) * (prevMean * prevN + mean * n)


    def addSampleToStumpMean(self, stump, mean, n=1):
        """

        :param key: (day) or (day, hour) or (day, hour, minute)
        :param mean:
        :return:
        """
        if stump['meta']['sampleN'] + n == 0:
            stump['meta']['mean'] = 0
        else:
            stump['meta']['mean'] = self.incrementMean(stump['meta']['mean'],
                                                       stump['meta']['sampleN'],
                                                        mean,
                                                        n)
        stump['meta']['sampleN'] += n


    def updateMean(self, day, hour, minute):
        # remove previous mean
        old_mean = self.hier[day][hour][minute]['meta']['mean']
        old_n = self.hier[day][hour][minute]['meta']['sampleN']
        self.addSampleToStumpMean(self.hier[day][hour], old_mean, -old_n)
        self.addSampleToStumpMean(self.hier[day], old_mean, -old_n)
        self.addSampleToStumpMean(self.hier, old_mean, -old_n)

        # calculate and add new mean
        df = self.getValues(day, hour, minute)
        if df.empty:
            mean = 0
            n = 0
        else:
            mean = np.mean(np.asarray(df))
            n = len(df)

        self.hier[day][hour][minute]['meta']['mean'] = mean
        self.hier[day][hour][minute]['meta']['sampleN'] = n
        self.addSampleToStumpMean(self.hier[day][hour], mean, n)
        self.addSampleToStumpMean(self.hier[day], mean, n)
        self.addSampleToStumpMean(self.hier, mean, n)


    def getFramesFilename(self, day, hour, minute):
        if not isinstance(day, basestring):
            day = "{0:03d}".format(day)

        if not isinstance(hour, basestring):
            hour = "{0:02d}".format(hour)

        if not isinstance(minute, basestring):
            minute = "{0:02d}".format(minute)

        return os.path.join(self.root,
                            day,
                            hour,
                            minute + ".pkl")

    #
    # def addSample(self, day, hour, minute, df):
    #     """ Adds single sample (single frame)
    #
    #     :param day:
    #     :param hour:
    #     :param minute:
    #     :return:
    #     """
    #     self.verifyStructureExists(day, hour, minute)
    #
    #     # using try, except because its much fast than looking up the keys
    #     try:
    #         self.replaceSample(day, hour, minute, df)
    #     except KeyError:
    #         self.insertSample(day, hour, minute, df)
    #
    #     self.addedNewData = True

    def restoreIntegrity(self):
        if self.integrityEnsured:
            return

        for day, hour, minute in list(self.possibleCorrupted):
            df = self.getValues(day, hour, minute)
            # remove negative values that could arise with negative increments in
            # new_df
            df.drop(df[df['amount'] <= 0].index, inplace=True)

        self.integrityEnsured = True

    def insertSample(self, day, hour, minute, new_df, dontSave=False, checkIntegrity=True):
        ts = time.time()
        self.verifyStructureExists(day, hour, minute)
        t1 = time.time()

        df = self.getValues(day, hour, minute)

        t2 = time.time()
        oldFrameAmount = len(df.index.levels[0])
        df = df.add(new_df, fill_value=0)
        if checkIntegrity:
            if new_df.min()['amount'] < 0:
                # remove negative values that could arise with negative increments in
                # new_df
                df = df.drop(df[df['amount'] <= 0].index)
        else:
            self.integrityEnsured = False
            self.possibleCorrupted |= {(day, hour, minute)}

        t3 = time.time()
        self.updateValues(day, hour, minute, df)
        t4 = time.time()

        frameAmountInc = len(df.index.levels[0]) - oldFrameAmount
        self.meta['totalNoFrames'] += frameAmountInc

        if self.meta['isCategoric']:
            self.updateMax(day, hour, minute)
            self.updateMean(day, hour, minute)

        t5 = time.time()
        self.addedNewData = True

        if not dontSave:
            self.saveValues(day, hour, minute)
        te = time.time()

        cfg.log.info("total time: {}\nt1: {}\nt2: {} \nt3: {} \nt4: {}\nt5: {}".format(te - ts,
                                                                       t1 - ts,
                                                                       t2 - t1,
                                                                       t3 - t2,
                                                                       t4 - t3,
                                                                       t5 - t4))


    def getIndexFromFramesAndClass(self, day, hour, minute, frames, classID):
        df = self.cache.getItem(self.getFramesFilename(day, hour, minute))

        if type(frames) != list:
            frames = [frames]

        cID = [classID] * len(frames)
        tuples = zip(*[frames, cID])
        idx = pd.MultiIndex.from_tuples(tuples,
                                         names=['frames', 'classID'])

        return idx.intersection(df.index)



    def removeSample(self, day, hour, minute, index, dontSave=False):
        """

        :param day:
        :param hour:
        :param minute:
        :param index: MultiIndex from Dataframe or generated by :func:`getIndexFromFramesAndClass`
        :param dontSave:
        :return:
        """
        oldData = self.getValues(day, hour, minute)
        oldFrameAmount = len(oldData.index.levels[0])

        try:
            oldData.drop(index, inplace=True)
        except KeyError:
            # nothing there, so nothing to remove
            pass

        if self.meta['isCategoric']:
            self.updateMax(day, hour, minute)
            self.updateMean(day, hour, minute)

        frameAmountInc = len(oldData.index.levels[0]) - oldFrameAmount
        self.meta['totalNoFrames'] += frameAmountInc
        self.addedNewData = True

        if not dontSave:
            self.saveValues(day, hour, minute)


    def replaceSample(self, day, hour, minute, df):
        self.removeSample(day, hour, minute, df.index, dontSave=True)
        self.insertSample(day, hour, minute, df)
        self.addedNewData = True


    def updateMax(self, day, hour, minute):
        df = self.getValues(day, hour, minute)
        if df.empty:
            new_max = 0
        else:
            new_max = np.max(np.asarray(df))

        if self.hier[day][hour][minute]['meta']['max'] < new_max:
            self.hier[day][hour][minute]['meta']['max'] = new_max

            if self.hier[day][hour]['meta']['max'] < new_max:
                self.hier[day][hour]['meta']['max'] = new_max

                if  self.hier[day]['meta']['max'] < new_max:
                    self.hier[day]['meta']['max'] = new_max

                    if self.hier['meta']['max'] < new_max:
                        self.hier['meta']['max'] = new_max
        else:
            old_max = self.hier[day][hour][minute]['meta']['max']
            self.hier[day][hour][minute]['meta']['max'] = new_max

            if self.hier[day][hour]['meta']['max'] == old_max:
                new_max = max([self.hier[day][hour][m]['meta']['max']
                                    for m in self.hier[day][hour].keys()
                                        if m != 'meta'])

                self.hier[day][hour]['meta']['max'] = new_max

                if self.hier[day]['meta']['max'] == old_max:
                    new_max = max([self.hier[day][h]['meta']['max']
                                        for h in self.hier[day].keys()
                                            if h != 'meta'])

                    self.hier[day]['meta']['max'] = new_max

                    if self.hier['meta']['max'] == old_max:
                        new_max = max([self.hier[d]['meta']['max']
                                            for d in self.hier.keys()
                                                if d != 'meta'])

                        self.hier['meta']['max'] = new_max

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

        for key in sorted(self.meta['rangeTemplate']['minutes']):
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
        frameResolution = float(frameResolution)
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
            keys = self.data[day][hour][minute].keys()
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
            self.plotData['frames']['weight'] += [sum(tmpVal) / float(cnt)]
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

    # def insertFrameArray(self, day, hour, minute, frames):
    #     self.addedNewData = True
    #     self.verifyStructureExists(day, hour, minute)
    #     for i, frame in enumerate(frames):
    #         self.data[day][hour][minute][i] = frame
    #
    #     self.addFrameArrayToMean(day, hour, minute, frames)
    #     self.updateMax(day, hour, minute, np.max(frames))
    #     self.meta['totalNoFrames'] += frames.shape[0]
    #     self.addedNewData = True


    # def insertDeltaValue(self, deltaValue):
    #     idx = deltaValue[0]
    #     data = deltaValue[1]
    #     self.updateValue(*self.idx2key(idx), data=data)
    #     self.addedNewData = True
    #
    #
    def insertDeltaVector(self, deltaVector):
        """
        Args:
            deltaVector (list of delta values)
                deltaValue ([idx, data])
        """
        # for deltaValue in deltaVector:
        #     self.insertDeltaValue(deltaValue,
        #                           checkIntegrity=False)

        ts = time.time()
        d = {}
        for deltaValue in deltaVector:
            day, hour, minute, frame = deltaValue[0]
            classID = deltaValue[1]
            increment = deltaValue[2]

            if (day, hour, minute) not in d:
                d[(day, hour, minute)] = []

            d[(day, hour, minute)] += [[frame, classID, increment]]

        t1 = time.time()
        for (day, hour, minute), lst in d.items():
            df = pd.DataFrame(lst, columns=('frames', 'classID', 'amount'))
            # t1 = time.time()
            df.set_index(['frames', 'classID'], inplace=True)
            # t2 = time.time()
            # df.sortlevel(inplace=True)
            # t3 = time.time()

            self.insertSample(day, hour, minute, df, checkIntegrity=True)


        # day, hour, minute, frame = deltaValue[0]
        # classID = deltaValue[1]
        # increment = deltaValue[2]
        #
        # ts = time.time()
        #
        # df = pd.DataFrame([[frame, classID, increment]], columns=('frames', 'classID', 'amount'))
        # t1 = time.time()
        # df.set_index(['frames', 'classID'], inplace=True)
        # t2 = time.time()
        # # df.sortlevel(inplace=True)
        # t3 = time.time()
        #
        # self.insertSample(day, hour, minute, df, checkIntegrity=checkIntegrity)

        # t4 = time.time()
        te = time.time()
        cfg.log.info("total time: {}\nt1: {}\nt2: {}".format(te - ts,
                                                             t1 - ts,
                                                             te - t1))

        # self.restoreIntegrity()

    #
    # def updateValue(self, day, hour, minute, frame, data):
    #     pMean =self.hier[day][hour][minute]['mean']
    #     N = len(self.data[day][hour][minute].keys())
    #     self.propagateMean(day, hour, minute, pMean, -N)
    #
    #     self.data[day][hour][minute][frame] = data
    #
    #     mean = np.mean(self.tree[day][hour][minute]['data'])
    #     self.propagateMean(day, hour, minute, mean, N)
    #     self.addedNewData = True
    #     # self.addSampleToMean(day, hour, minute, data)
    #
    #
    # def addFrameArrayToMean(self, day, hour, minute, frames):
    #     mean = np.mean(frames)
    #     N = frames.shape[0]
    #     self.propagateMean(day, hour, minute, mean, N)
    #
    #
    # def propagateMean(self, day, hour, minute, mean, N):
    #     self.addFrameArrayToStumpMean(self.hier[day][hour][minute], mean, N)
    #     self.addFrameArrayToStumpMean(self.hier[day][hour], mean, N)
    #     self.addFrameArrayToStumpMean(self.hier[day], mean, N)
    #     self.addFrameArrayToStumpMean(self.hier, mean, N)
    #
    #
    # def addFrameArrayToStumpMean(self, stump, mean, N):
    #     M = stump['meta']['sampleN']
    #     if M+N == 0:
    #         newMean = 0
    #     else:
    #         newMean = (stump['meta']['mean'] * M + mean * N) / np.float(M+N)
    #
    #     stump['meta']['mean'] = newMean
    #     stump['meta']['sampleN'] += N


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
    def __init__(self, root):
        super(FrameDataVisualizationTreeBehaviour, self).__init__(root)
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


    # def dict2array(self, d):
    #     if d:
    #         ar = np.zeros((self.meta['maxClass'],
    #                        len(self.meta['rangeTemplate']['frames'])))
    #         # ar = np.zeros((self.meta['maxClass'], max(d.keys()) + 1))
    #         for k, frame in d.items():
    #             if type(frame) != dict:
    #                 # quick hack... sorry
    #                 # first line needed for visualization (generate plot data)
    #                 ar[:, k] = frame
    #             else:
    #                 # these are needed for insertDeltaValue
    #                 for c, v in frame.items():
    #                     ar[c, k] = v
    #     else:
    #         ar = np.zeros((self.meta['maxClass'], 1))
    #
    #     return ar

    def addNewClass(self, filt):
        self.meta['filtList'] += [filt]
        self.meta['maxClass'] = len(self.meta['filtList'])
        self.addedNewData = True

    def addFrameArrayToStumpStack(self, stump, stack):
        if stump['meta']['stack'].shape[0] == stack.shape[0]:
            # needed to allow removing stack even if new class was added
            stump['meta']['stack'] += stack
        else:
            if stump['meta']['stack'].shape[0] != self.meta['maxClass']:
                tmp = np.zeros(self.meta['maxClass'])
                tmp[:stump['meta']['stack'].shape[0]] = stump['meta']['stack']
                stump['meta']['stack'] = tmp

            stump['meta']['stack'] += stack

    def propagateStack(self, day, hour, minute, stack):
        self.addFrameArrayToStumpStack(self.hier[day][hour][minute], stack)
        self.addFrameArrayToStumpStack(self.hier[day][hour], stack)
        self.addFrameArrayToStumpStack(self.hier[day], stack)
        self.addFrameArrayToStumpStack(self.hier, stack)

    def filterClass(self, df, classID):
        try:
            r = df.loc[(slice(None, None), classID), :]
        except KeyError:
            r = 0

        return r

    def updateStack(self, day, hour, minute):
        df = self.getValues(day, hour, minute)

        stackSum = lambda c: np.sum(np.asarray(self.filterClass(df, c)))
        stack = np.asarray([stackSum(c)
                                for c in range(self.meta['maxClass'])])

        oldStack = self.hier[day][hour][minute]['meta']['stack']
        self.propagateStack(day, hour, minute, -oldStack)
        self.propagateStack(day, hour, minute, stack)

    def insertSample(self, day, hour, minute, new_df, checkIntegrity=True):
        super(FrameDataVisualizationTreeBehaviour, self).insertSample(day,
                                                                      hour,
                                                                      minute,
                                                                      new_df,
                                                checkIntegrity=checkIntegrity)
        self.updateStack(day, hour, minute)

    def removeSample(self, day, hour, minute, index, dontSave=False):
        super(FrameDataVisualizationTreeBehaviour, self).removeSample(day,
                                                                      hour,
                                                                      minute,
                                                                      index,
                                                                      dontSave)
        self.updateStack(day, hour, minute)

    def insertDeltaValue(self, deltaValue, checkIntegrity=True):
        day, hour, minute, frame = deltaValue[0]
        classID = deltaValue[1]
        increment = deltaValue[2]

        ts = time.time()

        df = pd.DataFrame([[frame, classID, increment]], columns=('frames', 'classID', 'amount'))
        t1 = time.time()
        df.set_index(['frames', 'classID'], inplace=True)
        t2 = time.time()
        # df.sortlevel(inplace=True)
        t3 = time.time()

        self.insertSample(day, hour, minute, df, checkIntegrity=checkIntegrity)

        t4 = time.time()
        te = time.time()
        cfg.log.info("total time: {}\nt1: {}\nt2: {} \nt3: {} \nt4: {}".format(te - ts,
                                                                       t1 - ts,
                                                                       t2 - t1,
                                                                       t3 - t2,
                                                                       t4 - t3))
        # increment = deltaValue[2]
        #
        #
        # self.verifyStructureExists(key[0], key[1], key[2])
        # self.insertSampleIncrement(*key, dataKey=data, dataInc=increment)
        # frameArray = self.dict2array({key[3]:{data: increment}})
        # self.addFrameArrayToStack(key[0], key[1], key[2], frameArray)
        # self.addedNewData = True

    # def insertFrameArray(self, day, hour, minute, frames):
    #     # super(FrameDataVisualizationTreeBehaviour, self).insertFrameArray(day, hour, minute, frames)
    #
    #     self.verifyStructureExists(day, hour, minute)
    #
    #     for k, i in frames.items():
    #         self.addSample(day, hour, minute, k, i)
    #
    #     # frameList = [i for k, i in frames.items()]
    #     if frames.items():
    #         frameArray = self.dict2array(frames)
    #         self.addFrameArrayToStack(day, hour, minute, frameArray)
    #     self.addedNewData = True


    # def addFrameArrayToStack(self, day, hour, minute, frames):
    #     stack = self.calcStack(frames)
    #     self.propagateStack(day, hour, minute, stack)
    #
    #
    # def propagateStack(self, day, hour, minute, stack):
    #     self.addFrameArrayToStumpStack(self.hier[day][hour][minute], stack)
    #     self.addFrameArrayToStumpStack(self.hier[day][hour], stack)
    #     self.addFrameArrayToStumpStack(self.hier[day], stack)
    #     self.addFrameArrayToStumpStack(self.hier, stack)
    #
    #
    # def addFrameArrayToStumpStack(self, stump, stack):
    #     if stump['meta']['stack'].shape[0] != self.meta['maxClass']:
    #         tmp = np.zeros(self.meta['maxClass'])
    #         tmp[:stump['meta']['stack'].shape[0]] = stump['meta']['stack']
    #         stump['meta']['stack'] = tmp
    #
    #     stump['meta']['stack'] += stack

    #
    # def updateValue(self, day, hour, minute, frame, data):
    #     stack = self.calcStack(self.data[day][hour][minute])
    #     self.propagateStack(day, hour, minute, -stack)
    #
    #     super(FrameDataVisualizationTreeBehaviour, self).updateValue(day, hour,
    #                                                                  minute,
    #                                                                  frame,
    #                                                                  data)
    #
    #     stack = self.calcStack(self.data[day][hour][minute])
    #     self.propagateStack(day, hour, minute, stack)




    # def updateMax(self, day, hour, minute, data):
    #     m = np.sum(data)
    #     super(FrameDataVisualizationTreeBehaviour, self).updateMax(day,
    #                                                                hour,
    #                                                                minute,
    #                                                                m)
    #
    # def insertSampleIncrement(self, day, hour, minute, frame, dataKey, dataInc):
    #     try:
    #         if dataInc < 0:
    #             oldData = self.data[day][hour][minute][frame][dataKey]
    #             if oldData == self.hier[day][hour][minute]['meta']['max']:
    #                 newMax = np.max([np.sum(self.data[day][hour][minute][k]) \
    #                             for k in self.data[day][hour][minute].keys()])
    #                 self.updateMax(day, hour, minute, newMax)
    #
    #         self.data[day][hour][minute][frame][dataKey] += dataInc
    #     except KeyError:
    #         try:
    #             self.data[day][hour][minute][frame][dataKey] = dataInc
    #         except KeyError:
    #             self.data[day][hour][minute][frame] = {dataKey:dataInc}
    #
    #     if self.data[day][hour][minute][frame][dataKey] <= 0:
    #         del self.data[day][hour][minute][frame][dataKey]
    #
    #     data = self.data[day][hour][minute][frame]
    #     self.updateMax(day, hour, minute, data)
    #     # self.addSampleToMean(day, hour, minute, data)
    #     self.meta['totalNoFrames'] += dataInc


    def calcStack(self, data):
        """  Calculates the stack from the data by summing its values.

        IMPORTANT: data needs to have second dimension. Even if it is just
        a vector otherwise ambiguity could arise
        :param data:
        :return:
        """
        if data.shape[1] > self.meta['maxClass']:
            self.meta['maxClass'] = data.shape[1]
        # return bsc.countInt(data.astype(np.int),
        #                     minLength=self.meta['maxClass'] + 1)[1:,1]
        return np.sum(data, axis=1)

    # @profile
    def convertFrameListToDataframe(self, anno, frameSlc, filtList):
        data = []
        if frameSlc.start is not None:
            frameOffset = frameSlc.start
        else:
            frameOffset = 0

        for filterTuple in filtList:
            filtAnno = anno.filterFrameList(filterTuple,
                                            frameRange=frameSlc,
                                            exactMatch=False)

            if not filtAnno.dataFrame.empty:
                # make sure that every minute starts with frame 0
                filtAnno.dataFrame.set_index(
                    filtAnno.dataFrame.index.set_levels(
                        np.asarray(filtAnno.dataFrame.index.levels[0]) -
                        frameOffset,
                        level=0), inplace=True)

            classID = self.getAnnotationFilterCode(filterTuple)
            cnt = filtAnno.countAnnotationsPerFrame()

            data += zip(range(len(cnt)), [classID] * len(cnt), cnt)

        if data != []:
            df = pd.DataFrame(data, columns=('frames', 'classID', 'amount'))
        else:
            df = pd.DataFrame(columns=('frames', 'classID', 'amount'))

        df.set_index(['frames', 'classID'], inplace=True)
        df.sortlevel(inplace=True)

        return df

        # # data = np.zeros((len(anno.frameList[frameSlc])))
        # data = dict()
        # for l in xrange(len(filtList)):
        #     filteredAnno = anno.filterFrameList(filtList[l],
        #                                         exactMatch=False)
        #
        #     for i in xrange(frameSlc.start, frameSlc.stop):
        #         if 'behaviour' in filteredAnno.frameList[i][0]:
        #             try:
        #                 data[i - frameSlc.start][l] = \
        #                     len(filteredAnno.frameList[i][0].keys())
        #             except KeyError:
        #                 # data[i - frameSlc.start] = \
        #                 #     np.zeros((self.meta['maxClass'], 1))
        #                 # data[i - frameSlc.start][l] = \
        #                 #     len(filteredAnno.frameList[i][0].keys())
        #
        #                 data[i - frameSlc.start] = \
        #                     {l: len(filteredAnno.frameList[i][0].keys())}
        #
        #             # if filtList[l].behaviours == ['test']:
        #             #     1/0
        #             # data[i - frameSlc.start] = l + 1
        #
        # return data

    def incrementTime(self, day, hour, minute):
        minute += 1
        if minute > 59:
            minute = 0
            hour += 1
            if hour > 23:
                hour = 0
                day += 1

        return day, hour, minute



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

    def importAnnotation(self, annotation, fps=30, annoFilters=None):
        if annoFilters is not None:
            for af in annoFilters:
                self.addNewClass(af)

        day = 0
        hour = 0
        minute = 0

        if annotation.getLength() <= fps * 60:
            frameSlc = slice(0, annotation.getLength())
            df = self.convertFrameListToDataframe(annotation, frameSlc,
                                                self.meta['filtList'])

            self.insertSample(day, hour, minute, df)
            self.meta['not-initialized'] = False
            return

        i = 0
        for k in xrange(fps * 60, annotation.getLength(), fps * 60):
            print k, day, hour, minute
            frameSlc = slice(i, k)
            df = self.convertFrameListToDataframe(annotation, frameSlc,
                                                self.meta['filtList'])

            self.insertSample(day, hour, minute, df)
            day, hour, minute = self.incrementTime(day, hour, minute)

            i = k

            self.meta['not-initialized'] = False


    # @profile
    def importAnnotationsFromSingleFile(self, bhvrFile,
                                        vials, runningIndeces=False, fps=30):
        # filtList = []
        # self.resetAllSamples()

        if os.path.exists(bhvrFile):
            anno = Annotation.Annotation()
            anno.loadFromFile(bhvrFile)

            self.importAnnotation(anno, fps)


    def importAnnotationsFromFile(self, bhvrList, videoList, annoFilters=None, vials=None,
                          runningIndeces=False, fps=30, singleFileMode=None):

        # filtList = []
        self.resetAllSamples()

        if len(videoList) == 1:
            self.createFDVTTemplateFromSingleVideoFile(videoList[0])
            self.meta['singleFileMode'] = True
        elif len(videoList) > 1:
            self.createFDVTTemplateFromVideoList(videoList, runningIndeces)
            self.meta['singleFileMode'] = False

        #
        # for i in range(len(annotations)):
        #     annotator = annotations[i]["annot"]
        #     behaviour = annotations[i]["behav"]
        #     self.addNewClass(Annotation.AnnotationFilter(vials,
        #                                                 [annotator],
        #                                                 [behaviour]))


        if annoFilters is not None:
            for af in annoFilters:
                self.addNewClass(af)

        if len(bhvrList) == 0:
            return

        if len(videoList) == 1:
            self.importAnnotationsFromSingleFile(bhvrList[0],
                                                 vials,
                                                 runningIndeces=False, fps=30)
            return

        # if len(filtList) == 0:
        #     return
            # raise ValueError("no annotations specified!")

        for f in bhvrList:
            if not os.path.exists(f):
                continue

            # load annotation and filter it #
            anno = Annotation.Annotation()

            anno.loadFromFile(f)

            if not runningIndeces:
                day, hour, minute, second = filename2Time(f)
            else:
                day, hour, minute, second = filename2TimeRunningIndeces(f)

            frameSlc = slice(0, anno.getLength())
            df = self.convertFrameListToDataframe(anno, frameSlc,
                                                self.meta['filtList'])

            if not df.empty:
                self.insertSample(day, hour, minute, df)
                self.meta['not-initialized'] = False




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
            if str(k) in (str(x) for x in stump.keys()):
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
            stump = self.getValues(day, hour, minute)#self.data[day][hour][minute]
        except KeyError:
            stump = None

        if not stump.empty:
            self.createStackData(self.plotData['frames'],
                                 stump,
                                 frameResolution)
        else:
            self.plotData['frames']['data'] = np.zeros((
                                    len(self.meta['rangeTemplate']['frames']) /
                                    frameResolution,
                                    self.meta['maxClass']))

    def df2minuteArray(self, df, frames_per_minute=1800):
        maxClass = self.meta['maxClass']

        ar = np.zeros((frames_per_minute, maxClass))

        for c in range(maxClass):
            try:
                df2 = df.loc[(slice(None, None), c), :]
            except KeyError:
                continue

            df3 = df2.reset_index()
            df3.set_index(['frames', 'classID'], inplace=True)
            frames = np.asarray(df3.index.levels[0])
            counts = np.asarray(df3)
            ar[frames, c] = counts.reshape(counts.shape[0],)

        return ar

    def createStackData(self, plotData, inData, frameResolution):
#         plotData = dict()
        plotData['data'] = []
        plotData['weight'] = []
        plotData['tick'] = []


        # if self.data == dict():
        #     plotData['data'] += [0]
        #     plotData['weight'] += [0]
        #     plotData['tick'] += [0]
        #     return

        data = self.df2minuteArray(inData)

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
        1/0
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


    ### functions to find next annotation occurrence

    def getFirstKey(self, stump):
        keys = [x for x in stump.keys() if x != 'meta']
        return sorted(keys)[0]


    def getLastKey(self, stump):
        keys = [x for x in stump.keys() if x != 'meta']
        return sorted(keys)[-1]


    def findNextMinuteWithAnnotationInStump(self, anno_id, stump, start_token, ge=False):
        for t in sorted(stump):
            if t == 'meta':
                continue

            if ge:
                if t >= start_token:
                    if stump[t]['meta']['stack'][anno_id] > 0:
                        return t
            else:
                if t > start_token:
                    if stump[t]['meta']['stack'][anno_id] > 0:
                        return t
        return None


    def findPrevMinuteWithAnnotationInStump(self, anno_id, stump, start_token, le=False):
        for t in sorted(stump, reverse=True):
            if t == 'meta':
                continue

            if le:
                if t <= start_token:
                    if stump[t]['meta']['stack'][anno_id] > 0:
                        return t
            else:
                if t < start_token:
                    if stump[t]['meta']['stack'][anno_id] > 0:
                        return t
        return None


    def findNextMinuteWithAnnotation(self, anno_id, day, hour, minute):
        try:
            next_min = self.findNextMinuteWithAnnotationInStump(
                                                        anno_id,
                                                        self.hier[day][hour],
                                                        minute)
        except KeyError:
            next_min = None

        if next_min is None:
            next_hour = self.findNextMinuteWithAnnotationInStump(
                                                            anno_id,
                                                            self.hier[day],
                                                            hour)
            print next_hour
            if next_hour is None:
                next_day = self.findNextMinuteWithAnnotationInStump(
                                                               anno_id,
                                                               self.hier,
                                                               day)
                if next_day is None:
                    return None

                next_hour = self.findNextMinuteWithAnnotationInStump(
                                        anno_id,
                                        self.hier[next_day],
                                        self.getFirstKey(self.hier[next_day]),
                                        ge=True)
            else:
                next_day = day

            next_min = self.findNextMinuteWithAnnotationInStump(
                                        anno_id,
                                        self.hier[next_day][next_hour],
                                        self.getFirstKey(
                                            self.hier[next_day][next_hour]),
                                        ge=True)
        else:
            next_hour = hour
            next_day = day

        return next_day, next_hour, next_min


    def findPrevMinuteWithAnnotation(self, anno_id, day, hour, minute):
        try:
            prev_min = self.findPrevMinuteWithAnnotationInStump(
                                                       anno_id,
                                                       self.hier[day][hour],
                                                       minute)
        except KeyError:
            prev_min = None

        if prev_min is None:
            prev_hour = self.findPrevMinuteWithAnnotationInStump(
                                                            anno_id,
                                                            self.hier[day],
                                                            hour)
            if prev_hour is None:
                prev_day = self.findPrevMinuteWithAnnotationInStump(
                                                               anno_id,
                                                               self.hier,
                                                               day)
                if prev_day is None:
                    return None

                prev_hour = self.findPrevMinuteWithAnnotationInStump(
                                            anno_id,
                                            self.hier[prev_day],
                                            self.getLastKey(
                                                        self.hier[prev_day]),
                                            le=True)
            else:
                prev_day = day


            prev_min = self.findPrevMinuteWithAnnotationInStump(
                                        anno_id,
                                        self.hier[prev_day][prev_hour],
                                        self.getLastKey(
                                            self.hier[prev_day][prev_hour]),
                                        le=True)
        else:
            prev_hour = hour
            prev_day = day

        return prev_day, prev_hour, prev_min


    def getRangeSections(self, rng):
        """
        using
        http://stackoverflow.com/a/7353335
        and
        http://stackoverflow.com/questions/7088625/what-is-the-most-efficient-way-to-check-if-a-value-exists-in-a-numpy-array
        """

        return np.array_split(rng, np.where(np.diff(rng)!=1)[0]+1)


    def findNextFrameWithAnnotation(self, anno_id, day, hour, minute, frame):
        df = self.getValues(day, hour, minute)

        locations = np.where(self.df2minuteArray(df)[:, anno_id])[0]
        sections = self.getRangeSections(locations)

        if sections[0].size == 0:
            return None

        for section in sections:
            if frame in section:
                continue

            if np.all(section > frame):
                return section[0]

        return None


    def findPrevFrameWithAnnotation(self, anno_id, day, hour, minute, frame):
        df = self.getValues(day, hour, minute)

        locations = np.where(self.df2minuteArray(df)[:, anno_id])[0]
        sections = self.getRangeSections(locations)

        if sections[0].size == 0:
            return None

        for section in reversed(sections):
            if frame in section:
                continue

            if np.all(section < frame):
                return section[-1]

        return None


    def incrementTimeUsingTemplate(self, day, hour, minute):
        new_hour = hour
        new_day = day

        minute_idx = sorted(self.meta['rangeTemplate']['minutes']).index(minute)
        if minute_idx == len(self.meta['rangeTemplate']['minutes']) - 1:
            new_minute = sorted(self.meta['rangeTemplate']['minutes'])[0]

            hour_idx = sorted(self.meta['rangeTemplate']['hours']).index(hour)

            if hour_idx == len(self.meta['rangeTemplate']['hours']) - 1:
                new_hour = sorted(self.meta['rangeTemplate']['hours'])[0]
                day_idx = sorted(self.meta['rangeTemplate']['days']).index(day)

                if day_idx == len(self.meta['rangeTemplate']['days']) - 1:
                    return None, None, None
                else:
                    new_day = sorted(self.meta['rangeTemplate']['days'])[day_idx + 1]
            else:
                new_hour = sorted(self.meta['rangeTemplate']['hours'])[hour_idx + 1]
        else:
            new_minute = sorted(self.meta['rangeTemplate']['minutes'])[minute_idx + 1]

        return new_day, new_hour, new_minute


    def decrementTimeUsingTemplate(self, day, hour, minute):
        new_hour = hour
        new_day = day

        minute_idx = sorted(self.meta['rangeTemplate']['minutes']).index(minute)
        if minute_idx == 0:
            new_minute = sorted(self.meta['rangeTemplate']['minutes'])[-1]

            hour_idx = sorted(self.meta['rangeTemplate']['hours']).index(hour)

            if hour_idx == 0:
                new_hour = sorted(self.meta['rangeTemplate']['hours'])[-1]
                day_idx = sorted(self.meta['rangeTemplate']['days']).index(day)

                if day_idx == 0:
                    return None, None, None
                else:
                    new_day = sorted(self.meta['rangeTemplate']['days'])[day_idx - 1]
            else:
                new_hour = sorted(self.meta['rangeTemplate']['hours'])[hour_idx - 1]
        else:
            new_minute = sorted(self.meta['rangeTemplate']['minutes'])[minute_idx - 1]

        return new_day, new_hour, new_minute


    def findNextAnnotation(self, anno_id, day, hour, minute, frame):
        next_frame = self.findNextFrameWithAnnotation(anno_id, day, hour,
                                                      minute, frame)

        if next_frame is None:
            next_day, next_hour, next_minute = \
                                    self.incrementTimeUsingTemplate(day,
                                                                    hour,
                                                                    minute)

            if next_day is None:
                return None

            res = self.findNextMinuteWithAnnotation(anno_id, next_day,
                                                    next_hour, next_minute)

            if res is None:
                return None

            day, hour, minute = res

            res = self.findNextFrameWithAnnotation(anno_id, day,
                                                   hour, minute, -1)

            if res is None:
                return None
            else:
                return day, hour, minute, res

        return day, hour, minute, next_frame


    def findPrevAnnotation(self, anno_id, day, hour, minute, frame):
        prev_frame = self.findPrevFrameWithAnnotation(anno_id, day,
                                                      hour, minute, frame)

        if prev_frame is None:
            prev_day, prev_hour, prev_minute = \
                                    self.decrementTimeUsingTemplate(day,
                                                                    hour,
                                                                    minute)
            if prev_day is None:
                return None

            res = self.findPrevMinuteWithAnnotation(anno_id, prev_day,
                                                    prev_hour, prev_minute)

            if res is None:
                return None

            day, hour, minute = res

            res = self.findPrevFrameWithAnnotation(anno_id, day, hour, minute,
                          sorted(self.meta['rangeTemplate']['frames'])[-1] + 1)

            if res is None:
                return None
            else:
                return day, hour, minute, res

        return day, hour, minute, prev_frame