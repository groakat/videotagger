from PySide import QtCore, QtGui
from pyTools.gui.fullViewDialog_auto import Ui_Dialog

class FullViewDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(FullViewDialog, self).__init__(parent)
        # Usual setup stuff. Set up the user interface from Designer
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.scene = None

        self.ui.graphicsView.setMouseTracking(True)

    def setScene(self, scene):
        self.scene = scene
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.fitInView(self.scene.sceneRect())

    def resizeEvent(self, event):
        super(FullViewDialog, self).resizeEvent(event)
        if self.scene:
            self.ui.graphicsView.fitInView(self.scene.sceneRect())