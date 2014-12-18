import pyTools.system.plugins as P
import os
import numpy as np
import pyTools.features.trajectory.Burgos as B


class SimpleFlyShowCase(P.ClassificationPluginBase):
    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = P.MetaData(name='Simple Trajectory Classifier',
                        description='Simple Plugin to show how to implement interfaces using simple trajectory features')
        return meta

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
        print("saving to {0}".format(trajFeatFile))
        return trajFeatFile

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

    def trainClassifier(self):
        """
        Trains a classifier on the given labels
        :return:
        """
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
        self.extractFeatures()
        # self.trainClassifier()
        # self.classify()
        # self.generateFDVT()
        # self.sendFDVT()
