__author__ = 'peter'

import numpy as np
import scipy.misc as spm
import matplotlib.pyplot as plt
import os
import pyTools.system.videoExplorer as VE
import pyTools.videoProc.backgroundModel as BM
import time
import pyTools.batch.vials as V
import pyTools.imgProc.imgViewer as IV
from sklearn.externals import joblib
import skimage
import pyTools.libs.faceparts.vanillaHogUtils as vanHog

def computeHog(patch):
    img = skimage.color.rgb2gray(patch)
    a = list(skimage.transform.pyramid_gaussian(img, sigma=2,
                                                    max_layer=1))
    return vanHog.hog(a[1], 9,3, 360, [0, 64, 0, 64])


class backgroundPrecompute(object):
    def __init__(self, flyClassifier, noveltyClassfy, targetFolder=None):
        self.rois = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
        self.v = V.Vials(self.rois, gaussWeight=2000, sigma=20,  xoffsetFact=0.6)
        self.iV = IV.imgViewer()
        self.vE = VE.videoExplorer()
        self.update = None
        self.bgImg = None
        self.wasUpdated = [False for i in range(4)]
        self.diffImg = None
        self.frame = None
        self.clfyFunc = lambda patch: np.min(patch.flatten()) < -250
        self.bgModel = BM.backgroundModel(verbose=True, colorMode='rgb')
        if targetFolder is None:
            self.targetFolder = "/tmp/backgrounds/"
        else:
            self.targetFolder = targetFolder


        self.noveltyClassfy = noveltyClassfy
        self.flyClassifier = flyClassifier




    def updateBackgroundMask(self, update, vialNo, center, patchSize):
        mask = self.v.createBackgroundUpdateMask(self.frame, vialNo, center, patchSize)

        if self.update is None:
            self.update = self.bgImg.createUpdatedBgImg(self.frame, mask)
            self.wasUpdated = [False] * len(self.rois)
            self.wasUpdated[vialNo] = True
        else:
            if self.wasUpdated[vialNo] is not True:
                self.update[mask == 1] = self.frame[mask == 1]
                self.wasUpdated[vialNo] = True



    def checkForBackgroundUpdate(self, pos, i, patchSize=[64,64]):
        patch = self.iV.extractPatch(self.diffImg, pos, patchSize)

        if self.clfyFunc(patch):
            self.updateBackgroundMask(self.bgImg, i, pos, [300, 100])


    def acceptPosFunc(self, diffImg, startPos, vialNo, img, plotIterations, retIt, args):
        computeHog = args['computeHog']
        noveltyClassfy = args['noveltyClassfy']
        flyClassify = args['flyClassify']

        for i in range(2):
            initPos = self.v.localizeFly(diffImg, startPos, img=img,
                                                plotIterations=plotIterations, retIt=retIt)

            diffPatch = self.iV.extractPatch(diffImg, [initPos[0], initPos[1]], [64, 64])
            if np.min(diffPatch) > -40:
                if not np.allclose(diffPatch.shape, [64, 64]):
                    # patch is outside of the image
                    print "patch outside of image"
                    continue

                patch = self.iV.extractPatch(img, [initPos[0], initPos[1]], [64, 64])
                hog = computeHog(patch)

                if np.isnan(np.sum(hog.flatten())):
                    # happens if all values in patch are low(?)
                    # whatever it is, it will not represent a fly
                    continue

                if not(noveltyClassfy.predict(hog) == 1):
                    # hog features were not modelled, very likely to be background
                    continue

                if not(flyClassify is 1):
                    # position is valid
                    return initPos

                # do minimum suppresion
                diffImg[initPos[0]-32:initPos[0]+32, initPos[1]-32:initPos[1]+32] = 0
                startPos = self.getVialMinGlobal(diffImg)[vialNo]
            else:
                return initPos

        # return default position
        return [33, 33]



    def extractFlyPatch(self, pos, i):
        p = pos[i]
        acceptArgs = {'computeHog': computeHog,
                      'noveltyClassfy': self.noveltyClassfy,
                      'flyClassify': self.flyClassifier}

        actPos = self.acceptPosFunc(diffImg=self.diffImg, startPos=p, vialNo=i, img=self.frame,
                               plotIterations=None, retIt=None,
                               args=acceptArgs)

        if not self.wasUpdated[i]:
            self.checkForBackgroundUpdate(actPos, i)

        return actPos



    def getFlyPatches(self, f):
        self.frame = self.vE.getFrame(f, frameMode='RGB')
        self.setBackgroundImage(self.bgModel.getBgImg(self.frame))
        self.diffImg = self.bgImg.subtractStack(self.frame)
        initPos = self.v.getVialMinGlobal(self.diffImg)
        for i in range(len(initPos)):
            self.extractFlyPatch(initPos, i)


    def updateBackground(self, fileList):
        self.wasUpdated = [False for i in range(4)]
        for f in fileList:
            self.getFlyPatches(f[1])

    def resetUpdate(self):
        self.update = None
        self.wasUpdated = [False for i in range(len(self.rois))]

    def saveBackgroundModel(self, baseFilename):
        self.updateCnt = 0
        if self.update is not None:
            self.bgImg.updateBackgroundModel(self.update)

            print "update backgroundmodel v0: {0} --  v1: {1} --  v2: {2} --  v3: {3} -- ".format(self.wasUpdated[0],
                                         self.wasUpdated[1],
                                         self.wasUpdated[2],
                                         self.wasUpdated[3])
        else:
            #arcane procedure stolen from self.bgImg.updateBackgroundModel
            self.update = np.zeros(tuple(self.frame.shape), dtype=np.uint8)

            if len(self.update.shape) > 2:
                for i in range(self.update.shape[2]):
                    self.update[:,:,i] = self.bgImg.bgStack[i][self.bgImg.stackIdx, :].reshape(tuple(self.frame.shape[:2]))
            else:
                self.update[:,:] = self.bgImg.bgStack[self.bgImg.stackIdx, :].reshape(tuple(self.frame.shape))

        if self.targetFolder is not None:
            bgFilename = self.createBackgroundFilename(baseFilename)
            plt.imsave(bgFilename.format(self.wasUpdated[0],
                                         self.wasUpdated[1],
                                         self.wasUpdated[2],
                                         self.wasUpdated[3]),
                        self.update)

        self.resetUpdate()

        bgImg = self.bgModel.getBgImg(self.frame)

        if bgImg is not self.bgImg:
            self.setBackgroundImage(bgImg)


    def createBackgroundFilename(self, baseFilename):
        # strip baseFilename of .mp4 ending
        bgFilename = os.path.basename(baseFilename[1])[:-4]
        baseFolder =  V.constructSaveDir(self.targetFolder,
                                        baseFilename[1])
        bgFilename = os.path.join(baseFolder, "bg", bgFilename)
        bgFilename += '-bg-{0}-{1}-{2}-{3}.png'
        if not os.path.exists(os.path.dirname(bgFilename)):
            os.makedirs(os.path.dirname(bgFilename))

        return bgFilename


    def generateBackgrounds(self, fileList, N=5):
        print "generating backgrounds..."
        for i in range(0, len(fileList), N):
            start = i
            self.updateBackground(fileList[start: start + N])
            if start + N > len(fileList):
                self.saveBackgroundModel(fileList[len(fileList)-1])
            else:
                self.saveBackgroundModel(fileList[start+N])
            print "saving {end}".format(end=start+N)


    def parseVideofiles(self, folder):
        fileList = []
        for root,  dirs,  files in os.walk(folder):
            for fn in files:
                fileDT = self.vE.fileName2DateTime(fn)

                if fileDT == -1:
                    ## file is no mp4 file of interest
                    continue

                fileList.append([fileDT, root + r'/' + fn])

        return sorted(fileList)


    def setBackgroundImage(self, bgImg):
        if bgImg != []:
            bgFunc = bgImg.backgroundSubtractionWeaverF
            bgImg.configureStackSubtraction(bgFunc)
            self.bgImg = bgImg
            self.resetUpdate()

    def configureBackgroundModel(self, folder, start, stop):
        self.bgModel = BM.backgroundModel(verbose=True, colorMode='rgb')
        self.bgModel.getVideoPaths(folder, start, stop)
        self.bgModel.createDayModel(sampleSize=10)
        self.bgModel.createNightModel(sampleSize=10)
        self.setBackgroundImage(self.bgModel.modelNight)
        self.setBackgroundImage(self.bgModel.modelDay)


    def generateRecordingRanges(self, folder):
        fileList = self.parseVideofiles(folder)
        recRngs = self.vE.findInteruptions(fileList)
        return fileList, recRngs

    def computeBackgroundFromFolder(self, folder, idx=None):
        fileList, recRngs = self.generateRecordingRanges(folder)
        rngStart = 0
        if  idx is not None:
            recRngs = [recRngs[idx]]

        for recRng in recRngs:
            self.configureBackgroundModel(folder, recRng[0], recRng[1])
            self.generateBackgrounds(fileList[rngStart:recRng[2]])
            rngStart = recRng[2]


