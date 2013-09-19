# user input variables
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-fc', '--flyClassifierPath', 
    help="path to SVM that discriminates flies from background patches",
    default='/run/media/peter/Elements/peter/data/bin/models/fly_svm/fly.svm')
parser.add_argument('-nc', '--noveltyClassfyPath',
    help="path to SVM that discriminates between trained data and untrained patches",
    default='/run/media/peter/Elements/peter/data/bin/models/fly_svmNovelty/flyNovelty.svm')
parser.add_argument('-r', '--rootPath', 
    help='path to root folder containing the vials, typically a "box0.0" type of folder',
    default="/run/media/peter/Elements/peter/data/box1.0/")
parser.add_argument('-s', '--baseSaveDirPath', 
    help='path to root folder to save the results',
    default='/run/media/peter/Elements/peter/data/tmp-20130701/')
parser.add_argument('-c', '--gmailCredentialPath', 
    help="""
    path to gmail credentials. This file should only contain
    "[abc@gmail.com, password]" """,
    default='../sandbox/mailCredentials')
parser.add_argument('-n', '--notificationEmail', 
    help="email the notifications are sent to",
    default='p.rennert@cs.ucl.ac.uk')
parser.add_argument('-e', '--maxErrors', 
    help="maximum an error can occur repeatively before processing is stopped entirely",
    type=int, default=2)
parser.add_argument('-cs', '--chunkSize', 
    help="number of video files to be processed before status is send",
    type=int, default=500)
args = parser.parse_args()



flyClassifierPath = args.flyClassifierPath
noveltyClassfyPath = args.noveltyClassfyPath
rootPath = args.rootPath
baseSaveDirPath = args.baseSaveDirPath
gmailCredentialPath = args.gmailCredentialPath
notificationEmail = args.notificationEmail
maxErrors = args.maxErrors
chunkSize = args.chunkSize

# - - - - - - - - -
# import basic stuff
# - - - - - - - - -

import matplotlib.pyplot as plt
import sys, os, glob
sys.path.append("../..")

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
import ast
import logging
from StringIO import *

from email.mime.text import MIMEText

#~ flyClassifierPath = '/run/media/peter/Elements/peter/data/bin/models/fly_svm/fly.svm'
#~ noveltyClassfyPath = '/run/media/peter/Elements/peter/data/bin/models/fly_svmNovelty/flyNovelty.svm'
#~ rootPath = "/run/media/peter/Elements/peter/data/box1.0/"
#~ baseSaveDirPath = '/run/media/peter/Elements/peter/data/tmp-20130701/'
#~ gmailCredentialPath = '../sandbox/mailCredentials'
#~ notificationEmail = 'p.rennert@cs.ucl.ac.uk'
#~ maxErrors = 2

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


flyClassifier = joblib.load(flyClassifierPath)
noveltyClassfy = joblib.load(noveltyClassfyPath)

flyClassify = lambda patch: Vials.checkIfPatchShowsFly(patch, flyClassifier, flyClass=1, debug=True)

acceptArgs = {'computeHog': computeHog, 
              'noveltyClassfy': noveltyClassfy,
              'flyClassify': flyClassify}

vial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6)


# load credentials for gmail
f = open(gmailCredentialPath)
userdata = ast.literal_eval(f.read())
f.close()

# - - - - - - - - - - - - - - - - - - - - - - - -
# split files into sets of consequent recordings
# - - - - - - - - - - - - - - - - - - - - - - - - 
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

# retrieve all processed images
fileListS = []
for root,  dirs,  files in os.walk(baseSaveDirPath):
    for fn in files:
        fileDT = vE.fileName2DateTime(fn, 'pos')
        
        if fileDT == -1:
            ## file is no mp4 file of interest
            continue
            
        fileListS.append([fileDT, root + r'/' + fn])
        
fileListS = sorted(fileListS)

# retrieve paths of all background images
fileListB = []
for root,  dirs,  files in os.walk(baseSaveDirPath):
    for fn in files:
        fileDT = vE.fileName2DateTime(fn, 'png')
        
        if fileDT == -1:
            ## file is no mp4 file of interest
            continue
            
        fileListB.append([fileDT, root + r'/' + fn])
        
fileListB = sorted(fileListB)

# sort processed videos and backgrounds to root ranges
rngBgImgs = [[] for i in range(len(recRngs))]
rngPos = [[] for i in range(len(recRngs))]
    
for bg in fileListB:
    for i in range(len(recRngs)):
        if (bg[0] >= recRngs[i][0]) and (bg[0] < recRngs[i][1]):
            rngBgImgs[i] += [bg]

for vid in fileListS:
    for i in range(len(recRngs)):
        if (vid[0] >= recRngs[i][0]) and (vid[0] < recRngs[i][1]):
            rngPos[i] += [vid]
            


