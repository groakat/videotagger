import sys
import copy
import numpy as np
from PySide import QtCore, QtGui

class Test(QtGui.QMainWindow):
    def __init__(self):
        super(Test, self).__init__()


        self.setupUi(self)
        self.setupGV()
        self.connectElements()
        self.setupLabelMenu()

        self.rectY = 7
        self.initRect()

        self.show()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gv_center = QtGui.QGraphicsView(self.centralwidget)
        self.gv_center.setGeometry(QtCore.QRect(100, 60, 561, 331))
        self.gv_center.setObjectName("gv_center")
        self.pb_debug = QtGui.QPushButton(self.centralwidget)
        self.pb_debug.setGeometry(QtCore.QRect(540, 500, 94, 24))
        self.pb_debug.setObjectName("pb_debug")
        self.pb_debug.setText("push !")
        MainWindow.setCentralWidget(self.centralwidget)


    def connectElements(self):
        self.pb_debug.clicked.connect(self.buttonClick)

    def setupGV(self):
        self.overviewScene = QtGui.QGraphicsScene(self)
        # self.overviewScene.setSceneRect(0, -0.5,1, 7)

        self.gv_center.setScene(self.overviewScene)
        self.gv_center.fitInView(0, -0.5, 100, 400, QtCore.Qt.KeepAspectRatio)

    def setupLabelMenu(self):

        wa = QtGui.QWidgetAction(self)
        self.cle = ContextLineEdit(wa, self)
        wa.setDefaultWidget(self.cle)

        self.menu = QtGui.QMenu(self)
        delAction = self.menu.addAction("delete")
        self.menu.addAction(wa)

        delAction.triggered.connect(self.deleteLabel)
        wa.triggered.connect(self.lineEditChanged)

    def deleteLabel(self):
        print "deleteLabel", self.lastLabelRectContext

    def lineEditChanged(self):
        print "lineEditChanged", self.lastLabelRectContext
        self.menu.hide()
        print self.cle.text()

    def registerLastLabelRectContext(self, labelRect):
        self.lastLabelRectContext = labelRect

    def initRect(self):
        self.overviewScene.addLine(-5, self.rectY, 5, self.rectY, QtGui.QPen(QtGui.QColor(255, 0, 0)))
        self.overviewScene.addLine(-5, self.rectY + 1, 5, self.rectY + 1, QtGui.QPen(QtGui.QColor(255, 0, 0)))
        self.overviewScene.addLine(-5, 0, 5, 0, QtGui.QPen(QtGui.QColor(0, 255, 0)))


        self.rect = LabelRectItem(self.menu, self.registerLastLabelRectContext, "test")#lambda pos: self.v2.setSceneRect(pos.x(), pos.y(), 100, 100))
        self.rect.setRect(0, self.rectY, 100, 100)
        self.rect.setColor(QtCore.Qt.darkRed)
        self.overviewScene.addItem(self.rect)


        self.rect2 = LabelRectItem(self.menu, self.registerLastLabelRectContext, "test2")#lambda pos: self.v2.setSceneRect(pos.x(), pos.y(), 100, 100))
        self.rect2.setRect(0, self.rectY, 100, 100)
        self.rect2.setColor(QtCore.Qt.darkBlue)
        self.overviewScene.addItem(self.rect2)


    def buttonClick(self):
        newHeight = np.random.randint(1, 10)
        print(newHeight)
        geo = self.rect.rect()
        geo.setHeight(newHeight)
        self.rect.setRect(geo)

        self.rect.activate()

        # self.normalizeSubplot(self.rect, newHeight, self.rectY)



class AutoCompleteLineEdit(QtGui.QLineEdit):
    def __init__(self, *args, **kwargs):
        super(AutoCompleteLineEdit, self).__init__(*args, **kwargs)
        self.comp = QtGui.QCompleter([""], self)
        self.comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(self.comp)#
        self.setModel(["hallo", "world", "we", "are"])

    def setModel(self, strList):
        self.comp.model().setStringList(strList)



class ContextLineEdit(QtGui.QWidget):
    def __init__(self, action, *args, **kwargs):
        super(ContextLineEdit, self).__init__(*args, **kwargs)
        self.action = action

        self.label = QtGui.QLabel(self)
        self.label.setText("change label to ")
        self.autoCompeleteLineEdit = AutoCompleteLineEdit(self)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.autoCompeleteLineEdit)

        self.setLayout(self.layout)

        self.autoCompeleteLineEdit.returnPressed.connect(action.trigger)

    def text(self):
        return self.autoCompeleteLineEdit.text()

    def setModel(self, strList):
        self.autoCompeleteLineEdit.setModel(strList)

