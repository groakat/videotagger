
import numpy as np
import pyTools.system.videoExplorer as VE
import pyTools.videoProc.backgroundModel as BG
import pyTools.imgProc.imgViewer as IV
import pyTools.batch.vials as V
import pyTools.misc.basic as bsc
import time
import datetime as dt
import subprocess
from sklearn.externals import joblib
import getpass
import smtplib
import ast
import logging
from StringIO import *
import os

import pyTools.libs.faceparts.vanillaHogUtils as vanHog
from skimage.color import rgb2gray
import skimage.transform


class FlyExtractor(object):

    def __init__(self, videoFolder, backgroundFolder, patchFolder, flyClassifierPath, noveltyClassfyPath,
                 recIdx, runIdx, minPerRun=20, ffmpegpath=None):

        self.flyClassifierPath = flyClassifierPath
        self.noveltyClassfyPath = noveltyClassfyPath
        self.setupFlyClassifiers()


        self.vE = VE.videoExplorer()
        self.bgModel = BG.backgroundModel(verbose=False, colorMode='rgb')
        self.viewer = IV.imgViewer()
        self.roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
        self.vial = V.Vials(self.roi, gaussWeight=2000, sigma=20,
                            xoffsetFact=0.6, clfyFunc=self.flyClassify,
                            acceptPosFunc=V.Vials.acceptPosFunc,
                            acceptPosFuncArgs=self.acceptArgs, ffmpegpath=ffmpegpath)

        self.bgModel = BG.backgroundModel(verbose=False, colorMode='rgb')

        self.videoFolder = videoFolder
        self.backgroundFolder = backgroundFolder
        self.patchFolder = patchFolder
        self.recIdx = recIdx
        self.recIdx = recIdx
        self.minPerRun = minPerRun
        self.runIdx = runIdx
        self.bgSampleSize = 10


    def computeHog(self, patch):
        img = skimage.color.rgb2gray(patch)
        a = list(skimage.transform.pyramid_gaussian(img, sigma=2,
                                                        max_layer=1))
        return vanHog.hog(a[1], 9,3, 360, [0, 64, 0, 64])

    def setupFlyClassifiers(self):

        self.flyClassifier = joblib.load(self.flyClassifierPath)
        self.noveltyClassfy = joblib.load(self.noveltyClassfyPath)

        self.flyClassify = lambda patch: V.Vials.checkIfPatchShowsFly(patch, self.flyClassifier, flyClass=1, debug=True)

        self.acceptArgs = {'computeHog': self.computeHog,
                      'noveltyClassfy': self.noveltyClassfy,
                      'flyClassify': self.flyClassify}


    def parseVideofiles(self, folder):
        fileList = []
        for root,  dirs,  files in os.walk(folder):
            for fn in files:
                fileDT = self.vE.fileName2DateTime(fn)

                if fileDT == -1:
                    ## file is no mp4 file of interest
                    continue

                fileList.append([fileDT, root + r'/' + fn])

        fileList =  sorted(fileList)
        return fileList


    def generateRecordingRanges(self, folder):
        fileList = self.parseVideofiles(folder)
        recRngs = self.vE.findInteruptions(fileList)
        self.recRngs = recRngs
        return recRngs


    def filterFileList(self):
        self.startDate, self.endDate = self.generateDateRange()

        self.vE.setRootPath(self.videoFolder)
        self.vE.setTimeRange(self.startDate,  self.endDate)

        self.vE.parseFiles()

        self.fileList = self.vE.getPathsOfList(self.vE.dayList)
        self.fileList += self.vE.getPathsOfList(self.vE.nightList)
        self.fileList = sorted(self.fileList)


    def getSubfolder(self, path):
        path, folder = os.path.split(path)
        if folder == '':
            path, folder = os.path.split(path)

        return folder

    def filterBackgroundDates(self, folder):
        self.nightBackgrounds = []
        self.dayBackgrounds = []
        for root, dirs, files in os.walk(folder):
            for f in sorted(files):
                if self.getSubfolder(root) == "bg":
                    if f.endswith(".png"):
                        bgPath = os.path.join(root, f)
                        bgDate = self.vE.fileName2DateTime(bgPath,
                                                ending=os.path.basename(bgPath)[19:])
                        hour = bgDate.hour
                        if hour >= 10 and hour < 23:
                            self.dayBackgrounds += [[bgPath, bgDate]]
                        else:
                            self.nightBackgrounds += [[bgPath, bgDate]]

        self.nightBackgrounds = sorted(self.nightBackgrounds)
        self.dayBackgrounds = sorted(self.dayBackgrounds)


    def selectClosestBackgroundFileIdx(self, videoFile):
        videoDate = self.vE.fileName2DateTime(videoFile)

        hour = videoDate.hour
        if hour >= 10 and hour < 23:
            backgrounds = self.dayBackgrounds
        else:
            backgrounds = self.nightBackgrounds

        rng = range(len(backgrounds))
        while rng:
            rngCenter = int(np.floor(len(rng) / 2))
            idx = rng[rngCenter]
            if backgrounds[idx][1] > videoDate:
                rng = rng[:rngCenter]
            elif backgrounds[idx][1] < videoDate:
                rng = rng[rngCenter+1:]
            else:
                return idx

        return idx


    def generateDateRange(self, increment=0):
        if self.runIdx + increment < 0:
            return False

        startTimeD = dt.timedelta(minutes=self.minPerRun * self.runIdx)
        stopTimeD = dt.timedelta(minutes=self.minPerRun * self.runIdx + self.minPerRun)

        startDate = self.recRngs[self.recIdx + increment][0] + startTimeD
        stopDate = self.recRngs[self.recIdx + increment][0] + stopTimeD

        return [startDate, stopDate]


    def setupBasicBackgroundModel(self):
        start, end, _ = self.recRngs[self.recIdx]
        self.bgModel.getVideoPaths(self.videoFolder, start,  end)
        self.bgModel.createDayModel(self.bgSampleSize)
        self.bgModel.createNightModel(self.bgSampleSize)


    def getNightList(self):
        nightPaths = sorted(self.bgModel.vE.nightList)
        if nightPaths:
            nightPath = nightPaths[0]
        else:
            return []
        idx = self.selectClosestBackgroundFileIdx(nightPath[1])

        if idx - self.bgSampleSize > 0:
            s = idx - self.bgSampleSize
        else:
            s = 0
        return self.nightBackgrounds[s:idx]


    def getDayList(self):
        dayPaths = sorted(self.bgModel.vE.dayList)
        if dayPaths:
            dayPath = dayPaths[0]
        else:
            return []
        idx = self.selectClosestBackgroundFileIdx(dayPath[1])

        if idx - self.bgSampleSize > 0:
            s = idx - self.bgSampleSize
        else:
            s = 0
        return self.dayBackgrounds[s:idx]


    def loadBGImagesIntoBackgroundModel(self):
        self.setupBasicBackgroundModel()

        ret = self.generateDateRange(-1)
        if not ret:
            # there are no background images to add to the standard model
            print("no update")
            return
        else:
            startDate, stopDate = ret

        self.bgModel.getVideoPaths(self.videoFolder, startDate, stopDate)

        dayList = self.getDayList()
        nightList = self.getNightList()
        bgList = zip(*(dayList + nightList))[0]

        print("dates", startDate, stopDate)
        print("nightlist", nightList)
        print("dayList", dayList)
        self.bgModel.updateModelWithBgImages(bgList)

    def generateBackgroundModel(self):
        self.filterBackgroundDates(self.backgroundFolder)
        self.loadBGImagesIntoBackgroundModel()

    def extractPatches(self):
        self.generateRecordingRanges(self.videoFolder)
        if self.checkIfSectionWasProcessed(self.recIdx, self.runIdx):
            return

        self.generateBackgroundModel()
        self.filterFileList()
        print(self.fileList)
        self.vial.extractPatches(self.fileList, self.bgModel, baseSaveDir=self.patchFolder)



