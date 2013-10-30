import datetime
import numpy as np
import os
import json
import copy

def getTime(t, ref=None):
    """
    Args:
        t (string):
                    asctime string from logger module
    Returns:
        datetime object
    """
    a = datetime.datetime.strptime(t.split(',')[0], "%Y-%m-%d %H:%M:%S")
    b = datetime.timedelta(milliseconds=int(t.split(',')[1]))
    
    
    if ref is not None:
        return (a + b) - ref
    else:
        return a + b

def convertFrame2Date(key, idx=0, ref=None):
    """
    Args:
        arg ({"idx":int, "key": string})
        
        ref (datetime):
                        reference time
    
    Returns:
        datedelta object
    """
    # calculate how many ms the idx represents in the current video file #
    if idx > 0:
        totalF = np.load(key).shape[0]
        musPerIdx = 60.0 / totalF * 1000
        idxInMs = datetime.timedelta(milliseconds=(idx * musPerIdx))
    else:
        idxInMs = datetime.timedelta(milliseconds=(0))
    
    # retrieve video file timestamp #
    t = key.split('/')[-1].split(".")[0:2]
    t = t[0] + "." + t[1]
    d = datetime.datetime.strptime(t, "%Y-%m-%d.%H-%M-%S")
    
    if ref is not None:
        d = (d + idxInMs) - ref
    else:
        d = (d + idxInMs)
        
    return d
    
    


def parseLogFiles(dataFolder, lineThreshold=2000):
    procFiles = []
    for fn in (f for f in os.listdir(dataFolder) if f.endswith('.log')) :
        with open(dataFolder + "/" + fn) as f:
            for i, l in enumerate(f,1):
                pass
            if i > lineThreshold:
                procFiles += [dataFolder + "/" + fn]
    
    
    logs = []
    print "loading files"
    for fn in sorted(procFiles):
        print "loading", fn
        with open(fn) as f:
            log = []
            for line in f:
                try:
                    log += [json.loads(line)]
                except:
                    print line
                
            logs += [log]
    
    print "start to compute plot values\n"
    
    
    # figure(figsize=(30,20))
    plotDatas = []
    for log in logs:
        if len(log) == 0:
            continue
            
        clearLog = []
        annoActive = []
        isAnnoActive = False
        behaviour = None
        for line in log:
            if line["func"] == "getCurrentFrame":
                clearLog += [line]
                annoActive += [[isAnnoActive, behaviour]]
                
            if line["func"] == "addAnno":
                isAnnoActive = not isAnnoActive
                if isAnnoActive:
                    behaviour = line["args"]["behaviour"]
                else:
                    behaviour = None
                
        
        timings = []
        accFrames = []
        annoSpans = []
        isAnnoActive = False
        
        refDate = getTime(clearLog[0]["time"])
        for i in range(len(clearLog)):
            line = clearLog[i]
            annoA = annoActive[i]
            timings += [getTime(line["time"], refDate)]
            accFrames += [convertFrame2Date(line["args"]["key"],
                                            line["args"]["idx"])]
            
            aA, behaviour = annoActive[i]
            if isAnnoActive is not aA:
                if aA:
                    annoSpans += [{"start": getTime(line["time"], refDate),
                                   "behaviour": behaviour}]
                else:
                    annoSpans[-1]["end"] = getTime(line["time"], refDate)
                                
                isAnnoActive = aA
                
        if isAnnoActive:
            annoSpans[-1]["end"] = getTime(clearLog[-1]["time"], refDate)
            
                    
            
        plotDatas += [[timings, accFrames, annoSpans]]
    
    return plotDatas

def correctSpanTiming(x, os=0):
    ret = {}
    try:
        ret = {"start":datetime.datetime(2001,1,1) + x["start"] + os,
                "end": datetime.datetime(2001,1,1) + x["end"] + os}
    except:
        print x
        ret = {"start":datetime.datetime(2001,1,1) + x["start"] + os,
                "end": datetime.datetime(2001,1,1) + x["start"] + os}
    
    ret["behaviour"] =  x["behaviour"]
    
    return ret

def constructContinuousLabelData(plotDatas):
    contDataX = []
    contDataY = []
    d = plotDatas[0]
    contDataX = [datetime.datetime(2001,1,1) + x for x in d[0]]
    os = d[0][-1]
    contDataY = copy.copy(d[1])
    contSpans = [correctSpanTiming(x,os) for x in d[2]]
    
    for d in plotDatas[1:]:
#         print os
        # define offset #
        contDataX += [datetime.datetime(2001,1,1) + x + os for x in d[0]]
        contDataY += d[1]
        contSpans += [correctSpanTiming(x,os) for x in d[2]]
        os += d[0][-1]
    
    return contDataX, contDataY

if __name__ == "__main__":
    pass
    