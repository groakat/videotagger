from PySide import QtCore, QtGui, QtSvg
from pyTools.gui import fullViewDialog_auto
from pyTools.gui.fullViewDialog_auto import Ui_Dialog
import pyTools.videoTagger.hud as HUD
import pyTools.videoTagger.overlayDialog as OD

import json
import os

class FullViewDialog(QtGui.QMainWindow):
    def __init__(self, parent, previewWidget=None):
        super(FullViewDialog, self).__init__(parent)
        # Usual setup stuff. Set up the user interface from Designer
        # self.ui = Ui_Dialog()
        self.previewWidget = previewWidget
        self.cw = QtGui.QWidget(self)
        self.setCentralWidget(self.cw)
        l = QtGui.QHBoxLayout(self.cw)
        self.hSplitter = QtGui.QSplitter(QtCore.Qt.Horizontal, self.cw)
        self.hSplitter.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                   QtGui.QSizePolicy.MinimumExpanding)

        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical, self.cw)
        self.splitter.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                   QtGui.QSizePolicy.MinimumExpanding)
        l.addWidget(self.hSplitter)

        self.hSplitter.addWidget(self.splitter)
        self.bmView = bookmarkView(self, self.parent())
        self.lblView = fullFrameLabelView(self, self.parent())
        self.hSplitter.addWidget(self.bmView)
        self.hSplitter.addWidget(self.lblView)
        self.bmView.hide()
        self.lblView.hide()

        self.cw.setLayout(l)
        # self.cw = QtGui.QWidget(self)
        self.horizontalLayout = None
        self.verticalLayout = None
        self.graphicsView = None
        self.setupUI()
        self.scene = None
        self.hud = HUD.HUD(self.graphicsView)
        self.setupHUD()
        self.setupControlWidget()
        self.playing = False
        self.editing = True
        self.bookmarksOpen = False
        self.labelsOpen = False
        self.trajectoryEnabled = False
        self.mouseFilter = MouseFilterObj(self)
        self.installEventFilter(self.mouseFilter)
        # self.hud.installEventFilter(self.mouseFilter)

    def setupUI(self):
        if self.previewWidget is not None:
            prevDummyWidget = QtGui.QWidget()
            prevLayout = QtGui.QHBoxLayout(prevDummyWidget)
            prevLayout.addWidget(self.previewWidget)

        # self.graphicsView = QtGui.QGraphicsView()
        self.graphicsView = FullViewGraphicsView()
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setMouseTracking(True)

        self.splitter.addWidget(prevDummyWidget)
        self.splitter.addWidget(self.graphicsView)

        self.setGeometry(QtCore.QRect(100,100,800, 600))


    def setupHUD(self):
        self.hud.setColor(QtGui.QColor(255,255,255,100))
        self.hud.setGeometry(QtCore.QRect(10, 10, 841, 50))

    def setupControlWidget(self):
        self.controlWidget = QtGui.QWidget(self)
        layout = QtGui.QHBoxLayout(self.controlWidget)

        self.iconFolder = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            os.path.pardir,
                            'icon')

        self.fdvButton = SVGButton(self.controlWidget)
        self.fdvButton.load(self.iconFolder + '/Bar_chart_font_awesome.svg')
        self.fdvButton.setToolTip("Open hierarchical view of labels")
        self.fdvButton.setFixedSize(20, 20)
        self.fdvButton.clicked.connect(self.parent().openFDV)
        layout.addWidget(self.fdvButton)

        self.timelineButton = SVGButton(self.controlWidget)
        self.timelineButton.load(self.iconFolder + '/Align_justify_font_awesome.svg')
        self.timelineButton.setToolTip("Open timeline panel (not implemented yet)")
        self.timelineButton.setFixedSize(20, 20)
        layout.addWidget(self.timelineButton)

        self.bookmarkButton = SVGButton(self.controlWidget)
        self.bookmarkButton.load(self.iconFolder + '/Bookmark_font_awesome.svg')
        self.bookmarkButton.setToolTip("Open bookmark panel")
        self.bookmarkButton.setFixedSize(20, 20)
        self.bookmarkButton.clicked.connect(self.toggleBookmarks)
        layout.addWidget(self.bookmarkButton)

        self.fullFrameLabelButton = SVGButton(self.controlWidget)
        self.fullFrameLabelButton.load(self.iconFolder + '/Picture_font_awesome.svg')
        self.fullFrameLabelButton.setToolTip("Open panel showing labels covering the entire frame (not implemented yet))")
        self.fullFrameLabelButton.setFixedSize(20, 20)
        self.fullFrameLabelButton.clicked.connect(self.toggleFullFrameLabels)
        layout.addWidget(self.fullFrameLabelButton)

        self.trajectoryButton = SVGButton(self.controlWidget)
        self.trajectoryButton.load(self.iconFolder + '/trajectory.svg')
        self.trajectoryButton.setToolTip("Enable display of trajectory")
        self.trajectoryButton.setFixedSize(20, 20)
        self.trajectoryButton.clicked.connect(self.toggleTrajectory)
        layout.addWidget(self.trajectoryButton)

        layout.addStretch()

        self.fullResButton = SVGButton(self.controlWidget)
        self.fullResButton.load(self.iconFolder + '/Search_font_awesome.svg')
        self.fullResButton.setToolTip("Show current frame in full resolution [SPACE]")
        self.fullResButton.setFixedSize(20, 20)
        self.fullResButton.clicked.connect(self.parent().displayFullResolutionFrame)
        layout.addWidget(self.fullResButton)

        layout.addSpacing(30)

        self.playButton = SVGButton(self.controlWidget)
        self.playButton.load(self.iconFolder + '/Play_font_awesome.svg')
        self.playButton.setToolTip("Play video")
        self.playButton.setFixedSize(20, 20)
        self.playButton.clicked.connect(self.playButtonClick)
        layout.addWidget(self.playButton)

        layout.addSpacing(30)

        self.modeButton = SVGButton(self.controlWidget)
        self.modeButton.load(self.iconFolder + '/Edit_font_awesome.svg')
        self.modeButton.setToolTip("Switch to 'Edit-mode' [CTRL + RETURN]")
        self.modeButton.setFixedSize(20, 20)
        self.modeButton.clicked.connect(self.toggleEditModeCheckbox)
        layout.addWidget(self.modeButton)

        layout.addStretch()
        layout.addSpacing(60)

        self.saveButton = SVGButton(self.controlWidget)
        self.saveButton.load(self.iconFolder + '/Save_font_awesome.svg')
        self.saveButton.setToolTip("Save all annotations [CTRL + S]")
        self.saveButton.setFixedSize(20, 20)
        self.saveButton.clicked.connect(self.parent().saveAll)
        layout.addWidget(self.saveButton)

        self.settingsButton = SVGButton(self.controlWidget)
        self.settingsButton.load(self.iconFolder + '/Cogs_font_awesome.svg')
        self.settingsButton.setToolTip("Open settings")
        self.settingsButton.setFixedSize(20, 20)
        self.settingsButton.clicked.connect(self.parent().openKeySettings)
        layout.addWidget(self.settingsButton)

        self.startVideoButton = SVGButton(self.controlWidget)
        self.startVideoButton.load(self.iconFolder + '/Refresh_font_awesome.svg')
        self.startVideoButton.setToolTip("Restart video event loop")
        self.startVideoButton.setFixedSize(20, 20)
        try:
            self.startVideoButton.clicked.connect(self.parent().startVideo)
        except RuntimeError:
            # has already been connected
            pass
        layout.addWidget(self.startVideoButton)


        self.splitter.addWidget(self.controlWidget)


    def setScene(self, scene):
        self.scene = scene
        self.graphicsView.setScene(self.scene)
        self.graphicsView.fitInView(self.scene.sceneRect())
        self.scene.installEventFilter(self.mouseFilter)

    # def resizeEvent(self, event):
    #     super(FullViewDialog, self).resizeEvent(event)
    #     self.wasResized = True
    #
    #     bounds = self.graphicsView.scene().sceneRect()
    #     self.graphicsView.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
    #     self.graphicsView.centerOn(0, 0)

    def showEvent(self, event):
        super(FullViewDialog, self).showEvent(event)
        if self.scene:
            self.graphicsView.fitInView(self.scene.sceneRect())


    def setAnnotator(self, str):
        self.hud.setAnnotator(str)

    def setBehaviour(self, str, color=None):
        self.hud.setBehaviour(str, color)

    def setFrame(self, str):
        self.hud.setFrame(str)

    def setFile(self, str):
        self.hud.setFile(str)

    def setSpeed(self, str):
        self.hud.setSpeed(str)

    def setMode(self, str, color=None):
        self.hud.setMode(str, color)

    def playButtonClick(self):
        if not self.playing:
            self.playButton.load(self.iconFolder + '/Pause_font_awesome.svg')
            self.playButton.setToolTip("Pause video")
            self.parent().playback()
        else:
            self.playButton.load(self.iconFolder + '/Play_font_awesome.svg')
            self.playButton.setToolTip("Play video")
            self.parent().stopPlayback()

        self.playing = not self.playing

    def toggleEditModeCheckbox(self):
        self.editing = not self.editing

        if self.editing:
            self.modeButton.load(self.iconFolder + '/Edit_font_awesome.svg')
            self.modeButton.setToolTip("Switch to 'Edit-mode' [CTRL + RETURN]")
        else:
            self.modeButton.load(self.iconFolder + '/F0fe_font_awesome.svg')
            self.modeButton.setToolTip("Switch to 'Additive-mode' [CTRL + RETURN]")

        self.parent().toggleEditModeCheckbox()

    def toggleFullFrameLabels(self):
        self.labelsOpen = not self.labelsOpen
        if self.labelsOpen:
            self.lblView.show()
            # self.bookmarkButton.load(self.iconFolder + '/Bookmark_empty_font_awesome.svg')
        else:
            self.lblView.hide()
            # self.bookmarkButton.load(self.iconFolder + '/Bookmark_font_awesome.svg')

    def toggleBookmarks(self):
        self.bookmarksOpen = not self.bookmarksOpen
        if self.bookmarksOpen:
            self.bmView.show()
            self.bookmarkButton.load(self.iconFolder + '/Bookmark_empty_font_awesome.svg')
        else:
            self.bmView.hide()
            self.bookmarkButton.load(self.iconFolder + '/Bookmark_font_awesome.svg')

    def toggleTrajectory(self):
        self.trajectoryEnabled = not self.trajectoryEnabled
        if self.trajectoryEnabled:
            self.parent().showTrajectories(True)
            # self.bookmarkButton.load(self.iconFolder + '/Bookmark_empty_font_awesome.svg')
        else:
            self.parent().showTrajectories(False)
            # self.bookmarkButton.load(self.iconFolder + '/Bookmark_font_awesome.svg')


