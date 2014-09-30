from PySide import QtCore, QtGui
import pyTools.misc.config as cfg
import json
    
class MouseFilterObj(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.increment = 0
        self.isRectangleOpen = False
        
    @cfg.logClassFunction
    def eventFilter(self, obj, event):
        cfg.log.debug("mouse event!!!!!!!!!!!!!! {0}".format(event.type()))
        if event.type() == QtCore.QEvent.Type.GraphicsSceneMousePress:
            if event.button() == QtCore.Qt.RightButton:
                self.parent.addTempAnno()
            elif event.button() == QtCore.Qt.LeftButton:
                self.parent.clickInScene(int(event.scenePos().x()),
                                          int( event.scenePos().y()))


        if event.type() == QtCore.QEvent.Type.GraphicsSceneMouseRelease:
            if event.button() == QtCore.Qt.LeftButton:
                self.parent.clickInScene(int(event.scenePos().x()),
                                          int( event.scenePos().y()))

        if event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
            self.parent.moveInScene(int(event.scenePos().x()),
                                      int( event.scenePos().y()))
            #
            # self.parent.setCropCenter(int(event.scenePos().x()),
            #                           int( event.scenePos().y()),
            #                           increment = self.increment)

            
        if event.type() == QtCore.QEvent.Leave:
            self.parent.setCropCenter(None, None, increment=self.increment)
            
        if event.type() == QtCore.QEvent.GraphicsSceneWheel:
            self.parent.mouseWheelInScene(event.delta())

            
        return False
    
    
    
class ProgressFilterObj(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.increment = 0
        
    @cfg.logClassFunction
    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.MouseButtonRelease):
            self.parent.jumpToPercent(event.x())
            
    
            

class filterObj(QtCore.QObject):
    def __init__(self, parent, keyMap=None, stepSize=None, oneClickAnnotation=None):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.setStepSize(stepSize)
        self.setKeyMap(keyMap)

        if oneClickAnnotation is None:
            self.oneClickAnnotation = [False] * 4
        else:
            self.oneClickAnnotation = [oneClickAnnotation] * 4

        self.inConstantSpeed = False
        self.orignalStepSize = self.stepSize


    def setKeyMap(self, keyMap=None):
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

    def setStepSize(self, stepSize=None):
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
            
    def swapToConstantSpeed(self, speed):
        
        if self.inConstantSpeed:
            return
        
        self.orignalStepSize = self.stepSize
        
        self.stepSize = { "stop": speed,
                        "step-f": speed,
                        "step-b": speed,
                        "allow-steps": False,
                        "fwd-1": speed,
                        "fwd-2": speed,
                        "fwd-3": speed,
                        "fwd-4": speed,
                        "fwd-5": speed,
                        "fwd-6": speed,
                        "bwd-1": speed,
                        "bwd-2": speed,
                        "bwd-3": speed,
                        "bwd-4": speed,
                        "bwd-5": speed,
                        "bwd-6": speed}
        
    def swapFromConstantSpeed(self):
        if not self.inConstantSpeed:
            self.stepSize = self.orignalStepSize
        
            
#     @cfg.logClassFunction
    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.KeyPress):
            key = event.key()
                    
            if(event.modifiers() == QtCore.Qt.ControlModifier):
                if(key == QtCore.Qt.Key_S):
                    cfg.log.info('saving all annotations')
                    self.parent.saveAll()
                    event.setAccepted(True)
            
            else:
                self.parent.showTrajectTemp = True
                    
                        
                if key == self.keyMap["stop"]:
                    # stop playback
                    if self.stepSize["allow-steps"] == "true":
                        self.parent.play = False
                    else:
                        self.parent.play = True
                        
                    self.parent.increment = self.stepSize["stop"]
                    
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["step-f"]:
                    # step-wise forward
                    if self.stepSize["allow-steps"]:
                        self.parent.play = False
                        self.parent.showNextFrame(self.stepSize["step-f"])
                    else:
                        self.parent.play = True
                        
                    self.parent.increment = self.stepSize["step-f"]
    #                 self.parent.showNextFrame(self.increment)
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                
                if key == self.keyMap["step-b"]:
                    # step-wise backward
                    if self.stepSize["allow-steps"]:
                        self.parent.play = False
                        self.parent.showNextFrame(self.stepSize["step-b"])
                    else:
                        self.parent.play = True
                        
                    self.increment = self.stepSize["step-b"]
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-1"]:
                    # real-time playback
                    self.parent.increment = self.stepSize["fwd-1"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                        
                if key == self.keyMap["bwd-1"]:
                    # real-time playback
                    self.parent.increment = self.stepSize["bwd-1"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-2"]:
                    # 
                    self.parent.increment = self.stepSize["fwd-2"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-3"]:
                    self.parent.increment = self.stepSize["fwd-3"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-4"]:
                    self.parent.increment = self.stepSize["fwd-4"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-5"]:
                    self.parent.increment = self.stepSize["fwd-5"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["fwd-6"]:
                    self.parent.increment = self.stepSize["fwd-6"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
    #                     self.tempTrajSwap = True
    #                     self.showTrajectories(False)
                    
                    
                if key == self.keyMap["bwd-2"]:
                    self.parent.increment = self.stepSize["bwd-2"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-3"]:
                    self.parent.increment = self.stepSize["bwd-3"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-4"]:
                    self.parent.increment = self.stepSize["bwd-4"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-5"]:
                    self.parent.increment = self.stepSize["bwd-5"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                if key == self.keyMap["bwd-6"]:
                    self.parent.increment = self.stepSize["bwd-6"]
                    self.parent.play = True
                    if self.parent.tempTrajSwap:
                        self.parent.tempTrajSwap = False
                        self.parent.showTrajectories(True)
                    
                        
                if key == self.keyMap["info"]:
                    cfg.log.debug("position length: {0}".format(self.parent.vh.getCurrentPositionLength()))
                    cfg.log.debug("video length: {0}".format(self.parent.vh.getCurrentVideoLength()))
                    
                if key == self.keyMap["escape"]:
                    self.parent.escapeAnnotationAlteration()
                    
                if key == self.keyMap["anno-1"]:
                    self.parent.alterAnnotation(self.parent.annotations[0]["annot"], 
                                        self.parent.annotations[0]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[0])
                    
                if key == self.keyMap["anno-2"]:
                    self.parent.alterAnnotation(self.parent.annotations[1]["annot"], 
                                        self.parent.annotations[1]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[1])
                    
                if key == self.keyMap["anno-3"]:
                    self.parent.alterAnnotation(self.parent.annotations[2]["annot"], 
                                        self.parent.annotations[2]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[2])
                    
                if key == self.keyMap["anno-4"]:
                    self.parent.alterAnnotation(self.parent.annotations[3]["annot"], 
                                        self.parent.annotations[3]["behav"],
                                        confidence=1, 
                                        oneClickAnnotation=self.oneClickAnnotation[3])
                    
                if key == self.keyMap["erase-anno"]:
                    self.parent.addingAnnotations = not self.parent.addingAnnotations
                    if not self.parent.addingAnnotations:
                        cfg.log.info("changed to erasing mode")
                        self.parent.ui.lbl_eraser.setVisible(True)                      
                                
                    else:
                        cfg.log.info("changed to adding mode")                    
                        self.parent.ui.lbl_eraser.setVisible(False)
                    
                    cfg.logGUI.info(json.dumps({"addingAnnotations": 
                                            self.parent.addingAnnotations}))
                    
#                 self.parent.ui.speed_lbl.setText("Speed: {0}x".format(self.parent.increment)) 
            
        
        return False





class shortcutHandler(QtCore.QObject):
    def __init__(self, parent, cbTarget, keyMap=None, stepSize=None, oneClickAnnotation=None):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.cbTarget = cbTarget

        self.keySC = dict()
        # self.applyShortcuts()
        self.setKeyMap(keyMap)
        self.setStepSize(stepSize)


        if oneClickAnnotation is None:
            self.oneClickAnnotation = [False] * 4
        else:
            self.oneClickAnnotation = [oneClickAnnotation] * 4

        self.inConstantSpeed = False
        self.orignalStepSize = self.stepSize


    def setKeyMap(self, keyMap=None):
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

        self.applyShortcuts()

    def setStepSize(self, stepSize=None):
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

    def deactivateShortcuts(self):
        for shortcut in self.keySC:
            shortcut.setEnabled(False)

    def activateShortcuts(self):
        for shortcut in self.keySC:
            shortcut.setEnabled(True)

    def applyShortcuts(self):
        if self.keySC == {}:
            self.keySC['stop'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['stop']),
                            self.parent, self.stop)
            self.keySC['step-f'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['step-f']),
                            self.parent, self.stepF)
            self.keySC['step-b'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['step-b']),
                            self.parent, self.stepB)
            self.keySC['fwd-1'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-1']),
                            self.parent, self.fwd1)
            self.keySC['fwd-2'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-2']),
                            self.parent, self.fwd2)
            self.keySC['fwd-3'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-3']),
                            self.parent, self.fwd3)
            self.keySC['fwd-4'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-4']),
                            self.parent, self.fwd4)
            self.keySC['fwd-5'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-5']),
                            self.parent, self.fwd5)
            self.keySC['fwd-6'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['fwd-6']),
                            self.parent, self.fwd6)
            self.keySC['bwd-1'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-1']),
                            self.parent, self.bwd1)
            self.keySC['bwd-2'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-2']),
                            self.parent, self.bwd2)
            self.keySC['bwd-3'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-3']),
                            self.parent, self.bwd3)
            self.keySC['bwd-4'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-4']),
                            self.parent, self.bwd4)
            self.keySC['bwd-5'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-5']),
                            self.parent, self.bwd5)
            self.keySC['bwd-6'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['bwd-6']),
                            self.parent, self.bwd6)
            self.keySC['escape'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['escape']),
                            self.parent, self.escape)
            self.keySC['anno-1'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['anno-1']),
                            self.parent, self.anno1)
            self.keySC['anno-2'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['anno-2']),
                            self.parent, self.anno2)
            self.keySC['anno-3'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['anno-3']),
                            self.parent, self.anno3)
            self.keySC['anno-4'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['anno-4']),
                            self.parent, self.anno4)
            self.keySC['erase-anno'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['erase-anno']),
                            self.parent, self.eraseAnno)
            self.keySC['info'] = QtGui.QShortcut(QtGui.QKeySequence(self.keyMap['info']),
                            self.parent, self.info)
            self.keySC['save'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S),
                            self.parent, self.saveAll)
            self.keySC['fullRes'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space),
                            self.parent, self.cbTarget.displayFullResolutionFrame)
            self.keySC['editMode'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Return),
                            self.parent, self.cbTarget.toggleEditModeCheckbox)
            self.keySC['tempAnno'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Space),
                            self.parent, self.cbTarget.addTempAnno)
            self.keySC['openFDV'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Delete),
                            self.parent, self.cbTarget.openFDV)
            self.keySC['keySettings'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_End),
                            self.parent, self.cbTarget.openKeySettings)
            self.keySC['debug'] = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Pause),
                            self.parent, self.cbTarget.debug)
        else:
            for k, km in self.keyMap.items():
                self.keySC[k].setKey(km)


    def swapToConstantSpeed(self, speed):

        if self.inConstantSpeed:
            return

        self.orignalStepSize = self.stepSize

        self.stepSize = { "stop": speed,
                        "step-f": speed,
                        "step-b": speed,
                        "allow-steps": False,
                        "fwd-1": speed,
                        "fwd-2": speed,
                        "fwd-3": speed,
                        "fwd-4": speed,
                        "fwd-5": speed,
                        "fwd-6": speed,
                        "bwd-1": speed,
                        "bwd-2": speed,
                        "bwd-3": speed,
                        "bwd-4": speed,
                        "bwd-5": speed,
                        "bwd-6": speed}

    def swapFromConstantSpeed(self):
        if not self.inConstantSpeed:
            self.stepSize = self.orignalStepSize