############## CFG
    def checkIfOutputExists(self, videoPath):
        f = videoPath

        patchFolder = V.constructSaveDir(self.backgroundFolder, f, "patches")
        posFolder = V.constructSaveDir(self.backgroundFolder, f, ["feat", "pos"])

        res = True
        for k in range(4):
            v1baseName = os.path.join(patchFolder, os.path.basename(f)[:-4] + ".v{v}.avi".format(v=k))
            v2baseName = os.path.join(patchFolder, os.path.basename(f)[:-4] + ".v{v}.mp4".format(v=k))
            p1baseName = os.path.join(posFolder, os.path.basename(f)[:-4] + ".v{v}.pos".format(v=k))
            p2baseName = os.path.join(posFolder, os.path.basename(f)[:-4] + ".v{v}.pos.npy".format(v=k))

            res = res and os.path.exists(v1baseName)
            res = res and os.path.exists(v2baseName)
            res = res and os.path.exists(p1baseName)
            res = res and os.path.exists(p2baseName)

        return res

    def checkIfSectionWasProcessed(self, recIdx, runIdx):
        self.runIdx = runIdx
        self.recIdx = recIdx
        self.filterFileList()

        res = True
        for f in self.fileList:
            res = res and self.checkIfOutputExists(f)

            if not res:
                break

        return res



    def retrieveScriptList(self):
        recCfgList = []
        for i in range(len(self.recRngs)):
            recRng = self.recRngs[i]
            if (recRng[1] - recRng[0]) > dt.timedelta(minutes=10):
                timeDiff = recRng[1] - recRng[0]
                seconds = timeDiff.total_seconds() / 60 / self.minPerRun
                for k in range(int(np.ceil(seconds))):
                    recCfgList += [[i, k]]



        return recCfgList


    def generateScriptConfigString(self, recCfgList,redoAll):
        baseString = "{i} {vf} {bf} {pf} {fcp} {ncp} {recIdx} {runIdx} {mpr}\n"
        cfgString = ""
        cnt = 0
        for recIdx, runIdx in recCfgList:
            if not redoAll:
                if self.checkIfSectionWasProcessed(recIdx, runIdx):
                    continue

            cfgString += baseString.format(i=cnt,
                                           vf=self.videoFolder,
                                           bf=self.backgroundFolder,
                                           pf=self.patchFolder,
                                           fcp=self.flyClassifierPath,
                                           ncp=self.noveltyClassfyPath,
                                           recIdx=recIdx,
                                           runIdx=runIdx,
                                           mpr=self.minPerRun)
            cnt += 1

        return cfgString

    def generateConfig(self, filename, redoAll=False):
        self.generateRecordingRanges(self.videoFolder)
        recCfgList = self.retrieveScriptList()
        cfgString = self.generateScriptConfigString(recCfgList, redoAll)
        with open(filename, "w") as f:
            f.write(cfgString)




