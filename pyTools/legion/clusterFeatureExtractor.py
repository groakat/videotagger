__author__ = 'peter'
import os
from collections import namedtuple, OrderedDict
import copy
import numpy as np

featureDesc = namedtuple("featureDescription", ['path', 'ext'])

class featureFilter(object):
    def __init__(self, baseFolder, featureLst):
        self.baseFolder = baseFolder
        if not type(featureLst) == list:
            featureLst = [featureLst]

        self.vialIdces = [0,1,2,3]
        self.filelists = []
        self.featureLst = featureLst

        self.prepareFilelist()
        self.scanForFeatures()

    def prepareFilelist(self):
        self.filelists = []

        for v in self.vialIdces:
            self.filelists += {}
            for featDesc in self.featureLst:
                self.filelists[v][featDesc] = []

    def scanForFeatures(self):
        self.prepareFilelist()

        for root, dirs, files in os.walk(self.baseFolder):
            for f in files:
                for featDesc in self.featureLst:
                    if root.endswith(featDesc.path) \
                    and f.endswith(featDesc.ext):
                        vialNo = int(f[-(len(featDesc.ext) + 1)])
                        self.filelists[vialNo][featDesc] += [os.path.join(root, f)]


class ClusterFeatureExtratorBase(object):
    def __init__(self, baseFolder, featureLst, targetFeat, startIdx, stopIdx, params=None, overlap=[0,0]):
        """
        param has to be an collections.OrderedDict
        """
        self.baseFolder = baseFolder
        if not type(featureLst) == list:
            featureLst = [featureLst]

        self.featureLst = featureLst
        self.targetFeat = targetFeat
        self.lstRange = range(startIdx, stopIdx)
        self.overlap = overlap
        self.vialIdces = [0,1,2,3]

        if params is None:
            params = {}

        self.params = params

        self.ff = featureFilter(baseFolder, featureLst)


    def splitFolders(self, path):
        splits = []
        while path != '/' and path:
            path, folder = os.path.split(path)
            splits += [folder]

        splits.reverse()
        return splits

    def constructSaveDir(self, baseSaveDir, filename, featPath, appendix):
        folders = self.splitFolders(filename)
        fpl = len(self.splitFolders(featPath))

        if type(appendix) == list:
            baseFolder = os.path.join(baseSaveDir, folders[-3-fpl], folders[-2-fpl], *appendix)
        else:
            baseFolder = os.path.join(baseSaveDir, folders[-3-fpl], folders[-2-fpl], appendix)

        if not os.path.exists(baseFolder):
            os.makedirs(baseFolder)

        return baseFolder


    def createFeatureSavePath(self, i):
        srcFilename = self.ff.filelists[self.featureLst[0]][i]
        featPath = self.featureLst[0].path

        dirname = self.constructSaveDir(self.baseFolder, srcFilename, featPath, self.targetFeat.path)
        basename = os.path.basename(self.ff.filelists[self.featureLst[0]][i])
        basename = basename[:-len(self.featureLst[0].ext)]
        basename += self.targetFeat.ext

        return os.path.join(dirname, basename)



    def extractFeatures(self):
        filelistLength = len(self.ff.filelists[self.featureLst[0]])
        for i in self.lstRange:
            paths = []
            rng = slice(i-self.overlap[0], i + 1 +self.overlap[1])
            loc = slice(-self.overlap[0], self.overlap[1] + 1)
            if rng.start < 0:
                rng = slice(0, rng.stop)
                loc = slice(0, loc.stop)
            if rng.stop >= filelistLength:
                stop = rng.stop - filelistLength
                loc = slice(loc.start, loc.stop - stop)

            for featDesc in self.featureLst:
                paths += [self.ff.filelists[featDesc][rng]]

            feat = self.calculateFeatures(paths, loc, **self.params)
            filename = self.createFeatureSavePath(i)

            np.save(filename, feat)

    ############## CFG #################################
    def getNumberOfFiles(self):
        return len(self.ff.filelists[self.featureLst[0]])

    def generateBaseString(self):
        baseString = '{0} {1} {2} {3}'
        params = copy.copy(self.params)
        while params:
            baseString += " {{{0}}}".format(params.popitem(last=False)[0])

        baseString += '\n'

        return baseString

    def generateScriptConfigString(self, noPerBatch):
        nf = self.getNumberOfFiles()
        cfgString = ''
        baseString = self.generateBaseString()

        cnt = 0
        for i in range(0, nf, noPerBatch):
            if i + noPerBatch > nf:
                stop = nf
            else:
                stop = i + noPerBatch
            cfgString += baseString.format(cnt,
                                           i,
                                           stop,
                                           self.baseFolder,
                                           **self.params)
            cnt += 1

        return cfgString



    def generateConfig(self, filename, noPerBatch=100):
        cfgString = self.generateScriptConfigString(noPerBatch)
        with open(filename, "w") as f:
            f.write(cfgString)


    ############## VIRTUAL FUNCTIONS ###################
    def calculateFeatures(self, paths, loc, **params):
        print paths
        print loc
        print params
        return np.zeros((10,1))



