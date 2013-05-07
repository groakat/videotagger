==============================
Fly localization documentation
==============================


General description of Concepts
===============================

To extract fly locations for a set of video, a good starting point is to do::

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
    from time import time
    import subprocess
    import joblib

    # - - - - - - - - - - - - -
    # compute background models
    # - - - - - - - - - - - - -

    vE = videoExplorer()
    bgModel = backgroundModel(verbose=True, colorMode='rgb')
    viewer = imgViewer()
    roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
    vial = Vials(roi, gaussWeight=2000, sigma=15)

    import datetime as dt
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 21)
    rootPath = "/run/media/peter/Elements/peter/data/box1.0/"
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()

    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createDayModel(sampleSize=10)
    bgModel.createNightModel(sampleSize=10)

    testImg = vE.getRandomFrame(vE.getPathsOfList(vE.nightList), info=True, frameMode='RGB')

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


    pathList = vE.nightList
    night = sorted(pathList)[1:3]#[1:300]

    pathList = vE.dayList
    day = sorted(pathList)[0:300]

    #loadBackground(bgModel.modelDay)
    #vial.extractPatches(day, bgModel)

    nightVial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, clfyFunc=flyClassify, acceptPosFunc=Vials.acceptPosFunc, acceptPosFuncArgs=acceptArgs)
    nightVial.extractPatches(night, bgModel, baseSaveDir='/run/media/peter/Elements/peter/data/tmp-20130506/')

    dayVial = Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, clfyFunc=flyClassify, acceptPosFunc=Vials.acceptPosFunc, acceptPosFuncArgs=acceptArgs)
    dayVial.extractPatches(day, bgModel, baseSaveDir='/run/media/peter/Elements/peter/data/tmp-20130506/')


Important members
=================	

As it can be seen from the example above, there are to important configuration
 steps to do, to extract fly locations in a batch.

First one has to create a :mod:`Vials` object and then call :func:`extractPatches`. 
Those are the most important functions for the user and are documented here. The
complete documentation can be found below.

.. autoclass:: pyTools.batch.vials.Vials
    :members: __init__, extractPatches
    :noindex:
