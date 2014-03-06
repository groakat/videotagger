# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import pyTools.system.videoPlayerComClient as ComClient
import pyTools.system.labelExplorer as LE
import pyTools.videoProc.annotation as Annotation
import pyTools.misc.FrameDataVisualization as FDV
import numpy as np
import time
import copy
import cPickle as pickle

# <codecell>

queryFDVT = FDV.FrameDataVisualizationTreeBehaviour()
queryFDVT.load(fdvtBehaviourPath)

# <codecell>

class Test(object):
    def __init__(self, fdvtBehaviourPath='/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v2.npy',
                 vial=2,
                 address="tcp://127.0.0.1:4242", comServer=None):
        
        
        self.fdvtBehaviourPath = fdvtBehaviourPath       
        self.vial = vial
        
        self.queryFDVT = FDV.FrameDataVisualizationTreeBehaviour()
        self.queryFDVT.load(self.fdvtBehaviourPath)
        
        
        self.prepareAnnotationFilters()
        
    def prepareAnnotationFilters(self):
        self.annotations = []        
        self.annotations += [[\
                Annotation.AnnotationFilter([self.vial],["peter"],["falling"]),
                Annotation.AnnotationFilter([self.vial],["peter"],["dropping"])\
                            ]]
        
        self.annotations += [[\
               Annotation.AnnotationFilter([self.vial],["peter"],["struggling"])
                             ]]
        
        self.annoIdces = []
        for i in range(len(self.annotations)):
            self.annoIdces += [[]]
            for filt in self.annotations[i]:
                print filt
                self.annoIdces[i] += [self.queryFDVT.getAnnotationFilterCode(filt)]
        
        
        self.annoIdces.insert(0, [0])
        
        
    def drawSamples(self, amount=10):
        self.samples = []
        for i in range(amount):
            choice = np.random.randint(0, len(self.annoIdces))
            clses = self.annoIdces[choice]
            self.samples += [[choice, self.drawSampleFromFDVT(clses)]]
            
                   
        return self.samples
    
    def drawSampleFromFDVT(self, clses):
        return self.drawSampleFromStump(self.queryFDVT.tree, clses)
    
    
    def drawSampleFromStump(self, stump, clses):
        weights = []
        for k in sorted(stump.keys()):
            if k == 'meta':
                continue
                
            weight = 0
            for c in clses:
                weight += self.getStumpWeight(stump[k], c)
                                              
            weights += [weight]
        
        weights = np.asarray(weights)
        weights /= np.sum(weights)
        
        idx = np.random.choice(len(stump.keys()) - 1, size=None, p=weights)
        
        key = sorted(stump.keys())[idx]
        
        if 'data' in stump[key].keys():
            return [key] + self.drawSampleFromArray(stump[key]['data'], clses)
        else:
            return [key] + self.drawSampleFromStump(stump[key], clses)
        
    def drawSampleFromArray(self, ar, clses):
        targets = np.asarray(clses)
        idces = np.arange(ar.size)[(ar == targets[..., None]).any(axis=0)]
        
        choice = np.random.randint(0, idces.shape[0])
        
        return [idces[choice]]
                            
        
    def getStumpWeight(self, stump, c=0):
        stack = stump['meta']['stack']
        
        if c == 0:
            return stump['meta']['sampleN'] - np.sum(stack.ravel())
        else:
            if stack.shape[0] <= (c-1):
                return 0
            else:
                return stack[c - 1]
        
        

# <codecell>

fdvtBehaviourPath='/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp03.npy'

# <codecell>

t = Test(fdvtBehaviourPath=fdvtBehaviourPath, vial=3)

# <codecell>

s = t.drawSamples(200)

# <codecell>

t.queryFDVT.key2idx(*s[0][1])

# <codecell>

with open('/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/requests_v3_exp03.req', 'wb') as f:
    pickle.dump(s,f)

# <codecell>

t.queryFDVT.tree.keys()

# <codecell>

'data' in t.queryFDVT.tree['2013-02-19']['00']['00'].keys()

# <codecell>


# <codecell>

a

# <codecell>

getStumpWeight(c = 1,stump = t.queryFDVT.tree)

# <codecell>

t.queryFDVT.tree['meta']

# <codecell>

t.queryFDVT.tree['2013-02-19']['meta']

# <codecell>

a = np.arange(10)

# <codecell>

np.arange(len(a))[np.logical_or(a==1, a ==2)]

# <codecell>

targets = np.asarray([1,2])

# <codecell>

np.arange(a.size)[(a == targets[..., None]).any(axis=0)]

# <codecell>

%qtconsole

# <codecell>