class FullViewGraphicsView(QtGui.QGraphicsView):

    def __init__(self, *args, **kwargs):
        super(FullViewGraphicsView, self).__init__(*args, **kwargs)


    def resizeEvent(self, event):
        super(FullViewGraphicsView, self).resizeEvent(event)

        if self.scene():
            bounds = self.scene().sceneRect()
            self.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
            self.centerOn(0, 0)



class SVGButton(QtGui.QPushButton):

    def __init__(self, svgPath=None, *args, **kwargs):
        super(SVGButton, self).__init__(*args, **kwargs)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
        self.icon = None

        self.centralWidget = QtGui.QWidget(self)
        self.setFlat(True)
        self.setContentsMargins(0,0,0,0)

        if svgPath is not None:
            self.load(svgPath)


    def load(self, svgPath):
        if self.icon is None:
            self.icon = QtSvg.QSvgWidget(svgPath, self.centralWidget)
            self.icon.setFixedSize(self.size())
        else:
            self.icon.load(svgPath)

        self.layoutBase = QtGui.QHBoxLayout(self)
        self.layoutBase.addWidget(self.icon)

    def resizeEvent(self, event):
        super(SVGButton, self).resizeEvent(event)

        if self.icon is not None:
            self.icon.setFixedSize(self.size())