def logMessage(message, subject):    
    message += '\n'

    print message

    # send a status email
    msg = MIMEText(message)

    me = userdata[0]
    you = notificationEmail
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = you

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo
    s.login(*userdata)
    s.sendmail(me, [you], msg.as_string())
    s.quit()
    
    if not os.path.exists(baseSaveDirPath):
        os.makedirs(baseSaveDirPath)
        
    with open(baseSaveDirPath + 'log.txt', 'a+') as myfile:
        myfile.write(message)

# - - - - - - - - - - - - - - - - - - - - - - - -
# compute each section
# - - - - - - - - - - - - - - - - - - - - - - - - 
totI = len(fileList)
curI = 0
errorCnt = [0, 0]

startTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
user = getpass.getuser()


for i in range(len(recRngs)):
    start, end = recRngs[i]
    
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()
    
    if len(vE.fileList) < 10:
        logMessage("skipped {0} to {1} because it had too few files".format(start, end),
                    "Skipping in {0}".format(user))
        continue
    
    
    pathList = vE.nightList
    night = sorted(pathList)
    
    pathList = vE.dayList
    day = sorted(pathList)
    
    # take all files except the last one, because that will be corrupted (not closed properly)
    fileList = sorted(night + day)[:-1]
    
    #calculate differences
    #diff = set(vE.getDatesOfList(fileList)).difference(vE.getDatesOfList(rngPos[i]))
    
    a = dict(fileList)
    b = dict(rngPos[i])
    
    # compute the files that were not processed so far
    diff = [[item, a[item]] for item in a.keys() if not b.has_key(item)]
    
    logMessage("{0} will process {1} of {2} ({3} to {4}) @ {5}".format(i, len(diff), len(fileList), start, end,
        dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))),
        "Process new batch in {0}".format(user))
    
    if len(diff) == 0:
        continue      
    
    fileList = diff
    
    # create background models
    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createDayModel(sampleSize=10)
    bgModel.createNightModel(sampleSize=10)
    
    #update models
    bgModel.updateModelWithBgImages(vE.getPathsOfList(rngBgImgs[i]))
    
    for files in bsc.chunks(fileList, chunkSize):   
        curI += len(files)   
        try:            

            logStream = StringIO()
            logHandler = logging.StreamHandler(logStream)
            log = logging.getLogger()
            log.setLevel(logging.DEBUG)
            for handler in log.handlers: 
                log.removeHandler(handler)
                
            log.addHandler(logHandler)
            
            
            vial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, clfyFunc=flyClassify, acceptPosFunc=Vials.acceptPosFunc, acceptPosFuncArgs=acceptArgs)
            vial.extractPatches(files, bgModel, baseSaveDir=baseSaveDirPath)
            
            currentTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
            
            progress = curI / float(totI)
            if progress == 0:
	      progress = 1
            passedTime = currentTime - startTime
            eta = passedTime * int(100 / progress)
            finish = currentTime + eta
            
            status = \
            """
            {0} @ {1}:
            
            Processed: \t\t {2} / {3} files ({4}%).
            Processing time: \t {5}
            ETA: \t\t {6}
            estimated finish: \t {7}
            ==============================================
            """
            
            logMessage(status.format(user, currentTime,
                                    curI, totI, progress, passedTime, eta, finish),
                       'Status Report of {0}'.format(user))
            
        except Exception as inst: 
            if curI - chunkSize ==  errorCnt[0]:
                # there were errors just before
                errorCnt[1] += 1
            else:
                errorCnt[1] = 1
            
            errorCnt[0] = curI
            
            currentTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
            
            progress = curI / float(totI)
            if progress == 0:
	      progress = 1
            passedTime = currentTime - startTime
            eta = passedTime * int(100.0 / progress)
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
            ==============================================
            Processing:
            {9}
            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            """
            # - - - - - - - - - - - - -
            # setup of logging process
            # - - - - - - - - - - - - -
            
            logging.exception(inst)
            
            log.removeHandler(logHandler)
            
            #self.logHandler.flush()
            logHandler.flush()
            logStream.flush()
            
            logMessage(status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish, logStream.getvalue(), files),
                       '!!!! ERROR !!!! Status Report of {0}'.format(user))
            
            # remove files from /tmp/ to free memory
            tmpFiles = glob.glob("/tmp/*.tif")
            for f in tmpFiles:
                os.remove(f)
            
            if errorCnt[1] >= maxErrors:
                logMessage("== stopping process of {0} ==".format(user),
                       '!!!! STOPPING !!!! Too many errors in {0}'.format(user))
                
                raise Exception("Process failed too often: Stop.")
            
