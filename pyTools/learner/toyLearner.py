import pyTools.system.videoPlayerComClient as ComClient
import pyTools.system.labelExplorer as LE
from sklearn.ensemble import RandomForestClassifier as RFC
import numpy as np
import time
import copy


class ALToyLearner(ComClient.ALComBase):
    def __init__(self, featureBasePath='/media/peter/Elements/peter/data/tmp-20130506/',
                 featureMatrixPath='/home/peter/phd/code/notebooks/pyTools/sandbox/posFM.npy',
                 address="tcp://127.0.0.1:4242", comServer=None):
        super(ALToyLearner, self).__init__(address, comServer)
        
        self.featureBasePath = featureBasePath
        self.featureMatrixPath = featureMatrixPath
        self.cfr = RFC(n_estimators=2, max_depth=20, n_jobs=4)
        
        
        self.requestBaseLabelTree()
        self.labels = copy.copy(self.fdvt.flatten()['data'])
        self.deltaVectors = []
        self.loadFeatureMatrix()
        
        self.running = True
        self.selectNewFrame2Label()
        self.mainloop()
        
    
########## Communication stuff #######################
    def mainloop(self):
        while(self.running):
            self.queryNextCompletedJob()
        
        
    def noNewReply(self):
        time.sleep(0.05)
        
    def updatedFDVT(self, reply):
        print "ALComBase: updatedFDVT -- {0}".format(reply)
        time.sleep(0.05)
        
    def updateFrame(self, reply):
        print "ALComBase: updateFrame -- {0}".format(reply.reply)
        dv = reply.reply
        self.deltaVectors += [dv]
        self.labels[dv[0]] = dv[1]
        
        self.retrain()
        
        
    def updateFrameRange(self, reply):
        print "ALComBase: updateFrameRange -- {0}".format(reply)


########## Learning stuff ##################################
    def loadFeatureMatrix(self):
        if self.featureMatrixPath is not None:
            self.fm = np.load(self.featureMatrixPath)
            return
        
        # scan folder for feature files
        posList = LE.providePosList(self.featureBasePath, '.pos.npy')
        v = 2
        
        featDim = np.load(posList[0]).shape[2]
        self.fm = np.empty((self.labels.shape[0], featDim))
        
        cnt = 0
        for pos in sorted(posList):
            feat = np.load(pos)
            self.fm[cnt:cnt+feat.shape[0], :] = feat[:,v,:]
            cnt += feat.shape[0]
        

    def retrain(self):
        print "retraining.."
        testSet = self.labels.shape[0] / 5
        self.cfr.fit(self.fm[:-testSet], self.labels[:-testSet])
        
        print "predicting.."
        res = self.cfr.predict(self.fm[testSet:])
        
        cmat = LE.computeConfusionMatrix(res, self.labels[testSet:])
        score = LE.computeBalancedInlierRate(cmat)
        
        print "result:"
        print cmat
        print score
        print "================================================="
        
        self.selectNewFrame2Label()
        
        
    def selectNewFrame2Label(self):
        idx = np.random.randint(0, self.labels.shape[0])
        print "requesting frame {0}".format(idx)
        self.queryFrameLabel(idx)
    
    



if __name__ == "__main__":
    ALCom = ALToyLearner()
    