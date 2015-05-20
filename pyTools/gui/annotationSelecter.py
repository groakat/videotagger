__author__ = 'peter'

import pyTools.videoTagger.overlayDialog as OD
import pyTools.videoProc.annotation as A

from PySide import QtCore, QtGui
import sys


class Test(QtGui.QMainWindow):

    def __init__(self):
        super(Test, self).__init__()

        self.annoSelector = AnnotationSelecter(self)

        self.setCentralWidget(self.annoSelector)
        self.show()

        import pyTools.videoProc.annotation as A

        a = A.Annotation()
        a.loadFromFile('/media/peter/Seagate Backup Plus Drive1/peter_testCopy/WP609L_small.bhvr')
        self.annoSelector.setAnnotation(a)

class AnnotationFilterWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(AnnotationFilterWidget, self).__init__(*args, **kwargs)
        self.setupWidget()
        self.show()

    def setupWidget(self):
        layout = QtGui.QHBoxLayout()

        self.lineEdit = QtGui.QLineEdit()
        self.button = QtGui.QPushButton()
        self.button.setText("Filter")
        self.button.clicked.connect(self.buttonClicked)

        layout.addWidget(self.lineEdit)
        layout.addWidget(self.button)

        self.setLayout(layout)


    def buttonClicked(self):
        print "buttonCLick"

class AnnotationFilterCheckbox(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(AnnotationFilterCheckbox, self).__init__(*args, **kwargs)
        self.setupWidget()
        self.checked = False
        self.show()

    def setupWidget(self):
        layout = QtGui.QHBoxLayout()

        self.checkbox = QtGui.QCheckBox()
        self.checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.label = QtGui.QLabel()

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()

        self.setLayout(layout)

    def setAnnotationFilter(self, annotationFilter):
        self.annotationFilter = annotationFilter
        self.label.setText("Annotator: {0} | Behaviour {1}".format(
                            annotationFilter.annotators[0],
                            annotationFilter.behaviours[0]))

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, bool):
        if bool:
            self.checkbox.setCheckState(QtCore.Qt.CheckState.Checked)
        else:
            self.checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)


class AnnotationSelecter(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(AnnotationSelecter, self).__init__(*args, **kwargs)
        self.setupWidget()
        self.show()

    def setupWidget(self):
        layout = QtGui.QVBoxLayout()
        self.filterWidget = AnnotationFilterWidget()

        self.annotationListBox = QtGui.QScrollArea(self)
        self.annotationListWidget = QtGui.QWidget(self)
        self.annotationLayout = QtGui.QVBoxLayout(self)

        self.annotationListWidget.setLayout(self.annotationLayout)
        self.annotationListBox.setWidget(self.annotationListWidget)
        self.annotationListBox.setWidgetResizable(True)

        self.buttonWidget = QtGui.QWidget()
        self.buttonLayout = QtGui.QHBoxLayout()
        self.pb_selectAll = QtGui.QPushButton()
        self.pb_selectAll.setText("Select all")
        self.pb_selectAll.clicked.connect(self.selectAll)
        self.pb_deselectAll = QtGui.QPushButton()
        self.pb_deselectAll.clicked.connect(self.deselectAll)
        self.pb_deselectAll.setText("Deselect all")
        self.buttonLayout.addWidget(self.pb_selectAll)
        self.buttonLayout.addWidget(self.pb_deselectAll)
        self.buttonWidget.setLayout(self.buttonLayout)

        layout.addWidget(self.filterWidget)
        layout.addWidget(self.annotationListBox)
        layout.addWidget(self.buttonWidget)

        self.setLayout(layout)

    def selectAll(self):
        for afc in self.AnnotationFilterCheckboxes:
            afc.setChecked(True)

    def deselectAll(self):
        for afc in self.AnnotationFilterCheckboxes:
            afc.setChecked(False)

    def submit(self):
        self.close()

    def setAnnotation(self, anno):
        self.anno = anno
        self.filterTuples = anno.extractAllFilterTuples()

        self.AnnotationFilterCheckboxes = []
        for af in self.filterTuples:
            alw = AnnotationFilterCheckbox()
            annoFilter = A.AnnotationFilter(vials=None,
                                            annotators=[af[0]],
                                            behaviours=[af[1]])
            alw.setAnnotationFilter(annoFilter)
            self.AnnotationFilterCheckboxes += [alw]

            self.annotationLayout.addWidget(alw)

    def getSelectedAnnotations(self):
        annoFilters = []
        for afc in self.AnnotationFilterCheckboxes:
            if afc.isChecked():
                annoFilters += [afc.annotationFilter]

        return sorted(annoFilters)

    @staticmethod
    def getAnnotationSelection(parent, annotation):
        annoSelect = AnnotationSelecter(parent)
        annoSelect.setAnnotation(annotation)

        ret = OD.OverlayDialogWidgetBase.getUserInput(parent, annoSelect)

        return annoSelect.getSelectedAnnotations()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    w = Test()
    sys.exit(app.exec_())