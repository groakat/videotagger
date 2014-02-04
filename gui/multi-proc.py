from multiprocessing import Process


import numpy as np
import subprocess as sp
import os, shutil, time

import pyTools.misc.basic as bsc
    
def computeHOG3D(fileList, i, v, xyWidth=2, tWidth=1):    
#     fileList, i, v = x
        
    rid = os.getpid()
    folder = os.path.join('/tmp/HOG3D', str(rid))
    
    if not os.path.exists(folder):
        os.makedirs(folder)        
            
    generateFFMPEGFilelist(fileList, i, folder, v, xyWidth, tWidth)
            
    concatenateVideos(folder)
            
    extractHOG3D(folder)
    
    ending = 'hog3d-xy{xy}-t{t}'.format(xy=xyWidth, t=tWidth)            
    storeResult(fileList, i, folder, v, ending)
    
    shutil.rmtree(folder)
#     return True
    
def generateFFMPEGFilelist(files, idx, folder, v, xyWidth=2, tWidth=1):
    with open(os.path.join(folder, 'concatList.txt'), 'w') as f:
        s = ''
        for i in range(-1, 2):
            fn = files[idx + i].split('.pos.npy')[0] + '.v{0}.avi'.format(v)
            s += "file {0}\n".format(os.path.join(folder, fn))
            
        f.write(s)
        
    generatePositionFile(files, idx, folder, v, xyWidth, tWidth)
    
    return True
    
def generatePositionFile(files, idx, folder, v, xyWidth=2, tWidth=1):
    start = np.load(files[idx - 1]).shape[0]
    length = np.load(files[idx]).shape[0]
    s = ''
    for i in range(length):
        s += "{0} {1} {2} {3} {4}\n".format(32, 32, start + i, xyWidth, tWidth)
        
    with open(os.path.join(folder, 'pos.txt'), 'w') as f:
        f.write(s)
        
    return True
        
def concatenateVideos(folder):
    p = sp.Popen('ffmpeg -f concat -i {0} -c copy {1}'.format(os.path.join(folder, 'concatList.txt'),
                                                         os.path.join(folder, 'concat.avi')),
             shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
    output = p.communicate()[0]
    
    return True
    
def extractHOG3D(folder):
    cmd = '/home/peter/code/pyTools/libs/3dhog/extractFeatures_x86_64_v1.3.0 -p {0} {1} > {2}'.format(\
                                os.path.join(folder, 'pos.txt'),
                                os.path.join(folder, 'concat.avi'),
                                os.path.join(folder, 'features.txt'))
    p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
    output = p.communicate()[0]
    
    return True
    
def storeResult(files, idx, folder, v, ending='hog3d'):
    a = np.genfromtxt(os.path.join(folder, 'features.txt'))
    
    dest = files[idx].split('.pos.npy')[0] + '.v{0}.feat.{ending}.npy'.format(v,
                                                                ending=ending)
    with open(dest, 'w') as f:
        np.save(f, a)
        
    return True
            
            
def f(x):
    print x[1], x[2]
    
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
            procs += [Process(target=computeHOG3D, args=(fileList, i, v,
                                                         1,0.25))]
            
        for p in procs:
            p.start()
        for p in procs:
            p.join()                
        for p in procs:
            p.terminate()
            
        if i % 15 == 0:
            print "finished", fileList[i], i / float(len(fileList)), "in", time.time() - t, "sec"
            
    print "finished all"
    
    
    
    
    
    
    
    
    
    
    
    
    