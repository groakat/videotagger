import pyTools.system.misc as systemMisc
import pyTools.misc.FrameDataVisualization2 as FDV

import json
import sys
import argparse
import textwrap
import os
import pyTools.misc.config as cfg


def getPathDirname(path):
    if os.path.isdir(path):
        dir = os.path.dirname(path + '/')
    else:
        dir = os.path.dirname(path)

    return dir

def generateVideoListPath(videoPath, videoListPathRel):
    if not videoListPathRel:
        videoListPathRel = 'videoCache.json'
        videoListPath = os.path.join(getPathDirname(videoPath),
                                     videoListPathRel)
        i = 1
        while os.path.exists(videoListPath):
            videoListPathRel = 'videoCache_{0}.json'.format(i)
            videoListPath = os.path.join(getPathDirname(videoPath),
                                         videoListPathRel)
            i += 1

    else:
        videoListPath = os.path.join(getPathDirname(videoPath),
                                     videoListPathRel)

    return videoListPath, videoListPathRel

def generateFDVTPath(videoPath, fdvtPathRel):
    if not fdvtPathRel:
        fdvtPathRel = 'framedataVis.npy'
        fdvtPath = os.path.join(getPathDirname(videoPath),
                                fdvtPathRel)
        i = 1
        while os.path.exists(fdvtPathRel):
            fdvtPathRel = 'framedataVis{0}.npy'.format(i)
            fdvtPath = os.path.join(getPathDirname(videoPath),
                                    fdvtPathRel)
            i += 1
    else:
        fdvtPath = os.path.join(getPathDirname(videoPath),
                                fdvtPathRel)

    return fdvtPathRel, fdvtPath

def convertVideoToBehaviourFiles(videoList, patchesFolder, behaviourFolder,
                                 videoExtension):
    bhvrList = []
    for video in videoList:
        folder = os.path.dirname(video)
        if len(patchesFolder) > 0:
            folder = folder[:-len(patchesFolder)]

        folder = os.path.join(folder, behaviourFolder)

        basename = os.path.basename(video)
        basename = basename[:-len(videoExtension)] + 'bhvr'

        bhvrList += [os.path.join(folder, basename)]

    return bhvrList


def cacheFilelist(videoPath, croppedVideo, selectedVial, videoExtension,
                  videoListPath, fdvtPathRel, annotations, runningIndeces,
                  patchesFolder, behaviourFolder):

    if videoPath.endswith(('avi', "mpeg", "mp4")):
        videoPath = os.path.dirname(videoPath)

    if croppedVideo:
        if type(selectedVial) == list:
            sv = selectedVial[0]
        else:
            sv = selectedVial

        extension = ".v{0}.{1}".format(sv, videoExtension)
    else:
        extension = ".{0}".format(videoExtension)

    videoList = systemMisc.providePosList(videoPath, ending=extension)

    if len(videoList) == 3:
        core = '.'.join(sorted(videoList)[0].split('.')[:-1])
        if core + '_full' + extension in videoList \
        and core + '_small' + extension in videoList \
        and core + extension in videoList:
            videoList = [core + '_small' + extension]

    videoListPath, videoListPathRel = generateVideoListPath(videoPath,
                                                           videoListPath)

    fdvtPathRel, fdvtPath = generateFDVTPath(videoPath, fdvtPathRel)

    rootPath = getPathDirname(videoPath)
    videoListRel = [x[len(rootPath)+1:] for x in videoList]
    with open(videoListPath, "w") as f:
        json.dump(videoListRel, f)

    potBhvrList = convertVideoToBehaviourFiles(videoList,
                                            patchesFolder,
                                            behaviourFolder,
                                            videoExtension)
    bhvrList = []
    for i, bhvrPath in enumerate(potBhvrList):
        if os.path.exists(bhvrPath):
            bhvrList += [bhvrPath]

    singleFileMode = None
    if len(videoList) > 1:
        singleFileMode = False
    else:
        singleFileMode = True

    fdtv = FDV.FrameDataVisualizationTreeBehaviour()
    fdtv.importAnnotations(bhvrList, videoList, annotations, selectedVial,
                           runningIndeces=runningIndeces,
                           singleFileMode=singleFileMode)

    print fdvtPath, fdvtPathRel

    fdtv.save(fdvtPath)

    return videoListPathRel, fdvtPathRel


def cacheFilelistFromConfig(config_file):
    try:
        VideoTagger.testFunction()
    except NameError:
        from pyTools.videoTagger.videoTagger import VideoTagger

    videoPath, annotations, annotator, backgroundPath, selectedVial, vialROI, \
    videoExtension, filterObjArgs, startVideo, rewindOnClick, croppedVideo, \
    patchesFolder, positionFolder, behaviourFolder, runningIndeces, fdvtPathRel,\
    videoListPathRel, bufferWidth, bufferLength, startFrame = \
                                    VideoTagger.parseConfig(config_file)

    cacheFilelist(videoPath, croppedVideo, selectedVial, videoExtension,
                  videoListPathRel, fdvtPathRel, annotations, runningIndeces,
                  patchesFolder, behaviourFolder)

if __name__ == "__main__":
    from pyTools.videoTagger.videoTagger import VideoTagger
    parser = argparse.ArgumentParser(\
    formatter_class=argparse.RawDescriptionHelpFormatter,\
    description=textwrap.dedent(\
    """
    Parses configuration file of videoTagger and creates a cache file that
    speeds up the start up significantly.
    
    This program has to be configured with a configuration file that is specified
    in the command-line argument. An example file should have been distributed
    with this program. It should be a json file like this (remember that 
    numbers, especially vials, start with 0). 
    
    The minimal values that have to be specified in the file are videoPath and
    bhvr-cache. The program will parse the videoPath folder for files and saves
    the cache in the file specified in bhvr-cache.
    
    An example would be:
    
    {
    "videoPath": "/run/media/peter/Elements/peter/data/tmp-20130506",
    "bhvr-cache": "/home/peter/phd/code/pyTools/videoTagger/bhvrList.json"
    }
    
    If you do not have the example file, you can simply copy and paste the 
    lines above (including the first and last { } ) in a text file and specify
    it as config-file path in the arguments.    
    """),
    epilog=textwrap.dedent(\
    """
    ============================================================================
    Written and tested by Peter Rennert in 2013 as part of his PhD project at
    University College London.
    
    You can contact the author via p.rennert@cs.ucl.ac.uk
    
    I did my best to avoid errors and bugs, but I cannot privide any reliability
    with respect to software or hardware or data (including fidelity and potential
    data-loss), nor any issues it may cause with your experimental setup.
    
    <Licence missing>
    """))
    
    parser.add_argument('-c', '--config-file', 
                help="path to file containing configuration")
    
       
    args = parser.parse_args()
    cacheFilelistFromConfig(args.config_file)

    
    