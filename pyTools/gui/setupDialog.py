__author__ = 'peter'
from PySide import QtCore, QtGui
import pyTools.gui.fullViewDialog as FVD
import sys
import os
import numpy as np
import json
import pyTools.misc.config as cfg
import pyTools.videoTagger.modifyableRect as MR
import pyTools.videoProc.annotation as A


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

        return False


class AnnotationSelector(QtGui.QScrollArea):
    def __init__(self,
                 annotator=None,
                 anno=None,
                 annotationSettingsList=None,
                 *args, **kwargs):
        super(AnnotationSelector, self).__init__(*args, **kwargs)

        self.anno = anno
        self.annotators = []
        self.labels = []
        self.classColor = dict()
        self.eventFilters = dict()

        self.annoLayout = QtGui.QGridLayout()

        self.setAnnotator(annotator)
        self.createAnnotationSelector(annotationSettingsList)

    def getUserSelection(self):
        selections = []
        for i in range(1, self.annoLayout.rowCount() - 1):
            anno = self.annoLayout.itemAtPosition(i, 0).widget().currentText()
            lbl = self.annoLayout.itemAtPosition(i, 1).widget().currentText()
            clr = self.classColor[self.annoLayout.itemAtPosition(i, 2)
                                                 .widget()]

            selections += [[anno, lbl, clr]]

        return selections

    def setUserSelection(self, selections):
        # self.deleteAllAnnotationLines()
        #
        # for anno, lbl, color in selections:
        #     self.createNewAnnotationLine(anno, lbl, color)
        self.createAnnotationSelector(annotationSettingsList=selections)


    def setAnnotationLabelSelection(self, annotators, labels):
        for i in range(1, self.annoLayout.rowCount() - 1):
            self.annoLayout.itemAtPosition(i, 0).widget().setModel(annotators)
            self.annoLayout.itemAtPosition(i, 1).widget().setModel(labels)

    def scanLabelFile(self):
        selections = self.getUserSelection()
        if self.anno is not None:
            annotationFilters = self.anno.extractAllFilterTuples()
            self.annotators = sorted(set(zip(*annotationFilters)[0]) - \
                         {'automatic placeholder'} | \
                         {self.annotator})
            self.labels = sorted(set(zip(*annotationFilters)[1]) - \
                                {'video length'})
        else:
            self.annotators = [self.annotator]
            self.labels = []

        # self.setAnnotationLabelSelection(self.annotators, self.labels)
        self.setUserSelection(selections=selections)

    def setAnnotationFile(self, filename):
        try:
            self.anno = A.Annotation()
            self.anno.loadFromFile(filename)
            self.scanLabelFile()
        except IOError:
            self.anno = None

    def setAnnotator(self, annotator=None):
        if annotator is None:
            annotator = ''

        self.annotator = annotator

        self.annotators = sorted(set(self.annotators) | {annotator})
        self.setAnnotationLabelSelection(self.annotators, self.labels)


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

        self.eventFilters[lbl] = MouseFilterObj(fp)
        lbl.installEventFilter(self.eventFilters[lbl])

        return lbl

    def populateNewAnnotationGrid(self, itemsToKeep):
        cfg.log.info("itemsToKeep: {}".format(itemsToKeep))
        gridLayout = QtGui.QGridLayout()

        for i, widgets in enumerate(itemsToKeep):
            for k, widget in enumerate(widgets):
                if widget is not None:
                    gridLayout.addWidget(widget, i, k)

        # self.annoLayout.deleteLater()
        self.annoLayout = gridLayout
        self.annoSelector.setLayout(self.annoLayout)

        return True

    # def deleteAllAnnotationLines(self):
    #     for i in range(self.annoLayout.rowCount() - 1, 0, -1):
    #         self.deleteAnnotationLine(
    #             self.annoLayout.itemAtPosition(i, 0).widget(),
    #             self.annoLayout.itemAtPosition(i, 1).widget(),
    #             self.annoLayout.itemAtPosition(i, 2).widget(),
    #             self.annoLayout.itemAtPosition(i, 3).widget())


    def deleteAnnotationLine(self, le_anno, le_bhvr, clr, pb_del):
        delRow = 0
        itemsToKeep = []
        for i in range(1, self.annoLayout.rowCount() - 1):
            if self.annoLayout.itemAtPosition(i, 0).widget() == le_anno:
                delRow = i
            else:
                widgets = []
                for k in range(4):
                    w = self.annoLayout.itemAtPosition(i, k).widget()
                    self.annoLayout.removeWidget(w)
                    if k == 0:
                        widgets += [w.currentText()]
                    if k == 1:
                        widgets += [w.currentText()]
                    if k == 2:
                        widgets += [self.classColor[w]]


                itemsToKeep += [widgets]

        self.annoLayout.removeWidget(self.annoLayout.itemAtPosition(self.annoLayout.rowCount()-1,
                                                                    3).widget())

        self.annoLayout.removeWidget(le_anno)
        self.annoLayout.removeWidget(le_bhvr)
        self.annoLayout.removeWidget(clr)
        self.annoLayout.removeWidget(pb_del)

        le_anno.deleteLater()
        le_bhvr.deleteLater()
        clr.deleteLater()
        pb_del.deleteLater()

        self.annoLayout.deleteLater()
        self.takeWidget()

        self.createAnnotationSelector(annotationSettingsList=itemsToKeep)

        return True



    def createNewAnnotationLine(self, annotator=None,
                                behaviour=None,
                                color=None):
        if annotator is None:
            annotator = self.annotator

        if behaviour is None:
            behaviour = ''

        if color is None:
            c = QtGui.QColor(np.random.randint(0, 256),
                             np.random.randint(0, 256),
                             np.random.randint(0, 256))
        else:
            c = QtGui.QColor(color)

        le_anno = MR.AutoCompleteComboBox(self)
        le_anno.setModel(self.annotators)
        le_anno.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                              QtGui.QSizePolicy.Minimum)
        le_anno.setCurrentText(annotator)
        le_bhvr = MR.AutoCompleteComboBox(self)
        le_bhvr.setModel(self.labels)
        le_bhvr.setCurrentText(behaviour)
        le_bhvr.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                              QtGui.QSizePolicy.Minimum)
        clr = self.createColorSelector(c)
        pb_del = QtGui.QPushButton()
        pb_del.setText("remove")
        fp = lambda: self.deleteAnnotationLine(le_anno,
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

        return True


    def createAnnotationSelector(self, annotationSettingsList=None):
        widget = QtGui.QWidget()

        self.setWidget(widget)
        self.setWidgetResizable(True)

        self.annoLayout = QtGui.QGridLayout()

        annoTitle =  QtGui.QLabel()
        annoTitle.setText("Annotator")
        bhvrTitle =  QtGui.QLabel()
        bhvrTitle.setText("Class")
        colorTitle = QtGui.QLabel()
        colorTitle.setText("Color")
        pb_scan = QtGui.QPushButton()
        pb_scan.setText("Scan")

        pb_scan.clicked.connect(self.scanLabelFile)

        self.annoLayout.addWidget(annoTitle, 0, 0)
        self.annoLayout.addWidget(bhvrTitle, 0, 1)
        self.annoLayout.addWidget(colorTitle, 0, 2)
        self.annoLayout.addWidget(pb_scan, 0, 3)

        self.pb_newAnnotationLine = QtGui.QPushButton()
        self.pb_newAnnotationLine.setText("+")

        self.annoLayout.addWidget(self.pb_newAnnotationLine, 1, 3)
        self.pb_newAnnotationLine.clicked.connect(self.createNewAnnotationLine)


        if annotationSettingsList is not None:
            for annotator, behaviour, color in annotationSettingsList:
                self.createNewAnnotationLine(annotator, behaviour, color)


        widget.setLayout(self.annoLayout)

        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                 QtGui.QSizePolicy.MinimumExpanding)

        return self