# special GraphicsRectItem that is aware of its position and does something if the position is changed
class ResizeableGraphicsRectItem(QtGui.QGraphicsRectItem):
    def __init__(self, callback=None, rectChangedCallback=None, *args, **kwargs):
        super(ResizeableGraphicsRectItem, self).__init__(*args, **kwargs)
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.callback = callback
        self.rectChangedCallback = rectChangedCallback
        self.resizeActivated = False
        self.activated = True
        self.resizeBox = None
        self.resizeFunction = None
        self.resizeBoxColor = QtGui.QColor(0, 0, 0, 50)
        self.setupResizeBox()

    def setupResizeBox(self):
        self.resizeBox = QtGui.QGraphicsRectItem(self)
        self.resizeBox.setRect(self.rect().x(), self.rect().y(), 0, 0)
        self.resizeBoxPenWidth = 0
        penColor = copy.copy(self.resizeBoxColor)
        penColor.setAlpha(255)
        pen = QtGui.QPen(penColor)
        pen.setWidthF(self.resizeBoxPenWidth)
        self.resizeBox.setPen(pen)
        self.resizeBox.setBrush(QtGui.QBrush(self.resizeBoxColor))
        self.resizeBox.setFlag(QtGui.QGraphicsItem.ItemStacksBehindParent, True)

    def setResizeBoxColor(self, color):
        self.resizeBoxColor = color
        self.setupResizeBox()

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionChange and self.callback:
            self.callback(value)

        return super(ResizeableGraphicsRectItem, self).itemChange(change, value)

    def activate(self):
        self.activated = True
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemSendsScenePositionChanges)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def deactivate(self):
        self.activated = False
        self.setFlags(not QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemSendsScenePositionChanges)
        self.setCursor(QtCore.Qt.ArrowCursor)

    def contextMenuEvent(self, event):
        wa = QtGui.QWidgetAction(self.parent)
        self.cle = ContextLineEdit(self.parent)
        wa.setDefaultWidget(self.cle)

        menu = QtGui.QMenu(self.parent)
        menu.addAction("test")
        menu.addAction(wa)
        menu.exec_(event.screenPos())

    def drawResizeBox(self, x, y, width, height):
        self.resizeBox.setVisible(True)
        self.resizeActivated = True
        # self.deactivate()
        self.resizeBox.setRect(self.rect().x() + x,
                               self.rect().y() + y,
                               width,
                               height)

    def activateResizeTop(self, y):
        self.drawResizeBox(0,
                           0,
                           self.rect().width(),
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeVerCursor)

    def activateResizeBottom(self, y):
        self.drawResizeBox(0,
                           self.rect().height() - self.rect().height()/5.0,
                           self.rect().width(),
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeVerCursor)

    def activateResizeLeft(self, x):
        self.drawResizeBox(0,
                           0,
                           self.rect().width() / 5.0,
                           self.rect().height())
        self.setCursor(QtCore.Qt.SizeHorCursor)

    def activateResizeRight(self, x):
        self.drawResizeBox(self.rect().width() - self.rect().width() / 5.0,
                           0,
                           self.rect().width() / 5.0,
                           self.rect().height())
        self.setCursor(QtCore.Qt.SizeHorCursor)

    def activateResizeTopLeft(self, x, y):
        self.drawResizeBox(0,
                           0,
                           self.rect().width() / 5.0,
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeFDiagCursor)

    def activateResizeTopRight(self, x, y):
        self.drawResizeBox(self.rect().width() - self.rect().width() / 5.0,
                           0,
                           self.rect().width() / 5.0,
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeBDiagCursor)

    def activateResizeBottomLeft(self, x, y):
        self.drawResizeBox(0,
                           self.rect().height() - self.rect().height()/5.0,
                           self.rect().width() / 5.0,
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeBDiagCursor)

    def activateResizeBottomRight(self, x, y):
        self.drawResizeBox(self.rect().width() - self.rect().width() / 5.0,
                           self.rect().height() - self.rect().height()/5.0,
                           self.rect().width() / 5.0,
                           self.rect().height()/5.0)
        self.setCursor(QtCore.Qt.SizeFDiagCursor)

    def activateMove(self):
        self.drawResizeBox(self.rect().width() / 5.0,
                           self.rect().height()/5.0,
                           self.rect().width() - 2 * self.rect().width() / 5.0,
                           self.rect().height() - 2 * self.rect().height()/5.0)

        self.activate()
        self.resizeActivated = False

    def deactivateResize(self):
        self.activate()
        self.resizeActivated = False
        self.resizeBox.setVisible(False)

    def mouseCloseToTop(self, y):
        return  y < self.rect().height() / 5

    def mouseCloseToBottom(self, y):
        return y > self.rect().height() - self.rect().height() / 5

    def mouseCloseToLeft(self, x):
        return x < self.rect().width() / 5

    def mouseCloseToRight(self, x):
        return x > self.rect().width() - self.rect().width() / 5

    def mouseCloseToUpperLeftCorner(self, x, y):
        return  self.mouseCloseToTop(y) and self.mouseCloseToLeft(x)

    def mouseCloseToUpperRightCorner(self, x, y):
        return  self.mouseCloseToTop(y) and self.mouseCloseToRight(x)

    def mouseCloseToLowerLeftCorner(self, x, y):
        return  self.mouseCloseToBottom(y) and self.mouseCloseToLeft(x)

    def mouseCloseToLowerRightCorner(self, x, y):
        return  self.mouseCloseToBottom(y) and self.mouseCloseToRight(x)


    def hoverMoveEvent(self, event):
        if not self.activated:
            return

        itemPos = event.pos()
        x = itemPos.x() - self.rect().x()
        y = itemPos.y() - self.rect().y()

        if self.mouseCloseToUpperLeftCorner(x,y):
            self.activateResizeTopLeft(x, y)

        elif self.mouseCloseToUpperRightCorner(x,y):
            self.activateResizeTopRight(x, y)

        elif self.mouseCloseToLowerLeftCorner(x,y):
            self.activateResizeBottomLeft(x, y)

        elif self.mouseCloseToLowerRightCorner(x,y):
            self.activateResizeBottomRight(x, y)

        elif self.mouseCloseToTop(y):
            self.activateResizeTop(y)

        elif self.mouseCloseToBottom(y):
            self.activateResizeBottom(y)

        elif self.mouseCloseToLeft(x):
            self.activateResizeLeft(x)

        elif self.mouseCloseToRight(x):
            self.activateResizeRight(x)
        else:
            self.activateMove()

    def hoverLeaveEvent(self, event):
        self.deactivateResize()

    def resizeTop(self, dx, dy):
        rect = self.rect()
        rect.setY(rect.y() + dy)
        self.setRect(rect)
        self.activateResizeTop(self.rect().y())

    def resizeBottom(self, dx, dy):
        rect = self.rect()
        rect.setHeight(rect.height() + dy)
        self.setRect(rect)
        self.activateResizeBottom(self.rect().y())

    def resizeLeft(self, dx, dy):
        rect = self.rect()
        rect.setX(rect.x() + dx)
        self.setRect(rect)
        self.activateResizeLeft(self.rect().x())

    def resizeRight(self, dx, dy):
        rect = self.rect()
        rect.setWidth(rect.width() + dx)
        self.setRect(rect)
        self.activateResizeRight(self.rect().x())

    def resizeTopLeft(self, dx, dy):
        rect = self.rect()
        rect.setY(rect.y() + dy)
        rect.setX(rect.x() + dx)
        self.setRect(rect)
        self.activateResizeTopLeft(self.rect().x(), self.rect().y())

    def resizeTopRight(self, dx, dy):
        rect = self.rect()
        rect.setY(rect.y() + dy)
        rect.setWidth(rect.width() + dx)
        self.setRect(rect)
        self.activateResizeTopRight(self.rect().x(), self.rect().y())

    def resizeBottomLeft(self, dx, dy):
        rect = self.rect()
        rect.setHeight(rect.height() + dy)
        rect.setX(rect.x() + dx)
        self.setRect(rect)
        self.activateResizeBottomLeft(self.rect().x(), self.rect().y())

    def resizeBottomRight(self, dx, dy):
        rect = self.rect()
        rect.setHeight(rect.height() + dy)
        rect.setWidth(rect.width() + dx)
        self.setRect(rect)
        self.activateResizeBottomRight(self.rect().x(), self.rect().y())

    def mousePressEvent(self, event):
        if not self.activated:
            return

        itemPos = event.pos()
        x = itemPos.x() - self.rect().x()
        y = itemPos.y() - self.rect().y()

        if self.resizeActivated:
            if self.mouseCloseToUpperLeftCorner(x,y):
                self.resizeFunction = self.resizeTopLeft

            elif self.mouseCloseToUpperRightCorner(x,y):
                self.resizeFunction = self.resizeTopRight

            elif self.mouseCloseToLowerLeftCorner(x,y):
                self.resizeFunction = self.resizeBottomLeft

            elif self.mouseCloseToLowerRightCorner(x,y):
                self.resizeFunction = self.resizeBottomRight

            elif self.mouseCloseToTop(y):
                self.resizeFunction = self.resizeTop

            elif self.mouseCloseToBottom(y):
                self.resizeFunction = self.resizeBottom

            elif self.mouseCloseToLeft(x):
                self.resizeFunction = self.resizeLeft

            elif self.mouseCloseToRight(x):
                self.resizeFunction = self.resizeRight

    def mouseMoveEvent(self, event):
        if not self.activated:
            return

        if not self.resizeActivated:
            return super(ResizeableGraphicsRectItem, self).mouseMoveEvent(event)

        itemPos = event.pos()
        lastPos = event.lastPos()
        dx = itemPos.x() - lastPos.x()
        dy = itemPos.y() - lastPos.y()

        self.resizeFunction(dx, dy)

    def setRect(self, *args, **kwargs):
        super(ResizeableGraphicsRectItem, self).setRect(*args, **kwargs)
        if self.rectChangedCallback:
            self.rectChangedCallback()


