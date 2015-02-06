from PySide import QtGui, QtCore
import pyTools.videoTagger.modifyableRect as MR
import warnings
import qimage2ndarray as qim2np

from collections import OrderedDict

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

        # self.parent.removeEventFilter(self.parentEventHandler)
        super(OverlayDialogBase, self).close()

    def keyPressEvent(self, event):
        print "keyPressEvent"
        if event.key() == QtCore.Qt.Key_Escape:
            self.ret = None
            if self.eventLoop is not None:
                self.eventLoop.exit()
            else:
                self.close()
        else:
            super(OverlayDialogBase, self).keyPressEvent(event)

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

            return True


class OverlayDialogWidgetBase(OverlayDialogBase):
    def __init__(self, parent, widget, *args,
                 **kwargs):

        self.widget = widget
        super(OverlayDialogWidgetBase, self).__init__(parent=parent, *args,
                                                      **kwargs)

        self.setupContent()
        self.setupLayout()
        self.connectSignals()

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("OK")

        self.contentLayout.addWidget(self.widget)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)


    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertSpacing(0, 30)
        # self.layout.addWidget(self.messageLabel)
        # self.layout.addWidget(self.content)
        # self.layout.addWidget(self.button)
        self.layout.addWidget(self.content)
        self.layout.insertSpacing(-1, 30)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertSpacing(0, 30)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertSpacing(-1, 30)
        self.setLayout(self.outerLayout)

    def connectSignals(self):
        self.button.clicked.connect(self.setReturnValue)

    def _setReturnValue(self):
        self.ret = True

    @staticmethod
    def getUserInput(parent, widget):
        od = OverlayDialogWidgetBase(parent, widget)
        od.exec_()
        return od.ret



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

        scrollArea = QtGui.QScrollArea(self)
        scrollArea.setWidget(w)
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        return scrollArea

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("OK")
        self.messageLabel = QtGui.QLabel(self.content)
        self.messageLabel.setText("Which class do you want to assign to this label?")
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
        self.FDV.show()
        # self.setupContent()
        # self.setupLayout()

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("Close")
        self.messageLabel = QtGui.QLabel(self.content)
        self.messageLabel.setText("Hierarchical Frame View")
        if self.FDV is not None:
            self.FDV = self.FDV

        self.contentLayout.addWidget(self.messageLabel)
        if self.FDV is not None:
            self.contentLayout.addWidget(self.FDV)
        self.contentLayout.addWidget(self.button)


        self.content.setLayout(self.contentLayout)

        # self.content.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
        #                            QtGui.QSizePolicy.MinimumExpanding)

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
        # od = FDVShowDialog(parent, FDV)
        od = OverlayDialogWidgetBase(parent, FDV)
        od.exec_()


        # return od.ret