#     @cfg.logClassFunction
    def saveAll(self):
        cfg.log.info('saving all annotations')
        self.cbTarget.saveAll()

    def stop(self):
        # stop playback
        self.cbTarget.showTrajectTemp = True

        if self.stepSize["allow-steps"]:
            self.cbTarget.play = False
        else:
            self.cbTarget.play = True

        self.cbTarget.increment = self.stepSize["stop"]

        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def stepF(self):
        self.cbTarget.showTrajectTemp = True

        # step-wise forward
        if self.stepSize["allow-steps"]:
            self.cbTarget.play = False
            self.cbTarget.showNextFrame(self.stepSize["step-f"])
        else:
            self.cbTarget.play = True

        self.cbTarget.increment = self.stepSize["step-f"]
#                 self.cbTarget.showNextFrame(self.increment)
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def stepB(self):
        self.cbTarget.showTrajectTemp = True

        # step-wise backward
        if self.stepSize["allow-steps"]:
            self.cbTarget.play = False
            self.cbTarget.showNextFrame(self.stepSize["step-b"])
        else:
            self.cbTarget.play = True

        self.increment = self.stepSize["step-b"]
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)


    def fwd1(self):
        self.cbTarget.showTrajectTemp = True
        # real-time playback
        self.cbTarget.increment = self.stepSize["fwd-1"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def bwd1(self):
        self.cbTarget.showTrajectTemp = True
        # real-time playback
        self.cbTarget.increment = self.stepSize["bwd-1"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def fwd2(self):
        self.cbTarget.showTrajectTemp = True
        #
        self.cbTarget.increment = self.stepSize["fwd-2"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def fwd3(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["fwd-3"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def fwd4(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["fwd-4"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def fwd5(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["fwd-5"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def fwd6(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["fwd-6"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)
#                     self.tempTrajSwap = True
#                     self.showTrajectories(False)

    def bwd2(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["bwd-2"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def bwd3(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["bwd-3"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def bwd4(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["bwd-4"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def bwd5(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["bwd-5"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def bwd6(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.increment = self.stepSize["bwd-6"]
        self.cbTarget.play = True
        if self.cbTarget.tempTrajSwap:
            self.cbTarget.tempTrajSwap = False
            self.cbTarget.showTrajectories(True)

    def info(self):
        self.cbTarget.showTrajectTemp = True
        cfg.log.debug("position length: {0}".format(self.cbTarget.vh.getCurrentPositionLength()))
        cfg.log.debug("video length: {0}".format(self.cbTarget.vh.getCurrentVideoLength()))

    def escape(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.escapeAnnotationAlteration()

    def anno1(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.alterAnnotation(self.cbTarget.annotations[0]["annot"],
                            self.cbTarget.annotations[0]["behav"],
                            confidence=1,
                            oneClickAnnotation=self.oneClickAnnotation[0])
    def anno2(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.alterAnnotation(self.cbTarget.annotations[1]["annot"],
                            self.cbTarget.annotations[1]["behav"],
                            confidence=1,
                            oneClickAnnotation=self.oneClickAnnotation[1])

    def anno3(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.alterAnnotation(self.cbTarget.annotations[2]["annot"],
                            self.cbTarget.annotations[2]["behav"],
                            confidence=1,
                            oneClickAnnotation=self.oneClickAnnotation[2])

    def anno4(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.alterAnnotation(self.cbTarget.annotations[3]["annot"],
                            self.cbTarget.annotations[3]["behav"],
                            confidence=1,
                            oneClickAnnotation=self.oneClickAnnotation[3])

    def eraseAnno(self):
        self.cbTarget.showTrajectTemp = True
        self.cbTarget.testFunction()
        # self.cbTarget.addingAnnotations = not self.cbTarget.addingAnnotations
        # if not self.cbTarget.addingAnnotations:
        #     cfg.log.info("changed to erasing mode")
        #     self.cbTarget.ui.lbl_eraser.setVisible(True)
        #
        # else:
        #     cfg.log.info("changed to adding mode")
        #     self.cbTarget.ui.lbl_eraser.setVisible(False)
        #
        # cfg.logGUI.info(json.dumps({"addingAnnotations":
        #                         self.cbTarget.addingAnnotations}))