class InfoRectItem(ResizeableGraphicsRectItem):
    def __init__(self, infoString=None, fontSize=None, callback=None, *args, **kwargs):
        super(InfoRectItem, self).__init__(callback, *args, **kwargs)

        self.infoTextItem = None
        self.infoTextFont = None
        self.setupInfoTextItem(fontSize)

        self.infoString = None
        self.setInfoString(infoString)

        self.setColor(QtGui.QColor(255,0,0))

    def setupInfoTextItem(self, fontSize):
        if self.infoTextItem is None:
            self.infoTextItem = QtGui.QGraphicsSimpleTextItem(self)

        self.infoTextItem.setVisible(False)
        if fontSize:
            self.infoTextFont = QtGui.QFont('', fontSize)
        else:
            self.infoTextFont = QtGui.QFont('', 120)

        self.infoTextItem.setFont(self.infoTextFont)
        self.infoTextItem.setPos(self.rect().x() + self.rect().width() + 10, self.rect().y())

    def setColor(self, color):
        self.setPen(QtGui.QPen(color))
        self.infoTextItem.setBrush(QtGui.QBrush(color))

    def setInfoString(self, s):
        self.infoString = s
        if self.infoString:
            self.infoTextItem.setText(self.infoString)

    def hoverEnterEvent(self, event):
        if not self.activated:
            return

        self.infoTextItem.setVisible(True)
        super(InfoRectItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.activated:
            return

        self.infoTextItem.setVisible(False)
        super(InfoRectItem, self).hoverLeaveEvent(event)

    def mouseMoveEvent(self, event):
        if not self.activated:
            return

        super(InfoRectItem, self).mouseMoveEvent(event)
        self.infoTextItem.setPos(self.rect().x() + self.rect().width() + 10, self.rect().y())

    def setRect(self, *args, **kwargs):
        super(InfoRectItem, self).setRect(*args, **kwargs)
        self.infoTextItem.setPos(self.rect().x() + self.rect().width() + 10, self.rect().y())

class LabelRectItem(InfoRectItem):
    def __init__(self, menu, contextRegisterCallback, *args, **kwargs):
        super(LabelRectItem, self).__init__(*args, **kwargs)
        self.menu = menu
        self.contextRegisterCallback = contextRegisterCallback

    def contextMenuEvent(self, event):
        if not self.activated:
            return

        if self.contextRegisterCallback:
            self.contextRegisterCallback(self)

        self.menu.exec_(event.screenPos())


class MouseInsideFilterObj(QtCore.QObject):#And this one
    def __init__(self, enterCallback, leaveCallback):
        QtCore.QObject.__init__(self)
        self.enterCallback = enterCallback
        self.leaveCallback = leaveCallback

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            self.enterCallback(obj)

        if event.type() == QtCore.QEvent.Type.Leave:
            self.leaveCallback(obj)

        return True



if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    w = Test()

    sys.exit(app.exec_())

