# - - - - - - - - -
# import basic stuff
# - - - - - - - - -

import matplotlib.pyplot as plt
import sys, os, glob
sys.path.append('/home/peter/code/pyTools/')

import numpy as np
from pyTools.system.videoExplorer import *
from pyTools.videoProc.backgroundModel import *
from pyTools.imgProc.imgViewer import *
from pyTools.batch.vials import *
import pyTools.misc.basic as bsc
import time 
import datetime as dt
import subprocess
import joblib
import getpass
import smtplib
from email.mime.text import MIMEText

# - - - - - - - - - - - - -
# create essential objects
# - - - - - - - - - - - - -

vE = videoExplorer()
bgModel = backgroundModel(verbose=False, colorMode='rgb')
viewer = imgViewer()
roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
vial = Vials(roi, gaussWeight=2000, sigma=15)

# - - - - - - - - - - - - - - - - - - - - - -
# load classifier and define helper functions
# - - - - - - - - - - - - - - - - - - - - - -
import pyTools.libs.faceparts.vanillaHogUtils as vanHog
from skimage.color import rgb2gray
import skimage.transform

def computeHog(patch):
    a = list(skimage.transform.pyramid_gaussian(patch, 
                                                sigma=2,
                                                max_layer=1))
    return vanHog.hog(a[1], 9,3, 360, [0, 64, 0, 64])


flyClassifier = joblib.load('/run/media/peter/Elements/peter/data/bin/models/fly_svm/fly.svm')
noveltyClassfy = joblib.load('/run/media/peter/Elements/peter/data/bin/models/fly_svmNovelty/flyNovelty.svm')

flyClassify = lambda patch: Vials.checkIfPatchShowsFly(patch, flyClassifier, flyClass=1, debug=True)

acceptArgs = {'computeHog': computeHog, 
              'noveltyClassfy': noveltyClassfy,
              'flyClassify': flyClassify}

vial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6)


# - - - - - - - - - - - - - - - - - - - - - - - -
# split files into sets of consequent recordings
# - - - - - - - - - - - - - - - - - - - - - - - - 

import datetime as dt

rootPath = "/run/media/peter/Elements/peter/data/box1.0/"
fileList = []
for root,  dirs,  files in os.walk(rootPath):
    for fn in files:
        fileDT = vE.fileName2DateTime(fn)
        
        if fileDT == -1:
            ## file is no mp4 file of interest
            continue
            
        fileList.append([fileDT, root + r'/' + fn])
        
fileList = sorted(fileList)
recRngs = vE.findInteruptions(fileList)


# - - - - - - - - - - - - - - - - - - - - - - - -
# compute each section
# - - - - - - - - - - - - - - - - - - - - - - - - 
totI = len(fileList)
curI = 0
startTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
user = getpass.getuser()

for start, end in recRngs:
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()
    
    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createDayModel(sampleSize=10)
    bgModel.createNightModel(sampleSize=10)
    
    pathList = vE.nightList
    night = sorted(pathList)#[0:100]#[1:300]
    
    pathList = vE.dayList
    day = sorted(pathList)#[0:600]
    
    fileList = night + day
    
    chunkSize = 2
    
    for files in bsc.chunks(fileList, chunkSize):    
        try:
            vial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, clfyFunc=flyClassify, acceptPosFunc=Vials.acceptPosFunc, acceptPosFuncArgs=acceptArgs)
            1/0
            vial.extractPatches(files, bgModel, baseSaveDir='/run/media/peter/Elements/peter/data/tmp-20130701/')
    
            curI += chunkSize        
            currentTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
            
            progress = curI / totI
            passedTime = currentTime - startTime
            eta = passedTime * (100 - progress)
            finish = currentTime + eta
            
            status = \
            """{0} @ {1}:
            
            Processed: \t\t {2} / {3} files ({4}%).
            Processing time: \t {5}
            ETA: \t\t\t {6}
            estimated finish: \t {7}
            ==============================================
            """
            
            print status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish)

            # send a status email
            msg = MIMEText(status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish))
            
            me = '{0}@prism-cluster.co.uk'.format(user)
            you = 'p.rennert@cs.ucl.ac.uk'
            msg['Subject'] = 'Status Report of %s' % user
            msg['From'] = me
            msg['To'] = you
            
            s = smtplib.SMTP('localhost')
            s.sendmail(me, [you], msg.as_string())
            s.quit()
            
        except Exception as inst:    
            curI += chunkSize        
            currentTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
            
            progress = curI / totI
            passedTime = currentTime - startTime
            eta = passedTime * (100 - progress)
            finish = currentTime + eta
            
            status = \
            """
            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            {0} @ {1}:
            
            Processed: \t\t {2} / {3} files ({4}%).
            Processing time: \t {5}
            ETA: \t\t\t {6}
            estimated finish: \t {7}
            ==============================================
            ERROR MESSAGE:
            {8}
            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            """
            
            print status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish, inst)

            # send a status email
            msg = MIMEText(status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish, inst))
            
            me = '{0}@prism-cluster.co.uk'.format(user)
            you = 'p.rennert@cs.ucl.ac.uk'
            msg['Subject'] = '!!!! ERROR !!!! Status Report of %s' % user
            msg['From'] = me
            msg['To'] = you
            
            s = smtplib.SMTP('localhost')
            s.sendmail(me, [you], msg.as_string())
            s.quit()
            
            
