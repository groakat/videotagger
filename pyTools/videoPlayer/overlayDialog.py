from PySide import QtGui, QtCore
import pyTools.videoPlayer.modifyableRect as MR
import warnings
import qimage2ndarray as qim2np

class OverlayDialogBase(QtGui.QWidget):

    def __init__(self, parent=None, *args, **kwargs):
        super(OverlayDialogBase, self).__init__(parent, *args, **kwargs)
        self.parent = parent
        self.setColor(QtGui.QColor(255,255,255,200))

        self.ret = None
        self.layout = None
        self.button = None
        self.messageLabel = None
        self.content = None
        self.outerLayout = None
        self.contentLayout = None
        self.returnValueSet = False
        self.eventLoop = QtCore.QEventLoop()

        self.closeHint = QtGui.QLabel(self)
        self.closeHint.setText("Close/Abort with [esc]")
        self.closeHint.adjustSize()

        self.setGeometry(self.parent.geometry())
        # self.setGeometry(QtCore.QRect(0,0,100,100))
        self.parentEventHandler = OverlayDialogBase.ParentEventHandler(self)
        self.parent.installEventFilter(self.parentEventHandler)
        #
        # self.setupContent()
        # self.setupLayout()

        self.show()
        self.setFocus()


    def exec_(self):
        self.eventLoop.exec_()
        self.close()

    @staticmethod
    def getChoice(parent):
        od = OverlayDialogBase(parent)
        od.exec_()
        return od.ret

    def setColor(self, color):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    def _setReturnValue(self):
        raise NotImplementedError()

    def setReturnValue(self):
        self._setReturnValue()
        self.eventLoop.exit()
        self.returnValueSet = True

    def connectSignals(self):
        self.button.clicked.connect(self.setReturnValue)

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("Alright'o")
        self.messageLabel = QtGui.QLabel(self.content)
        self.messageLabel.setText("What's you want?")
        self.autoCompleteBox = MR.AutoCompleteComboBox(self.content)

        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.autoCompleteBox)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertStretch(0)
        # self.layout.addWidget(self.messageLabel)
        # self.layout.addWidget(self.content)
        # self.layout.addWidget(self.button)
        self.layout.addWidget(self.content)
        self.layout.insertStretch(-1)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertStretch(0)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertStretch(-1)
        self.setLayout(self.outerLayout)

    def close(self):
        if not self.returnValueSet:
            self.ret = None

        if self.eventLoop is not None:
            self.eventLoop.exit()

        self.parent.removeEventFilter(self.parentEventHandler)
        super(OverlayDialogBase, self).close()

    def keyPressEvent(self, event):
        print "keyPressEvent"
        if event.key() == QtCore.Qt.Key_Escape:
            self.ret = None
            if self.eventLoop is not None:
                self.eventLoop.exit()
            else:
                self.close()

    class ParentEventHandler(QtCore.QObject):
        def __init__(self, overlayDialog):
            super(OverlayDialogBase.ParentEventHandler, self).__init__(
                                                            overlayDialog)
            self.overlayDialog = overlayDialog

        def eventFilter(self, obj, event):
            if event.type() == QtCore.QEvent.Type.Resize:
                self.overlayDialog.setGeometry(obj.geometry())

            if event.type() == QtCore.QEvent.KeyPress\
            or event.type() == QtCore.QEvent.KeyRelease:
                if event.key() == QtCore.Qt.Key_Escape:
                    self.overlayDialog.close()

            return False


class ClassSelectDialog(OverlayDialogBase):
    def __init__(self, parent, stringList=None, previews=None, *args, **kwargs):
        super(ClassSelectDialog, self).__init__(parent=parent, *args, **kwargs)
        self.previews = previews

        self.setupContent()
        self.setupLayout()
        self.connectSignals()

        if stringList is not None:
            self.setComboBoxModel(stringList)


    def _setReturnValue(self):
        self.ret = self.autoCompleteBox.currentText()

    def setComboBoxModel(self, stringList):
        self.autoCompleteBox.setModel(stringList)

    def loadImgInPreviewLabel(self, lbl, img):
        qi = qim2np.array2qimage(img)

        pixmap = QtGui.QPixmap()

        px = QtGui.QPixmap.fromImage(qi)

        lbl.setScaledContents(False)
        lbl.setPixmap(px)

        lbl.update()

    def generatePreviewLabels(self):
        w = QtGui.QWidget(self)
        layout = QtGui.QHBoxLayout(w)