##############################################################################

def generateConfigFile(configPath, flyClassifierPath, noveltyClassfyPath,
                       sourceFolder, targetFolder):
    bP = backgroundPrecompute(None, None, targetFolder=None)
    fileList, recRngs = bP.generateRecordingRanges(sourceFolder)

    configs = []
    baseString = "{idx} {clfPath} {novPath} {src} {target}\n"

    for i in range(len(recRngs)):
        configs += [baseString.format(idx=i,
                                     clfPath=flyClassifierPath,
                                     novPath=noveltyClassfyPath,
                                     src=sourceFolder,
                                     target=targetFolder)]

    if not os.path.exists(os.path.dirname(configPath)):
        os.makedirs(os.path.dirname(configPath))

    with open(configPath, "w") as f:
        f.writelines(configs)


##############################################################################

if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('videoIndex', metavar='i', type=int,
                       help='index to the section (between changing the vials) in the videos this script is going to estimate the background')
    parser.add_argument('flyClassifierPath', metavar='f',
                       help='path to fly classifier')
    parser.add_argument('noveltyClassfyPath', metavar='n',
                       help='path to novelty classifier')
    parser.add_argument('sourceFolder', metavar='s',
                       help='path to folder containing video files')
    parser.add_argument('targetFolder', metavar='t',
                       help='path to target folder where background images are going to be saved in')

    args = parser.parse_args()

    flyClassifierPath = args.flyClassifierPath
    noveltyClassfyPath = args.noveltyClassfyPath

    flyClassifier = joblib.load(flyClassifierPath)
    noveltyClassfy = joblib.load(noveltyClassfyPath)

    folder = args.sourceFolder
    targetFolder = args.targetFolder
    idx = args.videoIndex

    bP = backgroundPrecompute(flyClassifier, noveltyClassfy, targetFolder=targetFolder)
    bP.computeBackgroundFromFolder(folder, idx)