class SetupDialog(QtGui.QWidget):
    def __init__(self, videoTagger=None, *args, **kwargs):
        super(SetupDialog, self).__init__(*args, **kwargs)
        #
        # self.classColor = dict()
        # self.eventFilter = dict()
        self.videoTagger = videoTagger
        self.setupWidget()
        self.show()


    def connectSignals(self):
        self.files_button.clicked.connect(self.openFileWidget)
        self.annotations_button.clicked.connect(self.openAnnotationWidget)
        self.cropped_button.clicked.connect(self.openCroppedWidget)
        self.expert_button.clicked.connect(self.openExpertWidget)
        self.run_button.clicked.connect(self.launchVideoTagger)

        self.le_videoPath.editingFinished.connect(self.tryToLoadConfig)
        self.pb_videoPath.clicked.connect(self.selectVideoPathFolder)
        self.btn_videoSelection.clicked.connect(self.cacheFileList)
        self.cb_croppedVideo.stateChanged.connect(self.swapCroppedVideoState)

    def activateFileWidgetButton(self):
        self.files_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "folder_font_awesome_invert.svg"))

    def deactivateFileWidgetButton(self):
        self.files_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "folder_font_awesome.svg"))

    def activateAnnotationButton(self):
        self.annotations_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "users_font_awesome_invert.svg"))

    def deactivateAnnotationButton(self):
        self.annotations_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "users_font_awesome.svg"))



    def activateCroppedButton(self):
        self.cropped_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "crop_font_awesome_invert.svg"))

    def deactivateCroppedButton(self):
        if self.cb_croppedVideo.isChecked():
            self.cropped_button.load(os.path.join(
                                FVD.SVGButton.getIconFolder(),
                                "crop_font_awesome.svg"))
        else:
            self.cropped_button.load(os.path.join(
                                FVD.SVGButton.getIconFolder(),
                                "crop_font_awesome_grey.svg"))


    def activateExpertButton(self):
        self.expert_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "flask_font_awesome_invert.svg"))

    def deactivateExpertButton(self):
        self.expert_button.load(os.path.join(
                            FVD.SVGButton.getIconFolder(),
                            "flask_font_awesome.svg"))

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
        self.updateAnnotationSelector()
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
        self.le_startFrame.setText("0")

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

    def createAnnotationWidget(self):
        widget = QtGui.QWidget()
        outerLayout = QtGui.QGridLayout()

        self.lbl_annotatorName = QtGui.QLabel()
        self.lbl_annotatorName.setText("Your Name")
        self.le_annotatorName = QtGui.QLineEdit()

        outerLayout.addWidget(self.lbl_annotatorName, 0, 0)
        outerLayout.addWidget(self.le_annotatorName, 0, 1)

        self.annoSelector = AnnotationSelector(self.le_annotatorName.text())
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

        self.lbl_maxAnnotationSpeed = QtGui.QLabel()
        self.lbl_maxAnnotationSpeed.setText("Maximum speed while annotation is open")
        self.le_maxAnnotationSpeed = QtGui.QLineEdit()

        layout.addWidget(self.lbl_maxAnnotationSpeed, 3, 0)
        layout.addWidget(self.le_maxAnnotationSpeed, 3, 1)

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                 QtGui.QSizePolicy.MinimumExpanding)

        layout.addWidget(spacer, 4, 0, 1, 2)
        layout.setRowStretch(4, 10)

        widget.setLayout(layout)

        return widget


    def createButtonWidget(self):
        widget = QtGui.QWidget()

        iconFolder = FVD.SVGButton.getIconFolder()

        self.files_button = FVD.SVGButton(os.path.join(iconFolder,
                                            "folder_font_awesome_invert.svg"))
        self.files_button.setFixedSize(20, 20)
        self.files_button.setToolTip("File Settings")

        self.annotations_button = FVD.SVGButton(os.path.join(iconFolder,
                                                       "users_font_awesome.svg"))
        self.annotations_button.setFixedSize(20, 20)
        self.annotations_button.setToolTip("Annotation Settings")

        self.cropped_button = FVD.SVGButton(os.path.join(iconFolder,
                                            "crop_font_awesome_grey.svg"))
        self.cropped_button.setFixedSize(20, 20)
        self.cropped_button.setToolTip("Cropped Video Settings")

        self.expert_button = FVD.SVGButton(os.path.join(iconFolder,
                                                       "flask_font_awesome.svg"))
        self.expert_button.setFixedSize(20, 20)
        self.expert_button.setToolTip("Expert Settings")


        self.run_button = FVD.SVGButton(os.path.join(iconFolder,
                                                       "chevron-circle-right_font_awesome.svg"))
        self.run_button.setFixedSize(30, 30)
        self.run_button.setToolTip("Run")

        layout = QtGui.QHBoxLayout()
        layout.addStretch()
        layout.addSpacing(40)
        layout.addWidget(self.files_button)
        layout.addSpacing(10)
        layout.addWidget(self.annotations_button)
        layout.addSpacing(10)
        layout.addWidget(self.cropped_button)
        layout.addSpacing(10)
        layout.addWidget(self.expert_button)
        layout.addStretch()
        layout.addWidget(self.run_button)

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

    def updateAnnotationSelector(self, annotationFilters=None):
        self.annoSelector.setAnnotator(self.le_annotatorName.text())
        annotationFilename = os.path.join(self.le_videoPath.text(),
                                          '.'.join(self.cb_videoSelection
                                                       .currentText()
                                                       .split('.')[:-1])) \
                             + '.csv'

        self.annoSelector.setAnnotationFile(annotationFilename)

        if annotationFilters is not None:
            self.annotationsSelections = annotationFilters
            self.annoSelector.setUserSelection(annotationFilters)

    def setFormValues(self,
                             path,
                             videoListPathRel,
                             fileListRel,
                             annotator,
                             annotationFilters,
                             bhvrFolder,
                             selectedVial,
                             patchesFolder,
                             positionsFolder,
                             fdvtPathRel,
                             vialROI,
                             bufferWidth,
                             bufferLength,
                             getCurrentKey_idx,
                             croppedVideo,
                             maxAnnotationSpeed
                             ):

        # TODO: put this in videoTagger
        # self.fileListRel, self.videoListFullResRel, \
        #     self.bgListRel, self.posListRel =   \
        #             self.getFileList(path, videoExtension, videoListPathRel)
        #
        # self.fileList = self.getAbsolutePaths(fileListRel)


        self.cb_videoSelection.clear()
        print fileListRel
        self.cb_videoSelection.addItems(fileListRel)

        self.le_annotatorName.setText(annotator)
        self.annoSelector.setAnnotator(annotator)
        self.le_videoPath.setText(path)
        self.le_bhvrFolder.setText(bhvrFolder)
        self.le_bhvrCache.setText(videoListPathRel)
        if selectedVial is None:
            self.le_vial.setText(str(selectedVial))
        else:
            self.le_vial.setText(str(selectedVial[0]))
        self.le_patchesFolder.setText(str(patchesFolder))
        self.le_positionsFolder.setText(str(positionsFolder))
        self.le_FDV.setText(fdvtPathRel)
        self.le_vialROI.setText(str(vialROI))
        self.le_bufferWidth.setText(str(bufferWidth))
        self.le_bufferLength.setText(str(bufferLength))
        self.le_startFrame.setText(str(getCurrentKey_idx[1]))
        self.cb_croppedVideo.setChecked(croppedVideo)
        self.le_maxAnnotationSpeed.setText(str(maxAnnotationSpeed))

        self.updateAnnotationSelector(annotationFilters)

    def getFormValues(self):
        path = self.le_videoPath.text()
        annotator = self.le_annotatorName.text()
        if self.le_vial.text().lower() != 'none':
            selectedVial = [int(self.le_vial.text())]
        else:
            selectedVial = None

        if self.le_vialROI.text().lower() != 'none':
            vialROI = json.loads(self.le_vialROI.text())
        else:
            vialROI = None

        croppedVideo = self.cb_croppedVideo.isChecked()
        positionsFolder = self.le_positionsFolder.text()
        bhvrFolder = self.le_bhvrFolder.text()
        patchesFolder = self.le_patchesFolder.text()
        # runningIndeces = self.le_filesRunningIdx.isChecked()
        fdvtPath = self.le_FDV.text()
        videoListPath = self.le_bhvrCache.text()
        bufferWidth = int(self.le_bufferWidth.text())
        bufferLength= int(self.le_bufferLength.text())
        startVideoName = self.cb_videoSelection.currentText()
        startFrame = int(self.le_startFrame.text())
        maxAnnotationSpeed = int(self.le_maxAnnotationSpeed.text())

        self.annotationsSelections = self.annoSelector.getUserSelection()

        return  path,               \
                annotator,          \
                selectedVial,       \
                vialROI,            \
                croppedVideo,       \
                positionsFolder,    \
                bhvrFolder,         \
                patchesFolder,      \
                fdvtPath,           \
                videoListPath,      \
                bufferWidth,        \
                bufferLength,       \
                startVideoName,     \
                startFrame,         \
                maxAnnotationSpeed, \
                self.annotationsSelections

    def launchVideoTagger(self):
        self.videoTagger.submitForm()

    def tryToLoadConfig(self):
        self.videoTagger.tryToLoadConfig(self.le_videoPath.text())

    def selectVideoPathFolder(self):
        self.videoTagger.selectVideoPathFolder()

    def cacheFileList(self):
        self.videoTagger.cacheFileList()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    w = Test()
    sys.exit(app.exec_())