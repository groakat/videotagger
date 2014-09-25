import pyTools.system.videoPlayerComClient as ComClient
import pyTools.system.labelExplorer as LE
import pyTools.videoProc.annotation as Annotation
import pyTools.misc.FrameDataVisualization as FDV
import numpy as np
import time
import copy
import cPickle as pickle

class biasedClassLearnerRandom(ComClient.ALComBase):
    def __init__(self, requestPath='/home/peter/phd/code/pyTools/pyTools/pyTools/videoTagger/requests_v{v}_exp{exp}.req',
                 fdvtPath='/home/peter/phd/code/pyTools/pyTools/pyTools/videoTagger/bhvrTree_v{v}_exp{exp}.npy',
                 answerPath='/home/peter/phd/code/pyTools/pyTools/pyTools/videoTagger/requests_v{v}_exp{exp}_vol{vol}.awr',
                 exp="00",
                 vol="00",
                 vial=3,
                 address="tcp://127.0.0.1:4242", comServer=None):
        
        super(biasedClassLearnerRandom, self).__init__(address, comServer)
    
        self.exp = exp
        self.vol = vol
        self.vial = vial
        self.answerPath = answerPath.format(v=vial, exp=exp, vol=vol)
        
        self.queryFDVT = FDV.FrameDataVisualizationTreeBehaviour()
        self.queryFDVT.load(fdvtPath.format(v=vial, exp=exp))
        
        with open(requestPath.format(v=vial, exp=exp), 'rb') as f:
            self.requestList = pickle.load(f)
            
        self.idx = 0
        self.answerList = []
        self.prevFrames = []
        self.updated = True
        self.running = True
        self.timing = None
        
        
        self.mainloop()
        
    
########## Communication stuff #######################
    def mainloop(self):
        while(self.running):
            self.queryAllCompletedJobs()
            self.selectNewFrame2Label()
                
        
        
    def noNewReply(self):
        time.sleep(0.05)
        
    def updatedFDVT(self, reply):
        print "ALComBase: updatedFDVT -- {0}".format(reply)
        time.sleep(0.05)
        
    def updateFrame(self, reply):
        print "ALComBase: updateFrame -- {0}".format(reply.reply)
        self.answerList += [[self.requestList[self.idx - 1], 
                             reply.reply,
                             time.time() - self.timing]]
        
        for idx, lbl in reply.reply:
            self.prevFrames += [idx]
        
        with open(self.answerPath, 'wb') as f:
            pickle.dump(self.answerList,f)
            
        self.updated = True
        
        
    def updateFrameRange(self, reply):
        print "ALComBase: updateFrameRange -- {0}".format(reply)
        self.updateFrame(reply)


########## Learning stuff ##################################
        
    def selectNewFrame2Label(self):
        if not self.updated:
            return
        
        if self.idx > len(self.requestList):
            print "finished"
            self.running = False
            return
        
        qery = self.requestList[self.idx]
        fIdx = int(self.queryFDVT.key2idx(*qery[1]))
        self.idx += 1
        
        if fIdx in self.prevFrames:
            return self.selectNewFrame2Label()
        
        for i in range(100):
            time.sleep(0.20)
            
        print "requesting frame {0} ({1})".format(qery, fIdx)
        
        self.updated = False
        self.timing = time.time()
        self.queryFrameLabel(fIdx)
    
    



if __name__ == "__main__":
    ALCom = biasedClassLearnerRandom(exp="03", vol="03", vial=3)
    