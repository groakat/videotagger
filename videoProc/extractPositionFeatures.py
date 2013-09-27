from multiprocessing import Process


import subprocess as sp
import os, shutil, time

import numpy as np
import pyTools.misc.basic as bsc

def extractPosFeatfromVideo(pathList, idx):    
    posList = []
    if idx != 0:
        try:
            posList += [np.load(pathList[idx - 1])[-1].reshape((1,4,2))]
        except:
            print idx - 1
    else:
        posList += [np.zeros((1,4,2))]
        
    posList += [np.load(pathList[idx])]
    
    if idx != len(pathList) -1:
        try:
            posList += [np.load(pathList[idx + 1])[-1].reshape((1,4,2))]
        except:
            print idx  + 1
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
                '.v{vial}.feat.{ending}.npy'.format(ending='position', vial=v),
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

def partition ( lst, n ):
    return [ lst[i::n] for i in range(n) ]

if __name__ == '__main__':
    fileList = providePosList('/run/media/peter/Elements/peter/data/tmp-20130506')
    
    t = time.time()
#     for chunk in bsc.chunks(range(1, 1965, 60): #
#     noOfProgress = 100
    for i in range(len(fileList)):
        extractPosFeatfromVideo(fileList, i)
            
    print "finished all"
    
    
    
    
    
    
    
    
    
    
    
    
    