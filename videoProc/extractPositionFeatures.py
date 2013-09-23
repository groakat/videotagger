from multiprocessing import Process


import subprocess as sp
import os, shutil, time

import numpy as np
import pyTools.misc.basic as bsc

def extractPosFeatfromVideo(pathList, idx):    
    posList = []
    if idx != 0:
        posList += [np.load(pathList[idx - 1])[-1].reshape((1,4,2))]
    else:
        posList += [np.zeros((1,4,2))]
        
    posList += [np.load(pathList[idx])]
    
    if idx != len(pathList) -1:
        posList += [np.load(pathList[idx + 1])[-1].reshape((1,4,2))]
    else:
        posList += [np.zeros((1,4,2))]
        
    pos = np.concatenate(tuple(posList))
    
    for v in range(4):    
        xConv = np.convolve([1,-1], pos[:,v,0], mode='same')
        yConv = np.convolve([1,-1], pos[:,v,1], mode='same')
        feat = np.vstack(( pos[1:-1,v,0],
                           pos[1:-1,v,1],
                           xConv[1:-1],
                           yConv[1:-1],
                           xConv[2:],
                           yConv[2:],
                           )).transpose()
                   
        np.save(pathList[idx].split('.pos.npy')[0] + \
                '.v{vial}.feat.{ending}.npy'.format(ending='pos', vial=v),
                feat)
    
        
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
#     noOfProgress = 100
    curProgress = 0
    
    for chunk in bsc.chunks(range(len(fileList)), 6):
        procs = []
        for c in range(6):
            procs += [Process(target=extractPosFeatfromVideo, 
                                args=(fileList,chunk[c]))]
            
        for p in procs:
            p.start()
        for p in procs:
            p.join()                
        for p in procs:
            p.terminate()
            
        if np.floor(chunk[-1] / len(fileList) * 100) > curProgress:
            print "finished", chunk[-1] / len(fileList), "in", time.time() - t, "sec"
            curProgress = np.floor(chunk[-1] / len(fileList))
            
    print "finished all"
    
    
    
    
    
    
    
    
    
    
    
    
    