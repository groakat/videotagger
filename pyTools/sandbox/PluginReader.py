from PySide import QtCore, QtGui
import pyTools.system.plugins as P
import json

import imp
import os

class PluginGUITest(QtGui.QMainWindow):
    def __init__(self):
        super(PluginGUITest, self).__init__()

        self.pluginFolder = '/home/peter/phd/code/pyTools/pyTools/pyTools/sandbox/plugins/'
        self.MainModule = '__init__'

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

        videoData = P.VideoData(posList=fl['positionList'],
                              videoList=fl['videoList'],
                              annotationList=[],
                              featureFolder='')

        return videoData

    def getTutorialPlugin(self):
        videoData = self.loadFileList()
        self.tutPlugin = P.TutorialPlugin(videoData, self.updateFDVT)
        self.layout.addWidget(self.tutPlugin.getWidget())

    def getPlugins(self):
        plugins = []
        possibleplugins = os.listdir(self.PluginFolder)
        for i in possibleplugins:
            location = os.path.join(self.PluginFolder, i)
            if not os.path.isdir(location) or not self.MainModule + ".py" in os.listdir(location):
                continue
            info = imp.find_module(self.MainModule, [location])
            plugins.append({"name": i, "info": info})
        return plugins

    def loadPlugin(self, plugin):
        return imp.load_module(self.MainModule, *plugin["info"])



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    w = PluginGUITest()

    sys.exit(app.exec_())
