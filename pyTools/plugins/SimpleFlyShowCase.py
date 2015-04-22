import pyTools.system.plugins as P
import os
import numpy as np
import pyTools.features.trajectory.Burgos as B
import pyTools.videoProc.annotation as A
from sklearn.ensemble import RandomForestClassifier as RFC
import pyTools.misc.FrameDataVisualization2 as FDV


class SimpleFlyShowCase(P.ClassificationPluginBase):

    def __init__(self, *args, **kwargs):
        super(SimpleFlyShowCase, self).__init__(*args, **kwargs)
        self.classifier = None

    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = P.MetaData(name='Simple Trajectory Classifier',
                        description='Simple Plugin to show how to implement interfaces using simple trajectory features')
        return meta

    def rel2absFile(self, relFile):
        return  os.path.join(self.rootFolder, relFile)

    def generateFeatureSavePath(self, trajPath):
        posFolder = os.path.dirname(trajPath)
        currentRootFolder = posFolder[:-len(self.positionFolder)]
        generalFeatFolder = os.path.join(currentRootFolder,
                                         self.featureFolder)
        trajFeatFolder = os.path.join(self.rootFolder,
                                      generalFeatFolder,
                                      'burgos')
        if not os.path.exists(trajFeatFolder):
            os.makedirs(trajFeatFolder)

        trajFeatFile = os.path.join(trajFeatFolder,
                                    os.path.basename(trajPath))

        trajFeatFile = trajFeatFile[:-len('.pos.npy')] + '.burgos.npy'
        return trajFeatFile


    def convertVideoToAnnoFilename(self, videoFile):
        bn = os.path.basename(videoFile)[:-4] + '.bhvr'
        baseFolder = os.path.dirname(videoFile)[:-len(self.videoFolder)]
        annoFile = os.path.join(baseFolder,
                                self.annotationFolder,
                                bn)
        return annoFile

    def convertAnnoToVideoFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-5] + self.videoListRel[0][-4:]
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        videoFile = os.path.join(baseFolder,
                                self.videoFolder,
                                bn)

        return videoFile

    def convertAnnoToFeatFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-5] + '.burgos.npy'
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(baseFolder,
                                self.featureFolder,
                                'burgos',
                                bn)

        return featFile

    def extractFeatures(self):
        """
        Iteration over video file to extract features
        :return:
        """
        self.setStatus("extracting features..", len(self.videoListRel))
        prevTraj = None
        currentTraj = np.load(os.path.join(self.rootFolder,
                                           self.posListRel[0]))
        nextTraj = np.load(os.path.join(self.rootFolder,
                                           self.posListRel[1]))

        traj = np.zeros((currentTraj.shape[0] + 1, currentTraj.shape[1]),
                        dtype=currentTraj.dtype)

        traj[:-1] = currentTraj
        traj[-1] = nextTraj[0]

        feat = B.generateTrajFeatures(traj,
                                      dt=currentTraj.shape[0]/1000.0)[:-1]
        np.save(self.generateFeatureSavePath(self.posListRel[0]), feat)

        prevTraj = currentTraj
        currentTraj = nextTraj


        for i in range(2, len(self.posListRel)-1):
            nextTraj = np.load(os.path.join(self.rootFolder,
                                            self.posListRel[i]))

            traj = np.zeros((currentTraj.shape[0] + 2, currentTraj.shape[1]),
                            dtype=currentTraj.dtype)

            traj[0] = prevTraj[-1]
            traj[1:-1] = currentTraj
            traj[-1] = nextTraj[0]

            feat = B.generateTrajFeatures(traj,
                                          dt=currentTraj.shape[0]/1000.0)[1:-1]

            np.save(self.generateFeatureSavePath(self.posListRel[i-1]), feat)

            prevTraj = currentTraj
            currentTraj = nextTraj
            self.updateStatus(i)

        traj = np.zeros((nextTraj.shape[0] + 1, nextTraj.shape[1]),
                        dtype=nextTraj.dtype)
        traj[0] = currentTraj[-1]
        traj[1:] = nextTraj

        feat = B.generateTrajFeatures(traj,
                                      dt=currentTraj.shape[0]/1000.0)[1:]
        np.save(self.generateFeatureSavePath(self.posListRel[-1]), feat)


    def annotationFileList(self):
        annoFileList = []
        for videoFile in self.videoListRel:
            annoFileList += [self.convertVideoToAnnoFilename(videoFile)]

        return annoFileList


    def createAnnotationArrays(self, annoFileList):
        maxClass = len(self.annotationFilters)
        annotationArrays = dict()
        for annoFile in sorted(annoFileList):
            if os.path.exists(self.rel2absFile(annoFile)):
                anno = A.Annotation()
                anno.loadFromFile(self.rel2absFile(annoFile))
                for i, annoFilter in enumerate(self.annotationFilters):
                    filtAnno = anno.filterFrameListBool(annoFilter)
                    if i == 0:
                        annotationArrays[annoFile] = np.zeros(
                                                    (filtAnno.shape[0],
                                                     maxClass),
                                                    dtype=np.bool)
                    annotationArrays[annoFile][:,i] = filtAnno

        return annotationArrays


    def getClassLabels(self):
        annoFileList = self.annotationFileList()
        annoArrays = self.createAnnotationArrays(annoFileList)
        return annoArrays


    def loadFeatures(self, select, annoFile):
        featFile = self.rel2absFile(self.convertAnnoToFeatFilename(annoFile))
        feat = np.load(featFile)
        return feat[select]

    def createClassArray(self, classMatrix, select):
        """
        Simplified. Does not account for two concurrent labels in a frame
        :param classArray:
        :param select:
        :return:
        """
        maxClass = len(self.annotationFilters)
        filtered = classMatrix[select]
        classMask = np.arange(maxClass) + 1
        return np.max(filtered * classMask, axis=1)

    def getFeatureLength(self):
        return 8

    def sampleNegatives(self, negativeSelects, N):
        negFeatureMatrix = []
        draws = dict()

        for n in range(N):
            key = negativeSelects.keys()[np.random.randint(0,
                                                    len(negativeSelects))]
            idx = np.random.randint(0, len(negativeSelects[key]))

            if not key in draws:
                draws[key] = []

            draws[key] += [negativeSelects[key][idx]]
            del negativeSelects[key][idx]
            if negativeSelects[key] == []:
                del negativeSelects[key]

            if negativeSelects == {}:
                break

        for annoFile, selection in sorted(draws.items()):
            negFeatureMatrix += [self.loadFeatures(selection, annoFile)]
            self.incrementStatus()

        return np.vstack(negFeatureMatrix)

    def capNegativeSelects(self, negativeSelects, lastSelect):
        if lastSelect == [None, None]:
            return {}

        for k in negativeSelects.items():
            if k > lastSelect[0]:
                del negativeSelects[k]

        if lastSelect[0] in negativeSelects.keys():
            selection = np.asarray(negativeSelects[lastSelect[0]])
            negativeSelects[lastSelect[0]] = list(selection[selection <
                                                       lastSelect[1]])

        return negativeSelects


    def loadFeatureMatrix(self, annoArrays):
        classArray = []
        featureMatrix = []
        negativeSelects = dict()
        lastSelect = [None, None]
        N = 0
        for annoFile, classMatrix in sorted(annoArrays.items()):
            selection = np.where(classMatrix == True)[0]
            if selection.size: # if not "empty"
                featureMatrix += [self.loadFeatures(selection, annoFile)]
                classArray += [self.createClassArray(classMatrix, selection)]
                N += selection.shape[0]
                lastSelect = [annoFile, selection[-1]]

            rngSet = set(range(classMatrix.shape[0]))
            selSet = set(selection)

            negativeSelects[annoFile] = sorted(rngSet - selSet)
            self.incrementStatus()

        negativeSelects = self.capNegativeSelects(negativeSelects, lastSelect)

        negFeatureMatrix = self.sampleNegatives(negativeSelects, N)
        classArray += [np.zeros((negFeatureMatrix.shape[0],))]
        featureMatrix += [negFeatureMatrix]

        return np.hstack(classArray), np.vstack(featureMatrix)

    def getTrainingsMatrices(self):
        annoArrays = self.getClassLabels()
        classArray, featureMatrix = self.loadFeatureMatrix(annoArrays)
        return classArray, featureMatrix



    def trainClassifier(self):
        """
        Trains a classifier on the given labels
        :return:
        """
        self.setStatus("Training classifier..", len(self.videoListRel)*3)
        classArray, featureMatrix = self.getTrainingsMatrices()
        self.classifier = RFC(n_jobs=4)
        self.classifier.fit(featureMatrix, classArray)


    def classify(self):
        """
        Applies the classifier on all data
        :return:
        """
        print("classifying!")

        self.setStatus("classifying..", len(self.posListRel))

        filters = []
        self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
        self.fdvt.meta['singleFileMode'] = False

        filt = A.AnnotationFilter(annotators=["simpleFlyShowCase"],
                                  behaviours=['negative'],
                                  vials=self.annotationFilters[0].vials)
        self.fdvt.addNewClass(filt)
        filters += [filt]

        for af in self.annotationFilters:
            filt = A.AnnotationFilter(annotators=["simpleFlyShowCase"],
                                      behaviours=af.behaviours,
                                      vials=af.vials)
            self.fdvt.addNewClass(filt)
            filters += [filt]


        for i, posPath in enumerate(self.posListRel):
            feat = np.load(self.generateFeatureSavePath(posPath))
            predictions = self.classifier.predict(feat)
            dv = []                 # deltaVector
            for k, p in enumerate(predictions):
                dv += [self.fdvt.getDeltaValue(posPath, k, filters[int(p)])]

            self.fdvt.insertDeltaVector(dv)
            self.incrementStatus()

        self.fdvt.save("/media/peter/Seagate Backup Plus Drive/tmp/stackFdvt.npy")


    def generateFDVT(self):
        """
        Generates FrameDataVisualizationTree from classified frames
        :return:
        """

        print("Generating FrameDataVisualizationTree")
        self.fdvt = FDVT.FrameDataVisualizationTreeBase()


    def runPlugin(self):
        """
        Method that contains the logic of the plugin.

        This means typically that the plugin loops over the video files and
        extracts some features from the videos and applies a machine
        learning algorithm to it.

        At the end the function should call `self.sendFDVT()` to update the GUI
        :return:
        """
        self.extractFeatures()
        self.trainClassifier()
        self.classify()
        # self.generateFDVT()
        # self.sendFDVT()