class BookmarkListModel(QtGui.QStandardItemModel):
    def __init__(self, strList=None, keyList=None, idxList=None, parent=None,
                 filenameFunc=None, *args):
        """ datain: a list where each item is a row
        """
        super(BookmarkListModel, self).__init__(parent)

        if strList is not None\
        and keyList is not None\
        and idxList is not None:
            if len(strList) == len(keyList) == len(idxList):
                self.strList = strList
                self.keyList = keyList
                self.idxList = idxList
            else:
                self.strList = []
                self.keyList = []
                self.idxList = []
        else:
            self.strList = []
            self.keyList = []
            self.idxList = []

        if filenameFunc is not None:
            self.setFilenameFunction(filenameFunc)
            self.load()
        else:
            self.filenameFunction = None


    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.strList)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self.strList[index.row()]
        else:
            return None

    def addItem(self, str, key, idx):
        self.strList += [str]
        self.keyList += [key]
        self.idxList += [idx]
        self.appendRow(QtGui.QStandardItem(str))
        # self.dataChanged.emit()

    def removeItem(self, listIdx):
        del self.strList[listIdx]
        del self.keyList[listIdx]
        del self.idxList[listIdx]
        self.takeRow(listIdx)


    def getItem(self, listIdx):
        return self.strList[listIdx], \
               self.keyList[listIdx], \
               self.idxList[listIdx]

    def flags(self, *args, **kwargs):
        flags = super(BookmarkListModel, self).flags(*args, **kwargs)
        return flags | QtCore.Qt.ItemIsEditable

    def setFilenameFunction(self, func):
        self.filenameFunction = func

    def save(self, filename=None):
        if filename is not None:
            fn = filename

        elif self.filenameFunction is not None:
            fn = self.filenameFunction()

        else:
            raise ValueError("Neither filename given, nor self.filenameFunction set. Cannot save bookmarks")

        with open(fn, 'w') as f:
            json.dump([self.strList,
                       self.keyList,
                       self.idxList], f)

    def load(self, filename=None):
        if filename is not None:
            fn = filename

        elif self.filenameFunction is not None:
            fn = self.filenameFunction()

        else:
            raise ValueError("Neither filename given, nor self.filenameFunction set. Cannot load bookmarks")

        if os.path.exists(fn):
            with open(fn, 'r') as f:
                raw = json.load(f)

            while self.strList:
                self.removeItem(0)

            for str, key, idx in zip(*raw):
                self.addItem(str, key, idx)


