from collections import namedtuple
from PySide import QtCore, QtGui
import pyTools.misc.FrameDataVisualization2 as FDVT
import json


MetaData = namedtuple('plugin_meta_data', ['name',
                                           'description'])

VideoData = namedtuple('video_data', ["posList",
                                      "annotationList",
                                      'videoList',
                                      'featureFolder'])

class PluginBase(object):
    def __init__(self, videoData, FDVTsendCallback):
        """

        :param videoData: a VideoData tuple
        :param FDVTsendCallback: function that the FDVT can be send to to update it in the GUI
        :return:
        """
        self.meta = self.getMeta()
        self.posList = []
        self.annotationList = []
        self.videoList = []
        self.featureFolder = None
        self.classifier = None
        self.fdvt = None
        self.FDVTsendCallback = FDVTsendCallback
        self.registerFileLists(videoData)




    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = MetaData(name='PluginBase',
                        description='Base class from which all plugins are derived')


        raise NotImplementedError('You need to implement this method to provide meta data of your plugin')

    def extractFeatures(self):
        """
        Iteration over video file to extract features
        :return:
        """
        raise NotImplementedError('You need to implement this method to extract features')

    def trainClassifier(self):
        """
        Trains a classifier on the given labels
        :return:
        """
        raise NotImplementedError('You need to implement this method to train the classifier')


    def classify(self):
        """
        Applies the classifier on all data
        :return:
        """
        raise NotImplementedError('You need to implement this method to apply the classifier')


    def generateFDVT(self):
        """
        Generates FrameDataVisualizationTree from classified frames
        :return:
        """
        raise NotImplementedError('You need to implement this method to generate FDVT')



    def runPlugin(self):
        """
        Method that contains the logic of the plugin.

        This means typically that the plugin loops over the video files and
        extracts some features from the videos and applies a machine
        learning algorithm to it.
        :return:
        """
        self.extractFeatures()
        self.trainClassifier()
        self.classify()
        self.generateFDVT()
        self.sendFDVT()

    def sendFDVT(self):
        if self.fdvt is not None:
            self.FDVTsendCallback(self.meta, self.fdvt)
        else:
            ValueError("Call generateFDVT() before sending it")

    def getWidget(self):
        """
        Defines a widget that is shown to the user in the main GUI
        :return: QWidget
        """
        w = QtGui.QWidget()
        label = QtGui.QLabel("Plugin: {0}".format(self.meta.name))
        startButton = QtGui.QPushButton("Start")
        self.statusLabel = QtGui.QLabel()
        self.progressBar = QtGui.QProgressBar()
        layout = QtGui.QVBoxLayout()

        layout.addWidget(label)
        layout.addWidget(startButton)
        layout.addWidget(self.statusLabel)
        layout.addWidget(self.progressBar)
        w.setLayout(layout)

        self.statusLabel.hide()
        self.progressBar.hide()

        startButton.clicked.connect(self.runPlugin)
        return w

    def setStatus(self, message, maxProgressValue):
        self.statusLabel.show()
        self.progressBar.show()
        self.statusLabel.setText(message)
        self.progressBar.setMaximum(maxProgressValue)

    def updateStatus(self, progress):
        self.progressBar.setValue(progress)

    def hideStatus(self):
        self.progressBar.hide()
        self.statusLabel.hide()

    def registerFileLists(self, videoData):
        """
        :param posList: list containing absolute paths to position files
        :param annotationList: list containing absolute paths to behaviour files (annotations)
        :param videoList: list containing absolute paths to video files
        :return:
        """
        self.posList = videoData.posList
        self.annotationList = videoData.annotationList
        self.videoList = videoData.videoList
        self.featureFolder = videoData.featureFolder

class TutorialPlugin(PluginBase):
    def getMeta(self):
        """
        Function that return meta data of plugin
        :return: MetaData object
        """
        meta = MetaData(name='TutorialPlugin',
                        description='Simple Plugin to show how to implement interfaces')
        return meta

    def extractFeatures(self):
        """
        Iteration over video file to extract features
        :return:
        """
        self.setStatus("extracting features..", len(self.videoList))
        for i, videoFile in enumerate(self.videoList):
            print("Extracting features of {0}".format(videoFile))
            QtCore.QThread.msleep(1)
            self.updateStatus(i)

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


class PluginGUITest(QtGui.QMainWindow):
    def __init__(self):
        super(PluginGUITest, self).__init__()


        self.setupUi(self)
        self.connectElements()


        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.cw = QtGui.QWidget(MainWindow)
        self.cw.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.cw)

        self.layout = QtGui.QVBoxLayout()

        self.pb_debug = QtGui.QPushButton("click me")
        self.layout.addWidget(self.pb_debug)

        self.cw.setLayout(self.layout)


    def connectElements(self):
        self.pb_debug.clicked.connect(self.buttonClick)

    def buttonClick(self):
        self.getTutorialPlugin()

    def updateFDVT(self, meta, fdvt):
        print("update FDVT")

    def loadFileList(self):
        with open("/media/peter/Seagate Backup Plus Drive/backgroundEstimation4Matt/videoCache.json", 'r') as f:
            fl = json.load(f)

        videoData = VideoData(posList=fl['positionList'],
                              videoList=fl['videoList'],
                              annotationList=[],
                              featureFolder='')

        return videoData

    def getTutorialPlugin(self):
        videoData = self.loadFileList()
        self.tutPlugin = TutorialPlugin(videoData, self.updateFDVT)
        self.layout.addWidget(self.tutPlugin.getWidget())

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    w = PluginGUITest()

    sys.exit(app.exec_())









