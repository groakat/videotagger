from PySide import QtCore, QtGui
from pyTools.gui import fullViewDialog_auto
from pyTools.gui.fullViewDialog_auto import Ui_Dialog
import pyTools.videoPlayer.hud as HUD

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

    def setScene(self, scene):
        self.scene = scene
        self.graphicsView.setScene(self.scene)
        self.graphicsView.fitInView(self.scene.sceneRect())
        self.scene.installEventFilter(self.mouseFilter)

    def resizeEvent(self, event):
        super(FullViewDialog, self).resizeEvent(event)
        if self.scene:
            self.graphicsView.fitInView(self.scene.sceneRect())

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