class bookmarkView(QtGui.QWidget):
    def __init__(self, fullViewDialog, videoTagger, *args, **kwargs):
        super(bookmarkView, self).__init__(*args, **kwargs)


        self.iconFolder = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            os.path.pardir,
                            'icon')

        self.videoTagger = videoTagger
        self.fullViewDialog = fullViewDialog

        self.baseLayout = QtGui.QVBoxLayout(self)
        self.baseLayout.setContentsMargins(0,0,0,0)
        self.headerLabel = QtGui.QLabel(self)
        self.headerLabel.setText("Bookmarks")
        self.buttonWidget = QtGui.QWidget(self)
        self.buttonLayout = QtGui.QHBoxLayout(self.buttonWidget)

        self.undoButton = SVGButton(self.buttonWidget)
        self.undoButton.load(self.iconFolder + '/Reply_font_awesome.svg')
        self.undoButton.setToolTip("undo jumping to bookmark")
        self.undoButton.clicked.connect(self.undoJump)
        self.undoButton.setFixedSize(20, 20)

        self.addButton = SVGButton(self.buttonWidget)
        self.addButton.load(self.iconFolder + '/Plus_font_awesome.svg')
        self.addButton.setToolTip("add bookmark")
        self.addButton.clicked.connect(self.addBookmark)
        self.addButton.setFixedSize(20, 20)

        self.removeButton = SVGButton(self.buttonWidget)
        self.removeButton.load(self.iconFolder + '/Minus_font_awesome.svg')
        self.removeButton.setToolTip("remove bookmark")
        self.removeButton.clicked.connect(self.removeBookmark)
        self.removeButton.setFixedSize(20, 20)


        self.buttonLayout.addWidget(self.undoButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.addButton)
        self.buttonLayout.addWidget(self.removeButton)
        self.buttonWidget.setLayout(self.buttonLayout)

        self.listView = QtGui.QListView(self)
        self.baseLayout.addWidget(self.headerLabel)
        self.baseLayout.addWidget(self.listView)
        self.baseLayout.addWidget(self.buttonWidget)

        self.lm = BookmarkListModel(parent=self,
                            filenameFunc=self.videoTagger.getBookmarksFilename)
        self.listView.setModel(self.lm)
        self.listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        self.listView.activated.connect(self.jumpToBookmark)
        self.listView.doubleClicked.connect(self.jumpToBookmark)

    def addItem(self, item):
        self.lm.addItem(item)

    def addBookmark(self):
        key, idx = self.videoTagger.getCurrentKey_idx()
        description = OD.StringRequestDialog.getLabel(self.fullViewDialog.centralWidget(),
                                                      "Set bookmark name")
        self.lm.addItem(description, key, idx)
        self.lm.save()

    def removeBookmark(self):
        idx = self.listView.selectionModel().currentIndex().row()
        self.lm.removeItem(idx)
        self.lm.save()

    def undoJump(self):
        pass

    def jumpToBookmark(self, mdl):
        bookmarkIdx = mdl.row()
        str, key, idx = self.lm.getItem(bookmarkIdx)
        self.videoTagger.selectVideo(key, idx)


