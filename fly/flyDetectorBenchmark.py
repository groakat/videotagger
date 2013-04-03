def benchmarkFlyDetectors(bgImg, img):    
    from time import time
        
    bgFunc = bgImg.backgroundSubtractionWeaver
    bgImg.configureStackSubtraction(bgFunc)
    
    sumT = 0
    for i in range(10):
        t = time()
        diffImgWeaver = bgImg.subtractStack(img[0])
        sumT += time() - t
    print 'backgroundSubtractionWeaver ', sumT / i
    
    
    bgFunc = bgImg.backgroundSubtractionWeaverF
    bgImg.configureStackSubtraction(bgFunc)
    
    sumT = 0
    for i in range(10):
        t = time()  
        diffImgWeaverF = bgImg.subtractStack(img[0])
        sumT += time() - t
    print 'backgroundSubtractionWeaverF ', sumT / i
    
    
    figure = plt.figure(figsize=(20,16))
    imshow(img[0])
    title(img[1])
    
    figure = plt.figure(figsize=(20,16))
    diffImgWeaverMin = vial.plotVialMin(diffImgWeaver)
    
    figure = plt.figure(figsize=(20,16))
    diffImgWeaverFMin = vial.plotVialMin(diffImgWeaverF)
    
    diffPos = [None] * len(diffImgWeaverFMin)
    for i in range(len(diffImgWeaverFMin)):
        diffPos[i] = [a - b for a, b in zip(diffImgWeaverMin[i], diffImgWeaverFMin[i])]
    
    
    print "difference between min positions: ", diffPos
    
def compareFlyDetectors(bgImg, img):
    
    bgFunc = bgImg.backgroundSubtractionWeaver
    bgImg.configureStackSubtraction(bgFunc)
    diffImgWeaver = bgImg.subtractStack(img[0])
    
    bgFunc = bgImg.backgroundSubtractionWeaverF
    bgImg.configureStackSubtractionCustom(bgFunc, fortranStyle=True)
    diffImgTest = bgImg.subtractStack(img[0]) 
    
    
    minGold = vial.getVialMin(diffImgWeaver)    
    minTest = vial.getVialMin(diffImgTest)
    
    diffPosT = [None] * len(minTest)
    for i in range(len(minTest)):
        diffPosT[i] = [a - b for a, b in zip(minGold[i], minTest[i])]
    
    ret = [img[1], diffPosT]
    print("difference between min positions: ", ret)
    
    return ret
    
def showFlyDetectors(bgImg, img):
    
    bgFunc = bgImg.backgroundSubtractionWeaver
    bgImg.configureStackSubtraction(bgFunc)
    diffImgWeaver = bgImg.subtractStack(img[0])
    
    bgFunc = bgImg.backgroundSubtractionWeaverF
    bgImg.configureStackSubtractionCustom(bgFunc, fortranStyle=True)
    diffImgTest = bgImg.subtractStack(img[0]) 
    
    
    figure = plt.figure(figsize=(20,16))
    imshow(img[0])
    title(img[1])
    
    figure = plt.figure(figsize=(20,16))
    minGold = vial.plotVialMin(diffImgWeaver)   
    figure = plt.figure(figsize=(20,16)) 
    minTest = vial.plotVialMin(diffImgTest)
    
    diffPosT = [None] * len(minTest)
    for i in range(len(minTest)):
        diffPosT[i] = [a - b for a, b in zip(minGold[i], minTest[i])]
    
    ret = [img[1], diffPosT]
    print("difference between min positions: ", ret)
    
    return ret

if __name__ == "__main__":
    import sys
    sys.path.append('/home/peter/code/pyTools/')

    import numpy as np
    from pyTools.system.videoExplorer import *
    from pyTools.videoProc.backgroundModel import *
    from pyTools.imgProc.imgViewer import *
    from pyTools.batch.vials import *
    from time import time


    vE = videoExplorer()
    bgModel = backgroundModel(verbose=True, colorMode='rgb')
    viewer = imgViewer()
    roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
    vial = Vials(roi)
    
    ## compute background images
    
    import datetime as dt
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 21)
    rootPath = "/run/media/peter/Elements/peter/data/"
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()

    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createDayModel(sampleSize=5)
    bgModel.createNightModel(sampleSize=10)

    testImg = img, fileName = vE.getRandomFrame(vE.getPathsOfList(vE.nightList),
                                                    info=True, frameMode='RGB')
                                                    
    ## single benchmark
    testImg = vE.getRandomFrame(vE.getPathsOfList(vE.nightList), info=True,
                                                                frameMode='RGB')
    benchmarkFlyDetectors(bgModel.modelNight, testImg)
    
    ### run full comparison
    #print("run comparison for all videos in path. Can take very long...")
    #res = []
    #for f in vE.nightList:
        #testImg = vE.getFrame(f[1], info=True, frameMode='RGB')
        #res.append(compareFlyDetectors(bgModel.modelNight, testImg))
        
    ### extract locations of largest disagreement
    #b = []
    #for i in res:
        #b.append(i[1])
        
    #c = np.asarray(b)
    #sortedErrors = np.argsort(np.max(np.max(np.abs(c), axis=1), axis=1))
    
    ### show largest disagreements
    #for i in range(1,10):
        #print res[sortedErrors[-i]]
        #testImg = vE.getFrame(res[sortedErrors[-i]][0], info=True, frameMode='RGB')
        #showFlyDetectors(bgModel.modelNight, testImg)           
    