if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('videoFolder', metavar='v',
                       help='folder containing the video files')
    parser.add_argument('backgroundFolder', metavar='b',
                       help='folder contain the background files')
    parser.add_argument('patchFolder', metavar='n',
                       help='folder where patches are going to be saved to')
    parser.add_argument('flyClassifierPath', metavar='f',
                       help='path to fly classifier')
    parser.add_argument('noveltyClassfyPath', metavar='o',
                       help='path to novelty classifier')
    parser.add_argument('recIdx', metavar='r', type=int,
                       help='index of recording batch (vial exchange) the script is to run on')
    parser.add_argument('runIdx', metavar='i', type=int,
                       help='index of the batch within the recording batch the script is to run on')
    parser.add_argument('minPerRun', metavar='m', type=int,
                       help='coverage of each run')

    args = parser.parse_args()

    videoFolder = args.videoFolder
    backgroundFolder = args.backgroundFolder
    patchFolder = args.patchFolder
    flyClassifierPath = args.flyClassifierPath
    noveltyClassfyPath = args.noveltyClassfyPath
    recIdx = args.recIdx
    runIdx = args.runIdx
    minPerRun = args.minPerRun


    fe = FlyExtractor(videoFolder, backgroundFolder, backgroundFolder, flyClassifierPath, noveltyClassfyPath,
                      recIdx=recIdx, runIdx=runIdx, minPerRun=minPerRun, ffmpegpath='~/usr/bin/ffmpeg')
    fe.extractPatches()