class ControlsSettingDialog(OverlayDialogBase):
    def __init__(self, parent, keyMap=None, stepSize=None, *args, **kwargs):
        self.FDV = None
        super(ControlsSettingDialog, self).__init__(parent=parent, *args, **kwargs)
        self.keyMap = None
        self.stepSize = None
        self.keyWidgets = dict()
        self.stepWidgets = dict()

        self.setSettings_(keyMap, stepSize)

        self.setupContent()
        self.setupLayout()
        self.connectSignals()


    def _setReturnValue(self):
        for k in self.keyMap:
            self.keyMap[k] = self.keyWidgets[k].keySequence

        for k in self.stepSize:
            if k != 'allow-steps':
                self.stepSize[k] = int(self.stepWidgets[k].text())

        self.ret = {'keyMap': self.keyMap,
                    'stepSize': self.stepSize}


    def setSettings_(self, keyMap, stepSize):
        if keyMap is None:
            self.keyMap = OrderedDict()
            self.keyMap["stop"] = QtGui.QKeySequence(QtCore.Qt.Key_F)
            self.keyMap["step-f"] = QtGui.QKeySequence(QtCore.Qt.Key_G)
            self.keyMap["step-b"] = QtGui.QKeySequence(QtCore.Qt.Key_D)
            self.keyMap["fwd-1"] = QtGui.QKeySequence(QtCore.Qt.Key_T)
            self.keyMap["fwd-2"] = QtGui.QKeySequence(QtCore.Qt.Key_V)
            self.keyMap["fwd-3"] = QtGui.QKeySequence(QtCore.Qt.Key_B)
            self.keyMap["fwd-4"] = QtGui.QKeySequence(QtCore.Qt.Key_N)
            self.keyMap["fwd-5"] = QtGui.QKeySequence(QtCore.Qt.Key_H)
            self.keyMap["fwd-6"] = QtGui.QKeySequence(QtCore.Qt.Key_J)
            self.keyMap["bwd-1"] = QtGui.QKeySequence(QtCore.Qt.Key_E)
            self.keyMap["bwd-2"] = QtGui.QKeySequence(QtCore.Qt.Key_X)
            self.keyMap["bwd-3"] = QtGui.QKeySequence(QtCore.Qt.Key_Z)
            self.keyMap["bwd-4"] = QtGui.QKeySequence(QtCore.Qt.Key_Backslash)
            self.keyMap["bwd-5"] = QtGui.QKeySequence(QtCore.Qt.Key_S)
            self.keyMap["bwd-6"] = QtGui.QKeySequence(QtCore.Qt.Key_A)
            self.keyMap["escape"] = QtGui.QKeySequence(QtCore.Qt.Key_Escape)
            self.keyMap["anno-1"] = QtGui.QKeySequence(QtCore.Qt.Key_1)
            self.keyMap["anno-2"] = QtGui.QKeySequence(QtCore.Qt.Key_2)
            self.keyMap["anno-3"] = QtGui.QKeySequence(QtCore.Qt.Key_3)
            self.keyMap["anno-4"] = QtGui.QKeySequence(QtCore.Qt.Key_3)
            self.keyMap["erase-anno"] = QtGui.QKeySequence(QtCore.Qt.Key_Q)
            self.keyMap["info"] = QtGui.QKeySequence(QtCore.Qt.Key_I)
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
        self.button.setText("OK")
        self.messageLabel = QtGui.QLabel(self)
        self.messageLabel.setText("Select Keyboard Sequences and Stepsizes")

        self.populateKeySequencesFromSettings()

        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.keySelectWidget)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    def populateKeySequencesFromSettings(self):
        self.keySelectWidget = QtGui.QWidget(self.content)
        self.keySelectLayout = QtGui.QGridLayout()
        row = 0
        self.keyWidgets = dict()
        self.stepWidgets = dict()

        for k, keymap in self.keyMap.items():
            lbl = QtGui.QLabel(self.content)
            lbl.setText(k)
            # if type(keymap) is  QtGui.QKeySequence:
            #     keymap = QtGui.QKeySequence(keymap)
            # else:
            #     print  type(keymap)
            print keymap, keymap.toString()

            keySeqEdit = KeySequenceEdit(keymap, self.content)

            self.keySelectLayout.addWidget(lbl, row, 0)
            self.keySelectLayout.addWidget(keySeqEdit, row, 1)

            self.keyWidgets[k] = keySeqEdit

            if k in self.stepSize.keys():
                stepSize = self.stepSize[k]
                stepEdit = QtGui.QLineEdit(self.content)
                stepEdit.setText(str(stepSize))
                self.keySelectLayout.addWidget(stepEdit, row, 2)
                self.stepWidgets[k] = stepEdit

            row += 1

        self.keySelectWidget.setLayout(self.keySelectLayout)

    @staticmethod
    def getSelection(parent, keyMap, stepSize):
        od = ControlsSettingDialog(parent, keyMap, stepSize)
        od.exec_()
        return od.ret

