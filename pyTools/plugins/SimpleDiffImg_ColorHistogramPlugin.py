import pyTools.system.plugins as P
import os
import numpy as np
import pyTools.features.trajectory.Burgos as B
import pyTools.videoProc.annotation as A
from sklearn.ensemble import RandomForestClassifier as RFC
import pyTools.misc.FrameDataVisualization2 as FDV
import pyTools.system.videoExplorer as VE


class DiffImg_Color_Histogram_Plugin(P.ClassificationPluginBase):

    def __init__(self, *args, **kwargs):
        super(DiffImg_Color_Histogram_Plugin, self).__init__(*args, **kwargs)
        self.classifier = None

    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = P.MetaData(name='Simple Classifier based on Color and Difference Image Histograms',
                        description='Simple Plugin to show how to implement interfaces using simple histogram features of the video')
        return meta

    def rel2absFile(self, relFile):
        return  os.path.join(self.rootFolder, relFile)

    def generateColorFeatureSavePath(self, vidFile):
        bn = os.path.basename(vidFile)[:-4] + '.histogram.npy'
        baseFolder = os.path.dirname(vidFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(self.rootFolder,
                                baseFolder,
                                self.featureFolder,
                                'colorHistogram',
                                bn)
        return featFile

    def generateDiffImgFeatureSavePath(self, vidFile):
        bn = os.path.basename(vidFile)[:-4] + '.histogram.npy'
        baseFolder = os.path.dirname(vidFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(self.rootFolder,
                                baseFolder,
                                self.featureFolder,
                                'diffImgHistogram',
                                bn)
        return featFile


    def convertVideoToAnnoFilename(self, videoFile):
        bn = os.path.basename(videoFile)[:-4] + '.csv'
        baseFolder = os.path.dirname(videoFile)[:-len(self.videoFolder)]
        annoFile = os.path.join(baseFolder,
                                self.annotationFolder,
                                bn)
        return annoFile

    def convertAnnoToVideoFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-4] + self.videoListRel[0][-4:]
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        videoFile = os.path.join(baseFolder,
                                self.videoFolder,
                                bn)

        return videoFile

    def convertAnnoToColorFeatFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-5] + '.histogram.npy'
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(baseFolder,
                                self.featureFolder,
                                'colorHistogram',
                                bn)

        return featFile

    def convertAnnoToDiffImgFeatFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-5] + '.histogram.npy'
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(baseFolder,
                                self.featureFolder,
                                'diffImgHistogram',
                                bn)

        return featFile

    def computeColorHistogramFromFrame(self, frame):
        flattenedFrame = frame.reshape((-1, 3))
        H, edges = np.histogramdd(flattenedFrame, bins = (8, 8, 8))
        return H.ravel()

    def computeDiffImgHistogramFromFrame(self, frameA, frameB):
        from skimage.color import rgb2gray
        import cv2

        frameA_grey = rgb2gray(frameA)
        frameB_grey = rgb2gray(frameB)


        flow = cv2.calcOpticalFlowFarneback(frameA_grey, frameB_grey)

        flattenedFrame = flow.reshape((-1, 2))
        H, edges = np.histogramdd(flattenedFrame, bins = (8, 8))
        return H.ravel()

    def extractColorFeatureFromFrame(self, frame, annotation):
        """
        TODO: Implement this function
        :return:
        """

        return self.computeColorHistogramFromFrame(frame)

    def extractDiffImgFeatureFromFrames(self, frameA, frameB, annotation):
        """
        TODO: Implement this function
        :return:
        """

        return self.computeDiffImgHistogramFromFrame(frameA, frameB)

    def extractFeatures(self):
        """
        Iteration over video file to extract features
        :return:
        """
        if len(self.videoListRel) == 1:
            progressSteps = VE.videoExplorer.retrieveVideoLength(
                            self.rel2absFile(self.videoListRel[0]))
        else:
            progressSteps = len(self.videoListRel)

        self.setStatus("extracting features..", progressSteps)
        for i, relVidFile in enumerate(self.videoListRel):
            if os.path.exists(self.generateColorFeatureSavePath(relVidFile))\
            and os.path.exists(self.generateDiffImgFeatureSavePath(relVidFile)):
                # do not recompute features already computed
                if len(self.videoListRel) > 1:
                    self.incrementStatus()

                continue

            colorFeat = []
            diffImgFeat = []
            vE = VE.videoExplorer()
            vE.setVideoStream(self.rel2absFile(relVidFile), frameMode='RGB')

            anno = A.Annotation()
            anno.loadFromFile(self.rel2absFile(
                                self.convertVideoToAnnoFilename(relVidFile)))

            annotationList = anno.filterFrameLists(self.annotationFilters)
            prevFrame = None
            for frame in vE:
                colorFeat += [self.extractColorFeatureFromFrame(frame,
                                                      annotationList[i])]

                if prevFrame:
                    diffImgFeat += [self.extractDiffImgFeatureFromFrames(prevFrame,
                                                                         frame,
                                                                         annotationList[i])]
                else:
                    diffImgFeat += [np.zeros((16,), dtype=np.int32)]

                if len(self.videoListRel) == 1:
                    self.incrementStatus()

            np.save(self.generateColorFeatureSavePath(relVidFile),
                    np.asarray(colorFeat))

            np.save(self.generateDiffImgFeatureSavePath(relVidFile),
                    np.asarray(diffImgFeat))

            if len(self.videoListRel) > 1:
                self.incrementStatus()


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


    def loadColorFeatures(self, select, annoFile):
        featFile = self.rel2absFile(self.convertAnnoToColorFeatFilename(annoFile))
        feat = np.load(featFile)
        return feat[select]

    def loadDiffImgFeatures(self, select, annoFile):
        featFile = self.rel2absFile(self.convertAnnoToDiffImgFeatFilename(annoFile))
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
            negFeatureMatrix += [np.hstack((self.loadColorFeatures(selection, annoFile),
                                           self.loadDiffImgFeatures(selection, annoFile)))]
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
                featureMatrix += [np.hstack((self.loadColorFeatures(selection, annoFile),
                                           self.loadDiffImgFeatures(selection, annoFile)))]
                classArray += [self.createClassArray(classMatrix, selection)]
                N += selection.shape[0]
                lastSelect = [annoFile, selection[-1]]

            rngSet = set(range(classMatrix.shape[0]))
            selSet = set(selection)

            negativeSelects[annoFile] = sorted(rngSet - selSet)
            self.incrementStatus()

        # negativeSelects = self.capNegativeSelects(negativeSelects, lastSelect)
        #
        # negFeatureMatrix = self.sampleNegatives(negativeSelects, N)
        # classArray += [np.zeros((negFeatureMatrix.shape[0],))]
        # featureMatrix += [negFeatureMatrix]

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

        from sklearn.externals import joblib

        if os.path.exists(os.path.join(self.rootFolder,
                                                  'cls',
                                                  'color-diff')):

            self.classifier = joblib.load(os.path.join(self.rootFolder,
                                                  'cls',
                                                  'color-diff'))

        else:
            self.setStatus("Training classifier..", len(self.videoListRel)*3)
            classArray, featureMatrix = self.getTrainingsMatrices()
            self.classifier = RFC(n_jobs=4)
            self.classifier.fit(featureMatrix, classArray)

            if not os.path.exists(os.path.join(self.rootFolder,
                                                      'cls')):
                os.makedirs(os.path.join(self.rootFolder,
                                                      'cls'))

            joblib.dump(self.classifier, os.path.join(self.rootFolder,
                                                      'cls',
                                                      'color-diff'))


    def classify(self):
        """
        Applies the classifier on all data
        :return:
        """
        print("classifying!")
        if len(self.videoListRel) == 1:
            progressSteps = VE.videoExplorer.retrieveVideoLength(
                            self.rel2absFile(self.videoListRel[0]),
                            100000)
            self.fdvt = FDV.FrameDataVisualizationTreeBehaviour(os.path.join(self.rootFolder,
                                                                             'viz',
                                                                             'color-diff'))
            self.fdvt.meta['singleFileMode'] = True
        else:
            progressSteps = len(self.videoListRel)
            self.fdvt = FDV.FrameDataVisualizationTreeBehaviour(os.path.join(self.rootFolder,
                                                                             'viz',
                                                                             'color-diff'))
            self.fdvt.meta['singleFileMode'] = False

        self.setStatus("classifying...", progressSteps)

        filters = []

        # filt = A.AnnotationFilter(annotators=["simpleFlyShowCase"],
        #                           behaviours=['negative'],
        #                           vials=self.annotationFilters[0].vials)
        # self.fdvt.addNewClass(filt)
        # filters += [filt]

        for af in self.annotationFilters:
            filt = A.AnnotationFilter(annotators=["SimpleHistogramPlugin"],
                                      behaviours=af.behaviours,
                                      vials=af.vials)
            self.fdvt.addNewClass(filt)
            filters += [filt]

        for i, videoPathRel in enumerate(self.videoListRel):
            feat = np.hstack((np.load(self.generateColorFeatureSavePath(videoPathRel)),
                              np.load(self.generatediffImgFeatureSavePath(videoPathRel))))
            dv = []                 # deltaVector
            for k in range(0, feat.shape[0], 100):
                f = feat[k:k+100]
                prediction = self.classifier.predict(f)
                for i, p in enumerate(prediction) :
                    # p-1 because tehre is no negative class!!!
                    dv += [self.fdvt.getDeltaValue(videoPathRel, k + i,
                                               filters[int(p-1)])]


                if len(self.videoListRel) == 1:
                    self.incrementStatus(100)


            self.fdvt.insertDeltaVector(dv)

            if len(self.videoListRel) > 1:
                self.incrementStatus()

        self.fdvt.save()


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
        self.hideStatus()
        # self.generateFDVT()
        # self.sendFDVT()
