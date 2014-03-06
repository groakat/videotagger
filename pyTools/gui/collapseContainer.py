import sys
from PySide import QtCore, QtGui
import pyTools.gui.collapseWidget_auto as collapse
import pyTools.gui.FrameViewWidget as FVW



class collapseWidget(QtGui.QWidget, collapse.Ui_collapseWidget):
    expandSig = QtCore.Signal()
    
    """Widget defined in Qt Designer"""
    def __init__(self, parent = None, title=None, width=900):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        # set the canvas to the Matplotlib widget
        self.setupUi()
        self.connectSignals()
        self.layHeight = 100
        if title:
            self.setTitle(title)
        else:
            self.title = "" 
            
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
#         self.setFixedHeight(250)
#         self.setFixedWidth(900)
        self.width = 900
        self.isCollapsed = False
    
    def setupUi(self):
        super(collapseWidget, self).setupUi(self)
        
        self.titleLbl = QtGui.QLabel(self)
        self.titleLbl.setGeometry(QtCore.QRect(300, 460, 55, 15))
        self.titleLbl.setStyleSheet("color: rgba(0, 0, 0, 255);\n"
"background-color: rgba(200, 200, 200, 255);\n"
"")
        self.titleLbl.setObjectName("titleLbl")
        
        self.hLine = QtGui.QFrame(self)
        self.hLine.setGeometry(QtCore.QRect(80, 460, 511, 20))
        self.hLine.setFrameShape(QtGui.QFrame.HLine)
        self.hLine.setFrameShadow(QtGui.QFrame.Sunken)
        self.hLine.setObjectName("hLine")
        self.btn_expand = QtGui.QPushButton(self)
        self.btn_expand.setGeometry(QtCore.QRect(620, 460, 16, 16))
        self.btn_expand.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("../icon/downArrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_expand.setIcon(icon1)
        self.btn_expand.setIconSize(QtCore.QSize(5, 5))
        self.btn_expand.setFlat(True)
        self.btn_expand.setObjectName("btn_expand")
        
        self.titleLbl.setText(QtGui.QApplication.translate("collapseWidget", "Test Title", None, QtGui.QApplication.UnicodeUTF8))
        
        
#         self.btn_swap.resize(10,10)
        self.btn_swap.setIconSize(QtCore.QSize(5, 5))
        self.btn_swap.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        self.btn_expand.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        
        geo = self.lay_main.geometry()
#         
        self.layHeight = geo.height()
        self.layWidth = geo.width()
        
        self.positionTitle()
        self.hideTitle()
        self.expand()
        
        
    def sizeHint(self):
        if self.isCollapsed or not self.mainWidget:
            return QtCore.QSize(self.width, 10)
        else:
            height = self.layHeight
            return QtCore.QSize(self.width, height)
        
    def minimumSizeHint(self):
        return self.sizeHint()
    
    def setTitle(self, title):        
        self.title = title
        self.titleLbl.setText(self.title)
        self.titleLbl.adjustSize()
        
    def connectSignals(self):
        self.btn_swap.clicked.connect(self.collapse)
        self.btn_expand.clicked.connect(self.expand)
        
        
    def positionTitle(self):
        bWidth = self.btn_expand.geometry().width()
        geo = self.hLine.geometry()
        lineHeight = geo.height()
        geo.setX(0)
        geo.setY(0)
        lineWidth = self.layWidth - bWidth - 5
        geo.setWidth(lineWidth)
        geo.setHeight(lineHeight)
        lineY = geo.y()
        
        self.hLine.setGeometry(geo)
                
        lblGeo = self.titleLbl.geometry()
        self.titleLbl.move(lineWidth / 2 - lblGeo.width() / 2,
                           lineY + (lineHeight / 2 - lblGeo.height() / 2))
         
        btnGeo = self.btn_expand.geometry()
        self.btn_expand.move(lineWidth + 5, 
                             lineY + (lineHeight / 2 - btnGeo.height() / 2))
        
        self.titleLbl.raise_()
        self.btn_expand.setVisible(True)
        self.hLine.setVisible(True)
        self.titleLbl.setVisible(True)
        
        
    def hideTitle(self):
        self.btn_expand.setVisible(False)
        self.hLine.setVisible(False)
        self.titleLbl.setVisible(False)
        
        
    def collapse(self):
        geo = self.lay_main.geometry()
        self.layWidth = geo.width()
        geo.setHeight(0)
        self.lay_main.setGeometry(geo)
        self.mainWidget.setVisible(False)
        
        self.positionTitle()
        self.setFixedHeight(20)
        self.isCollapsed = True
        self.updateGeometry()
        
    @QtCore.Slot()
    def expand(self):
        self.hideTitle()
        self.mainWidget.setVisible(True)

        if self.mainWidget:
#             self.setFixedHeight(self.mainWidget.sizeHint().height())
            self.setFixedHeight(self.layHeight)
        else:
            self.setFixedHeight(50)
        self.updateGeometry()
        self.expandSig.emit()
        
        
    def setMainWidget(self, w):
        try:
            self.layHeight = w.geometry().height()
        except AttributeError:
            self.layHeight = w.height()
            
            
        self.lay_main.removeWidget(self.mainWidget)
        self.mainWidget = w
        self.lay_main.insertWidget(0, self.mainWidget)        
#         self.collapse()     
        self.expand()
        self.update()
        
        
        
class collapseContainer(QtGui.QWidget):
    
    def __init__(self, parent = None, width=900):
        QtGui.QWidget.__init__(self, parent)

        self.width = width
        
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSpacing(0)
        
        spacerItem = QtGui.QSpacerItem(1,1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        
        self.widgetList = []
        
        
    def sizeHint(self):
        height = 0
        for w, col in self.widgetList:
            try:
                height += col.sizeHint().height()
            except AttributeError:
                height += col.height()
                
            
        if height < 20:
            height = 20
                
        return QtCore.QSize(self.width, height)
        
    def minimumSizeHint(self):
        return self.sizeHint()
    
    

    def addWidget(self, w, title=""):        
        col = collapseWidget(self, title, self.width)        
        col.setMainWidget(w)
        w.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        
        self.widgetList += [[w, col]]
        self.verticalLayout.insertWidget(len(self.widgetList) -1, col)
#         self.updateGeometry()
        self.setFixedHeight(self.sizeHint().height())
        
        
        
#         self.verticalLayout.addWidget(col)
        
        
    def removeWidget(self, w):
        for i in range(len(self.widgetList)):
            w_, col = self.widgetList[i]
            if w_ == w:
                self.widgetList.pop(i)
                self.verticalLayout.removeWidget(col)
                del col
                break
            
        
        self.updateGeometry()
    


class TestClass(QtGui.QMainWindow):
    
    def __init__(self):        
        QtGui.QMainWindow.__init__(self)

        self.centralwidget = collapseContainer(self, 1200)
        self.setCentralWidget(self.centralwidget)
        
        fvw0 = FVW.FrameViewWidget(self)
        fvw1 = FVW.FrameViewWidget(self)
          
        self.col = collapseContainer(self)
         
        self.col.addWidget(fvw0, "FrameViewWidget 0")
        self.col.addWidget(fvw1, "FrameViewWidget 1")
           
        self.centralwidget.addWidget(fvw0, "")
        
        #################################################################
        
#         self.tabWidget = QtGui.QTabWidget(self)
#         self.tabWidget.setGeometry(QtCore.QRect(30, 560, 1071, 251))
#         self.tabWidget.setObjectName("tabWidget")
#         self.tab_1 = QtGui.QWidget()
#         self.tab_1.setObjectName("tab_1")
#         self.tabWidget.addTab(self.tab_1, "")
#          
#         print self.tabWidget.sizeHint()
#         print self.tabWidget.minimumSizeHint()
#         print self.tabWidget.geometry()
#          
#         self.centralwidget.addWidget(self.tabWidget, "")
#         print self.tabWidget.geometry()
        
        

        self.show()   

        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    w = TestClass()
    
    sys.exit(app.exec_())