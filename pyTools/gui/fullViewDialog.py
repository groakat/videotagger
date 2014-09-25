from PySide import QtCore, QtGui, QtSvg
from pyTools.gui import fullViewDialog_auto
from pyTools.gui.fullViewDialog_auto import Ui_Dialog
import pyTools.videoTagger.hud as HUD

class FullViewDialog(QtGui.QMainWindow):
    def __init__(self, parent, previewWidget=None):
        super(FullViewDialog, self).__init__(parent)
        # Usual setup stuff. Set up the user interface from Designer
        # self.ui = Ui_Dialog()
        self.previewWidget = previewWidget
        self.cw = QtGui.QWidget(self)
        self.setCentralWidget(self.cw)
        l = QtGui.QHBoxLayout(self.cw)
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical, self.cw)
        self.splitter.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                   QtGui.QSizePolicy.MinimumExpanding)
        l.addWidget(self.splitter)
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
        self.mouseFilter = MouseFilterObj(self)
        self.installEventFilter(self.mouseFilter)
        # self.hud.installEventFilter(self.mouseFilter)

    def setupUI(self):
        if self.previewWidget is not None:
            prevDummyWidget = QtGui.QWidget()
            prevLayout = QtGui.QHBoxLayout(prevDummyWidget)
            prevLayout.addWidget(self.previewWidget)

        self.graphicsView = QtGui.QGraphicsView()
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setMouseTracking(True)

        self.splitter.addWidget(prevDummyWidget)
        self.splitter.addWidget(self.graphicsView)

        self.setGeometry(QtCore.QRect(0,0,800, 600))


    def setupHUD(self):
        self.hud.setColor(QtGui.QColor(255,255,255,50))
        self.hud.setGeometry(QtCore.QRect(10, 10, 841, 50))

    def setupControlWidget(self):
        self.controlWidget = QtGui.QWidget(self)
        layout = QtGui.QHBoxLayout(self.controlWidget)

        self.fdvButton = SVGButton(self.controlWidget)
        self.fdvButton.load('../icon/Bar_chart_font_awesome.svg')
        self.fdvButton.setToolTip("Open hierarchical view of labels")
        self.fdvButton.setFixedSize(20, 20)
        self.fdvButton.clicked.connect(self.parent().openFDV)
        layout.addWidget(self.fdvButton)

        self.timelineButton = SVGButton(self.controlWidget)
        self.timelineButton.load('../icon/Align_justify_font_awesome.svg')
        self.timelineButton.setToolTip("Open timeline panel (not implemented yet)")
        self.timelineButton.setFixedSize(20, 20)
        layout.addWidget(self.timelineButton)

        layout.addSpacing(40)
        layout.addStretch()

        self.fullResButton = SVGButton(self.controlWidget)
        self.fullResButton.load('../icon/Search_font_awesome.svg')
        self.fullResButton.setToolTip("Show current frame in full resolution [SPACE]")
        self.fullResButton.setFixedSize(20, 20)
        self.fullResButton.clicked.connect(self.parent().displayFullResolutionFrame)
        layout.addWidget(self.fullResButton)

        layout.addSpacing(30)

        self.playButton = SVGButton(self.controlWidget)
        self.playButton.load('../icon/Play_font_awesome.svg')
        self.playButton.setToolTip("Play video")
        self.playButton.setFixedSize(20, 20)
        self.playButton.clicked.connect(self.playButtonClick)
        layout.addWidget(self.playButton)

        layout.addSpacing(30)

        self.modeButton = SVGButton(self.controlWidget)
        self.modeButton.load('../icon/Edit_font_awesome.svg')
        self.modeButton.setToolTip("Switch to 'Edit-mode' [CTRL + RETURN]")
        self.modeButton.setFixedSize(20, 20)
        self.modeButton.clicked.connect(self.toggleEditModeCheckbox)
        layout.addWidget(self.modeButton)

        layout.addStretch()

        self.saveButton = SVGButton(self.controlWidget)
        self.saveButton.load('../icon/Save_font_awesome.svg')
        self.saveButton.setToolTip("Save all annotations [CTRL + S]")
        self.saveButton.setFixedSize(20, 20)
        self.saveButton.clicked.connect(self.parent().saveAll)
        layout.addWidget(self.saveButton)

        self.settingsButton = SVGButton(self.controlWidget)
        self.settingsButton.load('../icon/Cogs_font_awesome.svg')
        self.settingsButton.setToolTip("Open settings")
        self.settingsButton.setFixedSize(20, 20)
        self.settingsButton.clicked.connect(self.parent().openKeySettings)
        layout.addWidget(self.settingsButton)

        self.startVideoButton = SVGButton(self.controlWidget)
        self.startVideoButton.load('../icon/Refresh_font_awesome.svg')
        self.startVideoButton.setToolTip("Restart video event loop")
        self.startVideoButton.setFixedSize(20, 20)
        self.startVideoButton.clicked.connect(self.parent().startVideo)
        layout.addWidget(self.startVideoButton)


        self.splitter.addWidget(self.controlWidget)


    def setScene(self, scene):
        self.scene = scene
        self.graphicsView.setScene(self.scene)
        self.graphicsView.fitInView(self.scene.sceneRect())
        self.scene.installEventFilter(self.mouseFilter)

    def resizeEvent(self, event):
        super(FullViewDialog, self).resizeEvent(event)
        self.wasResized = True

        bounds = self.graphicsView.scene().sceneRect()
        self.graphicsView.fitInView(bounds, QtCore.Qt.KeepAspectRatio)
        self.graphicsView.centerOn(0, 0)

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
            self.playButton.load('../icon/Pause_font_awesome.svg')
            self.playButton.setToolTip("Pause video")
            self.parent().playback()
        else:
            self.playButton.load('../icon/Play_font_awesome.svg')
            self.playButton.setToolTip("Play video")
            self.parent().stopPlayback()

        self.playing = not self.playing

    def toggleEditModeCheckbox(self):
        self.editing = not self.editing

        if self.editing:
            self.modeButton.load('../icon/Edit_font_awesome.svg')
            self.modeButton.setToolTip("Switch to 'Edit-mode' [CTRL + RETURN]")
        else:
            self.modeButton.load('../icon/Plus_font_awesome.svg')
            self.modeButton.setToolTip("Switch to 'Additive-mode' [CTRL + RETURN]")

        self.parent().toggleEditModeCheckbox()





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