class StringRequestDialog(OverlayDialogBase):
    def __init__(self, parent, message=None, *args, **kwargs):
        super(StringRequestDialog, self).__init__(parent=parent, *args, **kwargs)

        if message is not None:
            self.setMessage(message)
        else:
            self.message = None

        self.setupContent()
        self.setupLayout()
        self.connectSignals()

    def _setReturnValue(self):
        self.ret = self.lineEdit.text()

    def setMessage(self, str):
        self.message = str

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("OK")
        self.messageLabel = QtGui.QLabel(self.content)
        if self.message is not None:
            self.messageLabel.setText(self.message)
        self.lineEdit = QtGui.QLineEdit(self.content)


        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.lineEdit)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertStretch(0)
        self.layout.addWidget(self.content)
        self.layout.insertStretch(-1)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertStretch(0)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertStretch(-1)
        self.setLayout(self.outerLayout)

    @staticmethod
    def getLabel(parent, message):
        od = StringRequestDialog(parent, message)
        od.exec_()
        return od.ret


class ColorRequestDialog(OverlayDialogBase):
    def __init__(self, parent, message=None, *args, **kwargs):
        super(ColorRequestDialog, self).__init__(parent=parent, *args, **kwargs)

        if message is not None:
            self.setMessage(message)
        else:
            self.message = None

        self.labelColor = QtGui.QColor(0,0,0)

        self.setupContent()
        self.setupLayout()
        self.connectSignals()

    def _setReturnValue(self):
        self.ret = self.labelColor

    def setMessage(self, str):
        self.message = str

    def connectSignals(self):
        super(ColorRequestDialog, self).connectSignals()
        self.colorButton.clicked.connect(self.selectColor)

    def setupContent(self):
        self.content = QtGui.QWidget(self)
        self.contentLayout  = QtGui.QVBoxLayout()

        self.button = QtGui.QPushButton(self.content)
        self.button.setText("OK")
        self.messageLabel = QtGui.QLabel(self.content)
        if self.message is not None:
            self.messageLabel.setText(self.message)

        self.colorWidget = QtGui.QWidget(self)
        self.colorLayout = QtGui.QHBoxLayout(self.colorWidget)
        self.colorLabel = QtGui.QLabel(self.colorWidget)
        self.colorLabel.setText("")
        # self.setColor(self.labelColor)
        self.colorButton = QtGui.QPushButton(self.colorWidget)
        self.colorButton.setText("Select Colour")
        self.colorLayout.addWidget(self.colorLabel)
        self.colorLayout.addWidget(self.colorButton)


        self.contentLayout.addWidget(self.messageLabel)
        self.contentLayout.addWidget(self.colorWidget)
        self.contentLayout.addWidget(self.button)

        self.content.setLayout(self.contentLayout)

    def setupLayout(self):
        self.layout = QtGui.QVBoxLayout()

        self.layout.insertStretch(0)
        self.layout.addWidget(self.content)
        self.layout.insertStretch(-1)

        self.outerLayout = QtGui.QHBoxLayout(self)
        self.outerLayout.insertStretch(0)
        self.outerLayout.addLayout(self.layout)
        self.outerLayout.insertStretch(-1)
        self.setLayout(self.outerLayout)

    def selectColor(self):
        self.labelColor = QtGui.QColorDialog.getColor()
        self.setColor(self.labelColor)

    def setLabelColor(self, color):
        self.colorLabel.setAutoFillBackground(True)
        colourStyle = "#colorLabel {{background-color: {0} }}".format(color.name())
        self.colorLabel.setStyleSheet(colourStyle)


        # palette = self.colorLabel.palette()
        # palette.setColor(self.colorLabel.backgroundRole(), color)
        # palette.setColor(self.colorLabel.foregroundRole(), color)
        # self.colorLabel.setPalette(palette)

    @staticmethod
    def getColor(parent, message):
        od = ColorRequestDialog(parent, message)
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



