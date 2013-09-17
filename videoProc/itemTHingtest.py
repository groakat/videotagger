#!/usr/bin/python
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class SlotItem(QGraphicsRectItem):
    SIZE = 40
    def __init__(self, pos):
        QGraphicsRectItem.__init__(self)
        self.setRect(pos.x(), pos.y(), self.SIZE, self.SIZE)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(Qt.yellow)
        QGraphicsEllipseItem.hoverEnterEvent(self, event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(Qt.green)
        QGraphicsEllipseItem.hoverLeaveEvent(self, event)


class DiagramScene(QGraphicsScene):
    def __init__(self, *args):
        QGraphicsScene.__init__(self, *args)
        self.addItem(SlotItem(QPointF(30,30)))
        self.addItem(QGraphicsTextItem("Hover events on item not triggered if mouse button pressed"))


class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.scene = QGraphicsScene()
        self.scene.addItem(SlotItem(QPointF(30,30)))
        self.scene.addItem(QGraphicsTextItem("Hover events on item not triggered if mouse button pressed"))
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(self.view)

def main(args):
    app = QApplication(args)
    mainWindow = MainWindow()
    mainWindow.setGeometry(100, 100, 500, 40)
    mainWindow.show()

    # Qt Main loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)