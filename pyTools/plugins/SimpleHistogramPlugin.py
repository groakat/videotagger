import pyTools.system.plugins as P
import os
import numpy as np
import pyTools.features.trajectory.Burgos as B
import pyTools.videoProc.annotation as A
from sklearn.ensemble import RandomForestClassifier as RFC
import pyTools.misc.FrameDataVisualization2 as FDV
import pyTools.system.videoExplorer as VE


class SimpleHistogramPlugin(P.ClassificationPluginBase):

    def __init__(self, *args, **kwargs):
        super(SimpleHistogramPlugin, self).__init__(*args, **kwargs)
        self.classifier = None

    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = P.MetaData(name='Simple Histogram Classifier',
                        description='Simple Plugin to show how to implement interfaces using simple histogram features of the video')
        return meta

    def rel2absFile(self, relFile):
        return  os.path.join(self.rootFolder, relFile)

    def generateFeatureSavePath(self, vidFile):
        bn = os.path.basename(vidFile)[:-4] + '.histogram.npy'
        baseFolder = os.path.dirname(vidFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(self.rootFolder,
                                baseFolder,
                                self.featureFolder,
                                'colorHistogram',
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

    def convertAnnoToFeatFilename(self, annoFile):
        bn = os.path.basename(annoFile)[:-4] + '.histogram.npy'
        baseFolder = os.path.dirname(annoFile)[:-len(self.annotationFolder)]
        featFile = os.path.join(baseFolder,
                                self.featureFolder,
                                'colorHistogram',
                                bn)

        return featFile

    def computeHistogramFromFrame(self, frame):
        flattenedFrame = frame.reshape((-1, 3))
        H, edges = np.histogramdd(flattenedFrame, bins = (8, 8, 8))
        return H.ravel()

    def extractFeatureFromFrame(self, frame, annotation):
        """
        TODO: Implement this function
        :return:
        """

        return self.computeHistogramFromFrame(frame)

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
            if os.path.exists(self.generateFeatureSavePath(relVidFile)):
                # do not recompute features already computed
                if len(self.videoListRel) > 1:
                    self.incrementStatus()

                continue

            feat = []
            vE = VE.videoExplorer()
            vE.setVideoStream(self.rel2absFile(relVidFile), frameMode='RGB')

            anno = A.Annotation()
            anno.loadFromFile(self.rel2absFile(
                                self.convertVideoToAnnoFilename(relVidFile)))

            annotationList = anno.filterFrameLists(self.annotationFilters)
            for frame in vE:
                feat += [self.extractFeatureFromFrame(frame,
                                                      None)]
                if len(self.videoListRel) == 1:
                    self.incrementStatus()

            np.save(self.generateFeatureSavePath(relVidFile),
                    np.asarray(feat))

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
                    filtAnno = anno.filterFrameListBool([annoFilter])
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
        classMask = np.arange(maxClass) # + 1
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
        if len(self.videoListRel) == 1:
            progressSteps = VE.videoExplorer.retrieveVideoLength(
                            self.rel2absFile(self.videoListRel[0]),
                            100000)
            # self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
            # self.fdvt.meta['singleFileMode'] = True
        else:
            progressSteps = len(self.videoListRel)
            # self.fdvt = FDV.FrameDataVisualizationTreeBehaviour()
            # self.fdvt.meta['singleFileMode'] = False

        self.setStatus("classifying...", progressSteps)

        filters = []

        # filt = A.AnnotationFilter(annotators=["simpleFlyShowCase"],
        #                           behaviours=['negative'],
        #                           vials=self.annotationFilters[0].vials)
        # self.fdvt.addNewClass(filt)
        # filters += [filt]

        clfy_res = []

        for af in self.annotationFilters:
            filt = A.AnnotationFilter(annotators=["SimpleHistogramPlugin"],
                                      behaviours=af.behaviours,
                                      vials=af.vials)
            # self.fdvt.addNewClass(filt)
            filters += [filt]


            clfy_res += [{'frames': [],
                         'meta': {}}]

        for i, videoPathRel in enumerate(self.videoListRel):
            feat = np.load(self.generateFeatureSavePath(videoPathRel))
            dv = []                 # deltaVector
            for k in range(0, feat.shape[0], 100):
                f = feat[k:k+100]
                prediction = self.classifier.predict(f)
                for j, p in enumerate(prediction):
                    # p-1 because tehre is no negative class!!!
                    # dv += [self.fdvt.getDeltaValue(videoPathRel, k + j,
                    #                            filters[int(p-1)])]

                    # UPDATE ANNOTATIONS
                    clfy_res[p]['frames'] += [k + j]
                    clfy_res[p]['meta'][k + j] = {"confidence": 1,
                                                  "boundingBox":[None, None, None, None]}


                if len(self.videoListRel) == 1:
                    self.incrementStatus(100)


            # SAVE RESULT IN ANNOTATIONS
            resAnno = A.Annotation(frameNo=feat.shape[0])
            for i, af in enumerate(self.annotationFilters):
                annotator = af.annotators[0]
                label = af.behaviours[0]

                if clfy_res[i]['frames']:
                    resAnno.addAnnotation(vial=None,
                                          frames=clfy_res[i]['frames'],
                                          annotator='SimpleHistogramPlugin',
                                          behaviour=label,
                                          metadata=clfy_res[i]['meta'])


            # self.fdvt.insertDeltaVector(dv)

            resAnno.saveToFile(self.generateFeatureSavePath(videoPathRel) + 'hist.csv')

            if len(self.videoListRel) > 1:
                self.incrementStatus()
        # self.fdvt.save("/Volumes/Seagate Backup Plus Drive/tmp/stackFdvt.npy")


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