#         xPos = 0
        yPos = 0

        size = 128

        if self.previews is not None:
            self.noPrevFrames = len(self.previews)
            self.prevFrameLbls = []
    #         self.prevConnectHooks = []

            for img in self.previews:
                lbl = QtGui.QLabel(w)
                layout.addWidget(lbl)
                self.prevFrameLbls += [lbl]
                self.loadImgInPreviewLabel(lbl,
                                           img)

        return w

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("Alright'o")
        self.messageLabel = QtGui.QLabel(self.content)
        self.messageLabel.setText("What's you want?")
        self.autoCompleteBox = MR.AutoCompleteComboBox(self.content)

        self.previewWidget = self.generatePreviewLabels()

        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.previewWidget)
        self.contentLayout.addWidget(self.autoCompleteBox)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    @staticmethod
    def getLabel(parent, stringList, previewImgs=None):
        od = ClassSelectDialog(parent, stringList, previewImgs)
        od.exec_()
        return od.ret



class FDVShowDialog(OverlayDialogBase):
    def __init__(self, parent, FDV=None, *args, **kwargs):
        self.FDV = None
        super(FDVShowDialog, self).__init__(parent=parent, *args, **kwargs)
        if FDV is not None:
            self.setFDV(FDV)
            self.setupContent()
            self.setupLayout()
            self.connectSignals()

    def setFDV(self, FDV):
        self.FDV = FDV
        # self.setupContent()
        # self.setupLayout()

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("Alright'o")
        self.messageLabel = QtGui.QLabel(self.content)
        self.messageLabel.setText("What's you want?")
        if self.FDV is not None:
            self.FDV = self.FDV

        self.contentLayout.addWidget(self.messageLabel)
        if self.FDV is not None:
            self.contentLayout.addWidget(self.FDV)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

        self.content.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                   QtGui.QSizePolicy.MinimumExpanding)

    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertSpacing(0, 50)
        self.layout.addWidget(self.content)
        self.layout.insertSpacing(-1, 50)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertSpacing(0, 50)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertSpacing(-1, 50)
        self.setLayout(self.outerLayout)

    @staticmethod
    def getSelection(parent, FDV):
        od = FDVShowDialog(parent, FDV)
        od.exec_()
        return od.ret


