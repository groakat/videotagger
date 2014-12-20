import pyTools.system.plugins as P
import os
import numpy as np
import pyTools.features.trajectory.Burgos as B
import pyTools.videoProc.annotation as A


class SimpleFlyShowCase(P.ClassificationPluginBase):
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


        for i in range(1, len(self.posListRel)-1):
            nextTraj = np.load(os.path.join(self.rootFolder,
                                            self.posListRel[i]))

            traj = np.zeros((currentTraj.shape[0] + 2, currentTraj.shape[1]),
                            dtype=currentTraj.dtype)

            traj[0] = prevTraj[-1]
            traj[1:-1] = currentTraj
            traj[-1] = nextTraj[0]

            feat = B.generateTrajFeatures(traj,
                                          dt=currentTraj.shape[0]/1000.0)[1:-1]
            np.save(self.generateFeatureSavePath(self.posListRel[i]), feat)

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

            1/0

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


    def loadFeatureMatrix(self, annoArrays):
        classArray = []
        featureArray = []
        for annoFile, classMatrix in annoArrays.items():
            select = np.where(classMatrix == True)[0]
            if not select.size: # if not "empty"
                featureArray += [self.loadFeatures(select, annoFile)]
                classArray += [self.createClassArray(classMatrix, select)]

        1/0


    def getTrainingsMatrices(self):
        annoArrays = self.getClassLabels()
        classMatrix, featureMatrix = self.loadFeatureMatrix(annoArrays)
        1/0

    def trainClassifier(self):
        """
        Trains a classifier on the given labels
        :return:
        """
        self.getTrainingsMatrices()
        self.setStatus("Training classifier..", 100)
        print("Training classifier")
        for i in range(100):
            QtCore.QThread.msleep(10)
            self.updateStatus(i)

    def classify(self):
        """
        Applies the classifier on all data
        :return:
        """
        print("classifying!")

        self.setStatus("classifying..", 100)
        for i in range(100):
            QtCore.QThread.msleep(10)
            self.updateStatus(i)


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
        # self.extractFeatures()
        self.trainClassifier()
        # self.classify()
        # self.generateFDVT()
        # self.sendFDVT()
