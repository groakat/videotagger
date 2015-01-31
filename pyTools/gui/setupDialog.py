__author__ = 'peter'
from PySide import QtCore, QtGui
import pyTools.gui.fullViewDialog as FVD
import sys
import os
import numpy as np


class Test(QtGui.QMainWindow):

    def __init__(self):
        super(Test, self).__init__()

        self.setupDialog = SetupDialog(self)

        self.setCentralWidget(self.setupDialog)
        self.show()
        #
        # import pyTools.videoProc.annotation as A
        #
        # a = A.Annotation()
        # a.loadFromFile('/media/peter/Seagate Backup Plus Drive1/peter_testCopy/WP609L_small.bhvr')
        # self.annoSelector.setAnnotation(a)

class MouseFilterObj(QtCore.QObject):
    def __init__(self, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            self.callback()

class SetupDialog(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(SetupDialog, self).__init__(*args, **kwargs)

        self.classColor = dict()
        self.eventFilter = dict()
        self.setupWidget()
        self.show()

    def activateFileWidgetButton(self):
        self.files_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "F_font_awesome_invert.svg"))

    def deactivateFileWidgetButton(self):
        self.files_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "F_font_awesome.svg"))

    def activateAnnotationButton(self):
        self.annotations_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "A_font_awesome_invert.svg"))

    def deactivateAnnotationButton(self):
        self.annotations_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "A_font_awesome.svg"))

    def activateCroppedButton(self):
        self.cropped_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "C_font_awesome_invert.svg"))

    def deactivateCroppedButton(self):
        if self.cb_croppedVideo.isChecked():
            self.cropped_button.load(os.path.join(
                                FVD.SVGButton.getIconFolder(),
                                "C_font_awesome.svg"))
        else:
            self.cropped_button.load(os.path.join(
                                FVD.SVGButton.getIconFolder(),
                                "C_font_awesome_grey.svg"))


    def activateExpertButton(self):
        self.expert_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "E_font_awesome_invert.svg"))

    def deactivateExpertButton(self):
        self.expert_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "E_font_awesome.svg"))

    def loadWidget(self, widget):
        self.filesWidget.hide()
        self.annotationWidget.hide()
        self.croppedVideoWidget.hide()
        self.expertSettingsWidget.hide()

        widget.show()

    def openFileWidget(self):
        self.activateFileWidgetButton()
        self.deactivateAnnotationButton()
        self.deactivateCroppedButton()
        self.deactivateExpertButton()

        self.loadWidget(self.filesWidget)

    def openAnnotationWidget(self):
        self.deactivateFileWidgetButton()
        self.activateAnnotationButton()
        self.deactivateCroppedButton()
        self.deactivateExpertButton()

        self.loadWidget(self.annotationWidget)

    def openCroppedWidget(self):
        if self.cb_croppedVideo.isChecked():
            self.deactivateFileWidgetButton()
            self.deactivateAnnotationButton()
            self.activateCroppedButton()
            self.deactivateExpertButton()

            self.loadWidget(self.croppedVideoWidget)

    def openExpertWidget(self):
        self.deactivateFileWidgetButton()
        self.deactivateAnnotationButton()
        self.deactivateCroppedButton()
        self.activateExpertButton()

        self.loadWidget(self.expertSettingsWidget)

    def swapCroppedVideoState(self, state):
        self.deactivateCroppedButton()


    def connectSignals(self):
        self.files_button.clicked.connect(self.openFileWidget)
        self.annotations_button.clicked.connect(self.openAnnotationWidget)
        self.cropped_button.clicked.connect(self.openCroppedWidget)
        self.expert_button.clicked.connect(self.openExpertWidget)

        # self.le_videoPath.editingFinished.connect(self.tryToLoadConfig)
        # self.pb_videoPath.clicked.connect(self.selectVideoPathFolder)
        # self.btn_videoSelection.clicked.connect(self.cacheFileList)
        self.cb_croppedVideo.stateChanged.connect(self.swapCroppedVideoState)

    def createFilesWidget(self):
        widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()

        self.lbl_videoPath = QtGui.QLabel()
        self.lbl_videoPath.setText("Path to Folder with Video")
        self.le_videoPath = QtGui.QLineEdit()
        self.pb_videoPath = QtGui.QPushButton()
        self.pb_videoPath.setText("Open Folder")

        layout.addWidget(self.lbl_videoPath, 0, 0)
        layout.addWidget(self.le_videoPath, 0, 1)
        layout.addWidget(self.pb_videoPath, 0, 2)

        self.lbl_videoSelection = QtGui.QLabel()
        self.lbl_videoSelection.setText("Start Video")
        self.cb_videoSelection = QtGui.QComboBox()
        self.btn_videoSelection = QtGui.QPushButton()
        self.btn_videoSelection.setText("Scan")

        layout.addWidget(self.lbl_videoSelection, 1, 0)
        layout.addWidget(self.cb_videoSelection, 1, 1)
        layout.addWidget(self.btn_videoSelection, 1, 2)


        self.lbl_startFrame = QtGui.QLabel()
        self.lbl_startFrame.setText("Start Frame")
        self.le_startFrame = QtGui.QLineEdit()
        self.le_startFrame.setValidator(QtGui.QIntValidator())

        layout.addWidget(self.lbl_startFrame, 2, 0)
        layout.addWidget(self.le_startFrame, 2, 1, 1, 2)

        self.lbl_croppedVideo = QtGui.QLabel()
        self.lbl_croppedVideo.setText("Cropped Video?")
        self.cb_croppedVideo = QtGui.QCheckBox()

        layout.addWidget(self.lbl_croppedVideo, 3, 0)
        layout.addWidget(self.cb_croppedVideo, 3, 1, 1, 2)

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                 QtGui.QSizePolicy.MinimumExpanding)

        layout.addWidget(spacer, 4, 0, 1, 3)
        layout.setRowStretch(4, 10)

        widget.setLayout(layout)

        return widget

    def getColorFromUser(self, lbl):
        color = QtGui.QColorDialog.getColor()
        self.setLabelColor(lbl, color)

    def setLabelColor(self, label, color):
        colourStyle = "background-color: {0}".format(color.name())
        label.setStyleSheet(colourStyle)
        self.classColor[label] = color

    def createColorSelector(self, color):
        lbl = QtGui.QLabel()
        lbl.setText("        ")
        self.setLabelColor(lbl, color)

        fp = lambda : self.getColorFromUser(lbl)

        self.eventFilter[lbl] = MouseFilterObj(fp)
        lbl.installEventFilter(self.eventFilter[lbl])

        return lbl

    # def pushAnnotationLineUp(self, idx):
    #     le_anno = self.annoLayout.itemAtPosition(idx, 0).widget()
    #     le_bhvr = self.annoLayout.itemAtPosition(idx, 1).widget()
    #     clr = self.annoLayout.itemAtPosition(idx, 2).widget()
    #     pb_del = self.annoLayout.itemAtPosition(idx, 3).widget()
    #     self.annoLayout.removeWidget(le_anno)
    #     self.annoLayout.removeWidget(le_bhvr)
    #     self.annoLayout.removeWidget(clr)
    #     self.annoLayout.removeWidget(pb_del)
    #
    #     self.annoLayout.addWidget(le_anno, idx-1 , 0, 1, 1)
    #     self.annoLayout.addWidget(le_bhvr, idx-1 , 1, 1, 1)
    #     self.annoLayout.addWidget(clr, idx-1 , 2, 1, 1)
    #     self.annoLayout.addWidget(pb_del, idx-1 , 3, 1, 1)

    def populateNewAnnotationGrid(self, itemsToKeep):
        gridLayout = QtGui.QGridLayout()

        for i, widgets in enumerate(itemsToKeep):
            for k, widget in enumerate(widgets):
                if widget is not None:
                    gridLayout.addWidget(widget, i, k)

        self.annoLayout = gridLayout
        self.annoSelector.setLayout(self.annoLayout)


    def deleteAnnotationLine(self, le_anno, le_bhvr, clr, pb_del):
        delRow = 0
        itemsToKeep = []
        for i in range(self.annoLayout.rowCount() -1):
            if self.annoLayout.itemAtPosition(i, 0).widget() == le_anno:
                delRow = i
            else:
                widgets = []
                for k in range(4):
                    widgets += [self.annoLayout.itemAtPosition(i, k).widget()]

                itemsToKeep += [widgets]

        itemsToKeep += [[None, None, None, self.pb_newAnnotationLine]]

        le_anno.hide()
        le_bhvr.hide()
        clr.hide()
        pb_del.hide()
        self.annoLayout.removeWidget(le_anno)
        self.annoLayout.removeWidget(le_bhvr)
        self.annoLayout.removeWidget(clr)
        self.annoLayout.removeWidget(pb_del)

        self.populateNewAnnotationGrid(itemsToKeep)

        #
        # for k in range(i + 1, self.annoLayout.rowCount()-1):
        #     self.pushAnnotationLineUp(k)



    def createNewAnnotationLine(self, annotator=None,
                                behaviour=None,
                                color=None):
        if annotator is None:
            annotator = self.le_annotatorName.text()

        if behaviour is None:
            behaviour = ''

        if color is None:
            c = QtGui.QColor(np.random.randint(0, 256),
                             np.random.randint(0, 256),
                             np.random.randint(0, 256))
        else:
            c = QtGui.QColor(color)

        le_anno = QtGui.QLineEdit()
        le_anno.setText(annotator)
        le_bhvr = QtGui.QLineEdit()
        le_bhvr.setText(behaviour)
        clr = self.createColorSelector(c)
        pb_del = QtGui.QPushButton()
        pb_del.setText("remove")
        fp = lambda : self.deleteAnnotationLine(le_anno,
                                                le_bhvr,
                                                clr,
                                                pb_del)
        pb_del.clicked.connect(fp)


        cnt = self.annoLayout.rowCount() - 1
        self.annoLayout.removeWidget(self.pb_newAnnotationLine)
        self.annoLayout.addWidget(le_anno, cnt , 0, 1, 1)
        self.annoLayout.addWidget(le_bhvr, cnt , 1, 1, 1)
        self.annoLayout.addWidget(clr, cnt , 2, 1, 1)
        self.annoLayout.addWidget(pb_del, cnt , 3, 1, 1)

        self.annoLayout.addWidget(self.pb_newAnnotationLine, cnt + 1, 3)


    def createAnnotationSelector(self):
        widget = QtGui.QWidget()
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)

        self.annoLayout = QtGui.QGridLayout()

        annoTitle = QtGui.QLabel()
        annoTitle.setText("Annotator")
        bhvrTitle = QtGui.QLabel()
        bhvrTitle.setText("Class")
        colorTitle = QtGui.QLabel()
        colorTitle.setText("Color")
        pb_scan = QtGui.QPushButton()
        pb_scan.setText("Scan")

        self.annoLayout.addWidget(annoTitle, 0, 0)
        self.annoLayout.addWidget(bhvrTitle, 0, 1)
        self.annoLayout.addWidget(colorTitle, 0, 2)
        self.annoLayout.addWidget(pb_scan, 0, 3)

        self.pb_newAnnotationLine = QtGui.QPushButton()
        self.pb_newAnnotationLine.setText("+")

        self.annoLayout.addWidget(self.pb_newAnnotationLine, 1, 3)
        self.pb_newAnnotationLine.clicked.connect(self.createNewAnnotationLine)


        self.createNewAnnotationLine()

        widget.setLayout(self.annoLayout)

        scrollArea.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                 QtGui.QSizePolicy.MinimumExpanding)

        return scrollArea



    def createAnnotationWidget(self):
        widget = QtGui.QWidget()
        outerLayout = QtGui.QGridLayout()

        self.lbl_annotatorName = QtGui.QLabel()
        self.lbl_annotatorName.setText("Your Name")
        self.le_annotatorName = QtGui.QLineEdit()

        outerLayout.addWidget(self.lbl_annotatorName, 0, 0)
        outerLayout.addWidget(self.le_annotatorName, 0, 1)

        self.annoSelector = self.createAnnotationSelector()
        outerLayout.addWidget(self.annoSelector, 1, 0, 1, 2)

        self.lbl_FDV = QtGui.QLabel()
        self.lbl_FDV.setText("Path to Frame Data Visualisation")
        self.le_FDV = QtGui.QLineEdit()

        outerLayout.addWidget(self.lbl_FDV, 2, 0)
        outerLayout.addWidget(self.le_FDV, 2, 1)

        self.lbl_bhvrFolder = QtGui.QLabel()
        self.lbl_bhvrFolder.setText("Path for Saving Behaviour Files")
        self.le_bhvrFolder = QtGui.QLineEdit()
        outerLayout.addWidget(self.lbl_bhvrFolder, 3, 0)
        outerLayout.addWidget(self.le_bhvrFolder, 3, 1)

        widget.setLayout(outerLayout)

        return widget


    def createCroppedVideoWidget(self):
        widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()

        self.lbl_patchesFolder = QtGui.QLabel()
        self.lbl_patchesFolder.setText("Folder to Patches")
        self.le_patchesFolder = QtGui.QLineEdit()

        layout.addWidget(self.lbl_patchesFolder, 0, 0)
        layout.addWidget(self.le_patchesFolder, 0, 1)

        self.lbl_positionsFolder = QtGui.QLabel()
        self.lbl_positionsFolder.setText("Folder to Position Files")
        self.le_positionsFolder = QtGui.QLineEdit()

        layout.addWidget(self.lbl_positionsFolder, 1, 0)
        layout.addWidget(self.le_positionsFolder, 1, 1)

        self.lbl_vial = QtGui.QLabel()
        self.lbl_vial.setText("Vial Selected")
        self.le_vial = QtGui.QLineEdit()
        self.le_vial.setText("none")

        layout.addWidget(self.lbl_vial, 2, 0)
        layout.addWidget(self.le_vial, 2, 1)

        self.lbl_vialROI = QtGui.QLabel()
        self.lbl_vialROI.setText("ROI of Vials")
        self.le_vialROI = QtGui.QLineEdit()
        self.le_vialROI.setText("[ [350,660], [661,960], [971,1260], [1290,1590] ]")

        layout.addWidget(self.lbl_vialROI, 3, 0)
        layout.addWidget(self.le_vialROI, 3, 1)

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                 QtGui.QSizePolicy.MinimumExpanding)

        layout.addWidget(spacer, 4, 0, 1, 2)
        layout.setRowStretch(4, 10)

        widget.setLayout(layout)

        return widget

    def createExpertSettingsWidget(self):
        widget = QtGui.QWidget()
        layout = QtGui.QGridLayout()


        self.lbl_bufferWidth = QtGui.QLabel()
        self.lbl_bufferWidth.setText("Number of Frames per Buffer")
        self.le_bufferWidth = QtGui.QLineEdit()
        self.le_bufferWidth.setValidator(QtGui.QIntValidator())
        self.le_bufferWidth.setText("200")

        layout.addWidget(self.lbl_bufferWidth, 0, 0)
        layout.addWidget(self.le_bufferWidth, 0, 1)

        self.lbl_bufferLength = QtGui.QLabel()
        self.lbl_bufferLength.setText("Number of Buffers Used")
        self.le_bufferLength = QtGui.QLineEdit()
        self.le_bufferLength.setValidator(QtGui.QIntValidator())
        self.le_bufferLength.setText("5")

        layout.addWidget(self.lbl_bufferLength, 1, 0)
        layout.addWidget(self.le_bufferLength, 1, 1)

        self.lbl_bhvrCache = QtGui.QLabel()
        self.lbl_bhvrCache.setText("Path to File Cache")
        self.le_bhvrCache = QtGui.QLineEdit()

        layout.addWidget(self.lbl_bhvrCache, 2, 0)
        layout.addWidget(self.le_bhvrCache, 2, 1)

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                 QtGui.QSizePolicy.MinimumExpanding)

        layout.addWidget(spacer, 3, 0, 1, 2)
        layout.setRowStretch(4, 10)

        widget.setLayout(layout)

        return widget


    def createButtonWidget(self):
        widget = QtGui.QWidget()

        iconFolder = FVD.SVGButton.getIconFolder()

        self.files_button = FVD.SVGButton(os.path.join(iconFolder,
                                            "F_font_awesome_invert.svg"))
        self.files_button.setFixedSize(40, 40)
        self.files_button.setToolTip("File Settings")

        self.annotations_button = FVD.SVGButton(os.path.join(iconFolder,
                                                       "A_font_awesome.svg"))
        self.annotations_button.setFixedSize(40, 40)
        self.annotations_button.setToolTip("Annotation Settings")

        self.cropped_button = FVD.SVGButton(os.path.join(iconFolder,
                                            "C_font_awesome_grey.svg"))
        self.cropped_button.setFixedSize(40, 40)
        self.cropped_button.setToolTip("Cropped Video Settings")

        self.expert_button = FVD.SVGButton(os.path.join(iconFolder,
                                                       "E_font_awesome.svg"))
        self.expert_button.setFixedSize(40, 40)
        self.expert_button.setToolTip("Expert Settings")

        layout = QtGui.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.files_button)
        layout.addWidget(self.annotations_button)
        layout.addWidget(self.cropped_button)
        layout.addWidget(self.expert_button)
        layout.addStretch()

        widget.setLayout(layout)

        return widget


    def setupWidget(self):
        self.filesWidget = self.createFilesWidget()
        self.annotationWidget = self.createAnnotationWidget()
        self.croppedVideoWidget = self.createCroppedVideoWidget()
        self.expertSettingsWidget = self.createExpertSettingsWidget()
        self.buttonWidget = self.createButtonWidget()

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.filesWidget)
        self.layout.addWidget(self.annotationWidget)
        self.layout.addWidget(self.croppedVideoWidget)
        self.layout.addWidget(self.expertSettingsWidget)

        self.annotationWidget.hide()
        self.croppedVideoWidget.hide()
        self.expertSettingsWidget.hide()

        # self.layout.addStretch()
        # self.spacer = QtGui.QSpacerItem(0,10,
        #                                 QtGui.QSizePolicy.MinimumExpanding,
        #                                 QtGui.QSizePolicy.MinimumExpanding)

        self.layout.addWidget(self.buttonWidget)
        self.setLayout(self.layout)


        self.buttonWidget.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                 QtGui.QSizePolicy.Maximum)

        self.connectSignals()





if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    w = Test()
    sys.exit(app.exec_())