class ControlsSettingDialog(OverlayDialogBase):
    def __init__(self, parent, keyMap=None, stepSize=None, *args, **kwargs):
        self.FDV = None
        super(ControlsSettingDialog, self).__init__(parent=parent, *args, **kwargs)
        self.keyMap = None
        self.stepSize = None

        self.setSettings_(keyMap, stepSize)

        self.setupContent()
        self.setupLayout()
        self.connectSignals()

    def setSettings_(self, keyMap, stepSize):
        if keyMap is None:
            self.keyMap = { "stop": QtCore.Qt.Key_F,
                            "step-f": QtCore.Qt.Key_G,
                            "step-b": QtCore.Qt.Key_D,
                            "fwd-1": QtCore.Qt.Key_T,
                            "fwd-2": QtCore.Qt.Key_V,
                            "fwd-3": QtCore.Qt.Key_B,
                            "fwd-4": QtCore.Qt.Key_N,
                            "fwd-5": QtCore.Qt.Key_H,
                            "fwd-6": QtCore.Qt.Key_J,
                            "bwd-1": QtCore.Qt.Key_E,
                            "bwd-2": QtCore.Qt.Key_X,
                            "bwd-3": QtCore.Qt.Key_Z,
                            "bwd-4": QtCore.Qt.Key_Backslash,
                            "bwd-5": QtCore.Qt.Key_S,
                            "bwd-6": QtCore.Qt.Key_A,
                            "escape": QtCore.Qt.Key_Escape,
                            "anno-1": QtCore.Qt.Key_1,
                            "anno-2": QtCore.Qt.Key_2,
                            "anno-3": QtCore.Qt.Key_3,
                            "anno-4": QtCore.Qt.Key_3,
                            "erase-anno": QtCore.Qt.Key_Q,
                            "info": QtCore.Qt.Key_I}
        else:
            self.keyMap = keyMap

        if stepSize is None:
            self.stepSize = { "stop": 0,
                            "step-f": 1,
                            "step-b": -1,
                            "allow-steps": True,
                            "fwd-1": 1,
                            "fwd-2": 3,
                            "fwd-3": 10,
                            "fwd-4": 20,
                            "fwd-5": 40,
                            "fwd-6": 60,
                            "bwd-1": -1,
                            "bwd-2": -3,
                            "bwd-3": -10,
                            "bwd-4": -20,
                            "bwd-5": -40,
                            "bwd-6": -60}
        else:
            self.stepSize = stepSize

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self)
        self.button.setText("Alright'o")
        self.messageLabel = QtGui.QLabel(self)
        self.messageLabel.setText("What's you want?")

        self.populateKeySequencesFromSettings()

        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.keySelectWidget)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    def populateKeySequencesFromSettings(self):
        self.keySelectWidget = QtGui.QWidget(self.content)
        self.keySelectLayout = QtGui.QGridLayout()
        row = 0
        for k, keymap in self.keyMap.items():
            lbl = QtGui.QLabel(self.content)
            lbl.setText(k)
            if type(keymap) is  QtCore.Qt.Key:
                keymap = QtGui.QKeySequence(keymap)

            keySeqEdit = KeySequenceEdit(keymap, self.content)

            self.keySelectLayout.addWidget(lbl, row, 0)
            self.keySelectLayout.addWidget(keySeqEdit, row, 1)

            if k in self.stepSize.keys():
                stepSize = self.stepSize[k]
                stepEdit = QtGui.QLineEdit(self.content)
                stepEdit.setText(str(stepSize))
                self.keySelectLayout.addWidget(stepEdit, row, 2)
            row += 1

        self.keySelectWidget.setLayout(self.keySelectLayout)

    @staticmethod
    def getSelection(parent, settings):
        od = ControlsSettingDialog(parent, settings)
        od.exec_()
        return od.ret


class KeySequenceEdit(QtGui.QLineEdit):
    """
    This class is mainly inspired by
    http://stackoverflow.com/a/6665017

    """

    def __init__(self, keySequence, *args):
        super(KeySequenceEdit, self).__init__(*args)

        self.keySequence = keySequence
        self.setKeySequence(keySequence)

    def setKeySequence(self, keySequence):
        self.keySequence = keySequence
        self.setText(self.keySequence.toString(QtGui.QKeySequence.NativeText))


    def keyPressEvent(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            key = e.key()

            if key == QtCore.Qt.Key_unknown:
                warnings.warn("Unknown key from a macro probably")
                return

            # the user have clicked just and only the special keys Ctrl, Shift, Alt, Meta.
            if(key == QtCore.Qt.Key_Control or
               key == QtCore.Qt.Key_Shift or
               key == QtCore.Qt.Key_Alt or
               key == QtCore.Qt.Key_Meta):
                print("Single click of special key: Ctrl, Shift, Alt or Meta")
                print("New KeySequence:", QtGui.QKeySequence(key).toString(QtGui.QKeySequence.NativeText))
                return

            # check for a combination of user clicks
            modifiers = e.modifiers()
            keyText = e.text()
            # if the keyText is empty than it's a special key like F1, F5, ...
            print("Pressed Key:", keyText)

            if modifiers & QtCore.Qt.ShiftModifier:
                key += QtCore.Qt.SHIFT
            if modifiers & QtCore.Qt.ControlModifier:
                key += QtCore.Qt.CTRL
            if modifiers & QtCore.Qt.AltModifier:
                key += QtCore.Qt.ALT
            if modifiers & QtCore.Qt.MetaModifier:
                key += QtCore.Qt.META

            print("New KeySequence:", QtGui.QKeySequence(key).toString(QtGui.QKeySequence.NativeText))

            self.setKeySequence(QtGui.QKeySequence(key))