class fullFrameLabelView(QtGui.QWidget):
    def __init__(self, fullViewDialog, videoTagger, *args, **kwargs):
        super(fullFrameLabelView, self).__init__(*args, **kwargs)


        self.iconFolder = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            os.path.pardir,
                            'icon')

        self.videoTagger = videoTagger
        self.fullViewDialog = fullViewDialog

        self.baseLayout = QtGui.QVBoxLayout(self)
        self.baseLayout.setContentsMargins(0,0,0,0)
        self.headerLabel = QtGui.QLabel(self)
        self.headerLabel.setText("Labels covering the entire frame")
        self.buttonWidget = QtGui.QWidget(self)
        self.buttonLayout = QtGui.QHBoxLayout(self.buttonWidget)

        self.removeButton = SVGButton(self.buttonWidget)
        self.removeButton.load(self.iconFolder + '/Minus_font_awesome.svg')
        self.removeButton.setToolTip("remove bookmark")
        self.removeButton.clicked.connect(self.removeLabel)
        self.removeButton.setFixedSize(20, 20)


        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.removeButton)
        self.buttonWidget.setLayout(self.buttonLayout)

        self.listView = QtGui.QListWidget(self)
        self.baseLayout.addWidget(self.headerLabel)
        self.baseLayout.addWidget(self.listView)
        self.baseLayout.addWidget(self.buttonWidget)

        # self.lm = QtGui.QStandardItemModel()
        # self.listView.setModel(self.lm)
        # self.listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        self.listView.activated.connect(self.editLabel)
        self.listView.doubleClicked.connect(self.editLabel)

    def clear(self):
        self.listView.clear()

    def addItem(self, labelStr, color):
        self.listView.addItem(labelStr)
        self.listView.item(self.listView.count() - 1).setForeground(color)


    # def addBookmark(self):
    #     key, idx = self.videoTagger.getCurrentKey_idx()
    #     description = OD.StringRequestDialog.getLabel(self.fullViewDialog.centralWidget(),
    #                                                   "Set bookmark name")
    #     self.lm.addItem(description, key, idx)
    #     self.lm.save()

    def removeLabel(self):
        idx = self.listView.selectionModel().currentIndex().row()
        self.lm.removeItem(idx)
        self.lm.save()

    def undoJump(self):
        pass

    def editLabel(self, mdl):
        behaviour = self.listView.item(mdl.row()).data(0)
        self.videoTagger.registerLastLabelInteraction(behaviour)
        self.videoTagger.menu.exec_(QtGui.QCursor.pos())





class MouseFilterObj(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.MouseMove:
            mousePos = event.pos()
            if self.parent.hud.rect().contains(mousePos):
                self.parent.hud.setVisible(False)
            else:
                self.parent.hud.setVisible(True)
        if event.type() == QtCore.QEvent.Type.GraphicsSceneMouseMove:
            mousePos = self.parent.hud.mapFromGlobal(event.screenPos())
            if self.parent.hud.rect().contains(mousePos):
                self.parent.hud.setVisible(False)
            else:
                self.parent.hud.setVisible(True)


        return False
