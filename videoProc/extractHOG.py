from multiprocessing import Process


import subprocess as sp
import os, shutil, time

from vision import features as feat
from pyTools.system.videoExplorer import videoExplorer
import numpy as np

def extractHOGfromVideo(path):    
    vE = videoExplorer()           
    vE.setVideoStream(path, info=False, frameMode='RGB')
    
    feats = []
    for frame in vE:
        feats += [feat.hog(frame)]
        
    f = np.asarray(feats)
    
    np.save(path.split('.avi')[0] + '.feat.{ending}.npy'.format(ending='hog-8'), f)
    
        
def providePosList(path):
    fileList  = []
    posList = []
    print("scaning files...")
    for root,  dirs,  files in os.walk(path):
        for f in files:
            if f.endswith('pos.npy'):
                path = root + '/' + f
                fileList.append(path)
                
    fileList = sorted(fileList)
    print("scaning files done")
    return fileList

if __name__ == '__main__':
    fileList = providePosList('/run/media/peter/Elements/peter/data/tmp-20130506')
    
    t = time.time()
#     for chunk in bsc.chunks(range(1, 1965, 60): #
    for i in range(len(fileList)):
        procs = []
        for v in range(4):
            path = fileList[i].split('.pos.npy')[0] + '.v{0}.avi'.format(v)
            procs += [Process(target=extractHOGfromVideo, args=(path,))]
            
        for p in procs:
            p.start()
        for p in procs:
            p.join()                
        for p in procs:
            p.terminate()
            
        if i % 15 == 0:
            print "finished", fileList[i], i / float(len(fileList)), "in", time.time() - t, "sec"
            
    print "finished all"
    
    
    
    
    
    
    
    
    
    
    
    
    