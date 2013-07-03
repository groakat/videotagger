# user input variables
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-fc', '--flyClassifierPath', 
    help="path to SVM that discrimitates flies from background patches",
    default='/run/media/peter/Elements/peter/data/bin/models/fly_svm/fly.svm')
parser.add_argument('-nc', '--noveltyClassfyPath',
    help="path to SVM that discrimiates between trained data and untrained patches",
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
    help="maximum an error can occur repeatitly before processing is stopped entirely",
    type=int, default=2)
args = parser.parse_args()



flyClassifierPath = args.flyClassifierPath
noveltyClassfyPath = args.noveltyClassfyPath
rootPath = args.rootPath
baseSaveDirPath = args.baseSaveDirPath
gmailCredentialPath = args.gmailCredentialPath
notificationEmail = args.notificationEmail
maxErrors = args.maxErrors

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
import ast
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

import datetime as dt

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
errorCnt = [0, 0]

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
        curI += chunkSize   
        try:            
            vial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, clfyFunc=flyClassify, acceptPosFunc=Vials.acceptPosFunc, acceptPosFuncArgs=acceptArgs)
            vial.extractPatches(files, bgModel, baseSaveDir=baseSaveDirPath)
          
            currentTime = dt.datetime.fromtimestamp(time.mktime(time.localtime(time.time())))
            
            progress = curI / totI
            passedTime = currentTime - startTime
            eta = passedTime * (100 - progress)
            finish = currentTime + eta
            
            status = \
            """
            {0} @ {1}:
            
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
            
            me = userdata[0]
            you = notificationEmail
            msg['Subject'] = 'Status Report of %s' % user
            msg['From'] = me
            msg['To'] = you
            
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.ehlo
            s.login(*userdata)
            s.sendmail(me, [you], msg.as_string())
            s.quit()
            
        except Exception as inst: 
            if curI - chunkSize ==  errorCnt[0]:
                # there were errors just before
                errorCnt[1] += 1
            else:
                errorCnt = 1
            
            errorCnt[0] = curI
            
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
            Processing:
            {9}
            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            """
            
            print status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish, inst, files)

            # send a status email
            msg = MIMEText(status.format(user, currentTime,
                                         curI, totI, progress, passedTime, eta, finish, inst, files))
            
            me = userdata[0]
            you = notificationEmail
            msg['Subject'] = '!!!! ERROR !!!! Status Report of %s' % user
            msg['From'] = me
            msg['To'] = you
            
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.ehlo
            s.login(*userdata)
            s.sendmail(me, [you], msg.as_string())
            s.quit()
            
            if errorCnt[1] >= maxErrors:
                msg = MIMEText("== stopping process of {0}".format(user))
                
                me = userdata[0]
                you = notificationEmail
                msg['Subject'] = '!!!! STOPPING !!!! Too many errors in %s' % user
                msg['From'] = me
                msg['To'] = you
                
                s = smtplib.SMTP('smtp.gmail.com', 587)
                s.ehlo()
                s.starttls()
                s.ehlo
                s.login(*userdata)
                s.sendmail(me, [you], msg.as_string())
                s.quit()
                
                raise Exception("Process failed too often: Stop.")
            
