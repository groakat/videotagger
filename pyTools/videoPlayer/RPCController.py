import pyTools.system.videoPlayerComClient as comClient
import pyTools.videoPlayer.dataLoader as DL

from PySide import QtCore

# 
#     import gevent
#     from gevent import monkey
#     monkey.patch_all()

class RPCController(comClient.GUIComBase):
    
    def __init__(self, cbFuncs, address="tcp://127.0.0.1:4242", cServer=None, 
                 debug=False):
        """
        Args:
            cbFuncts (dict)
                                dictionary to callback function to be called
                                keys:
                                    'noNewJob', 'labelFrame', 'updateFDVT', 
                                    'labelFrameRange'
        """
        super(RPCController, self).__init__(address, cServer, debug)
        
        if set(cbFuncs.keys()) != set(['noNewJob', 'labelFrame', 'updateFDVT', 
                                    'labelFrameRange']):
            raise ValueError("Not all callback functions defined")
        
        self.cbFuncs = cbFuncs
        
                        
    def noNewJob(self):
        self.cbFuncs['noNewJob']()
        
    def labelFrame(self, query):
        self.cbFuncs['labelFrame'](query)
        
    def updateFDVT(self, query):
        self.cbFuncs['updateFDVT'](query)
        
    def labelFrameRange(self, query):
        self.cbFuncs['labelFrameRange'](query)
        
        
class RPCInterfaceHandler(QtCore.QObject):
    labelFrameSig = QtCore.Signal(int)
    labelFrameRangeSig = QtCore.Signal(list)
    updateFDVTSig = QtCore.Signal(list)
    wait4NextJobSig = QtCore.Signal()
    sendLabelFDVTSig = QtCore.Signal(list)
    
    
    def __init__(self, address="tcp://127.0.0.1:4242"):
        """
        Args:
            address for controller
        """
        super(RPCInterfaceHandler, self).__init__(None)
        
        self.controller = None
        self.address = address
        
        
#         self.thread = DL.MyThread("RPCInterfaceHandlerThread")
#                              
#         self.moveToThread(self.thread)         
#         self.thread.start()
        
        self.wait4NextJobSig.connect(self.wait4NextJob)
        self.initWaiting()
        
        
        
    def initWaiting(self):
        import pyTools.system.videoPlayerComServer as ComServer
        self.cServer = ComServer.ComServerFDVT()
        
        if self.controller is None:
            cbFuncs = {'noNewJob': self.noNewJob, 
                       'labelFrame': self.labelFrame, 
                       'updateFDVT': self.updateFDVT,
                       'labelFrameRange': self.labelFrameRange}
            self.controller = RPCController(cbFuncs=cbFuncs,
                                        address=self.address,
                                        cServer=self.cServer)
            
        self.currentQuery = None
        self.waitingForReply = False
#         self.wait4NextJobSig.emit()
        
        
    def getNextJob(self):
        self.controller.requestNewJob()
        
        
    @QtCore.Slot()
    def wait4NextJob(self):
        while not self.waitingForReply:
            self.controller.requestNewJob()
            self.thread.mssleep(1)
    
                        
    def noNewJob(self):
        return
        
        
    def labelFrame(self, query):
        self.waitingForReply = True
        self.currentQuery = query
        self.labelFrameSig.emit(query.query)
        
        
    def updateFDVT(self, query):
        self.waitingForReply = True
        self.currentQuery = query
        self.updateFDVTSig.emit([query.query])
        self.initWaiting()
        
        
    def labelFrameRange(self, query):
        self.waitingForReply = True
        self.currentQuery = query
        self.labelFrameRangeSig.emit(query.query)
        
    
    @QtCore.Slot(list)
    def sendReply(self, lst):
        """
        Args:
            lst (list)
                    [dVector]
                    
                    With dVector (list):
                            nested list [[fn1, lbl1], [fn2, lbl2], .., 
                                                                   [fnN, lblN]]
                                                                   
                            fnX -- frame index in FDVT
                            lblX -- label assigned to that frame
        """ 
        dVector = lst[0]
        self.controller.sendCompletedJob(self.currentQuery, dVector)
        self.initWaiting()
        
    
    @QtCore.Slot(list)
    def sendLabelFDVT(self, lst):
        fdvt = lst[0]
        self.controller.fdvt = fdvt
        self.controller.sendLabelTree()
        
        
        
        
        
        
        
        
        
        