from PySide import QtGui, QtCore
import pyTools.videoPlayer.modifyableRect as MR

class OverlayDialog(QtGui.QWidget):

    def __init__(self, parent=None, *args, **kwargs):
        super(OverlayDialog, self).__init__(parent, *args, **kwargs)
        self.parent = parent
        self.setColor(QtGui.QColor(255,255,255,200))

        self.ret = None
        self.layout = None
        self.button = None
        self.messageLabel = None
        self.content = None
        self.outerLayout = None
        self.eventLoop = QtCore.QEventLoop()

        self.closeHint = QtGui.QLabel(self)
        self.closeHint.setText("Close/Abort with [esc]")
        self.closeHint.adjustSize()

        self.setGeometry(self.parent.geometry())
        # self.setGeometry(QtCore.QRect(0,0,100,100))
        self.parentEventHandler = OverlayDialog.ParentEventHandler(self)
        self.parent.installEventFilter(self.parentEventHandler)

        self.setupContent()
        self.setupLayout()
        self.show()
        self.setFocus()

        self.connectSignals()

    def exec_(self):
        self.eventLoop.exec_()
        self.close()

    @staticmethod
    def getChoice(parent):
        od = OverlayDialog(parent)
        od.exec_()
        return od.ret

    def setColor(self, color):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    def setReturnValue(self):
        self.ret = self.content.currentText()
        self.eventLoop.exit()

    def connectSignals(self):
        self.button.clicked.connect(self.setReturnValue)

    def setupContent(self):
        self.button = QtGui.QPushButton(self)
        self.button.setText("Alright'o")
        self.messageLabel = QtGui.QLabel(self)
        self.messageLabel.setText("What's you want?")
        self.content = MR.AutoCompleteComboBox(self)

    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertStretch(0)
        self.layout.addWidget(self.messageLabel)
        self.layout.addWidget(self.content)
        self.layout.addWidget(self.button)
        self.layout.insertStretch(-1)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertStretch(0)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertStretch(-1)
        self.setLayout(self.outerLayout)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.ret = None
            if self.eventLoop is not None:
                self.eventLoop.exit()
            else:
                self.close()

    class ParentEventHandler(QtCore.QObject):
        def __init__(self, parent):
            super(OverlayDialog.ParentEventHandler, self).__init__(parent)
            self.parent = parent

        def eventFilter(self, obj, event):
            if event.type() == QtCore.QEvent.Type.Resize:
                self.parent.setGeometry(obj.geometry())

            return False


class ClassSelectDialog(OverlayDialog):
    def __init__(self, parent, stringList=None, *args, **kwargs):
        super(ClassSelectDialog, self).__init__(parent=parent, *args, **kwargs)
        if stringList is not None:
            self.setComboBoxModel(stringList)

    def setComboBoxModel(self, stringList):
        self.content.setModel(stringList)

    @staticmethod
    def getLabel(parent, stringList):
        od = ClassSelectDialog(parent, stringList)
        od.exec_()
        return od.ret