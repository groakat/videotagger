import pyTools.system.misc as systemMisc
import pyTools.misc.FrameDataVisualization2 as FDV
from pyTools.videoTagger.videoTagger import VideoTagger

import json
import sys
import argparse
import textwrap
import os

def cacheFilelist(config_file):
    videoPath, annotations, backgroundPath, selectedVial, vialROI, \
    videoExtension, filterObjArgs, startVideo, rewindOnClick, croppedVideo, \
    runningIndeces, fdvtPath, bhvrListPath, bufferWidth, \
    bufferLength = VideoTagger.parseConfig(config_file)

    print "start searching bhvr files"
    if videoPath.endswith(('avi', "mpeg", "mp4")):
        videoPath = os.path.dirname(videoPath)

    bhvrList = systemMisc.providePosList(videoPath, ending='.bhvr')
    print bhvrList

    with open(bhvrListPath, "w") as f:
        json.dump(bhvrList, f)


    print "start parsting bhvr files"
    fdtv = FDV.FrameDataVisualizationTreeBehaviour()
    fdtv.importAnnotations(bhvrList, annotations, selectedVial, runningIndeces=runningIndeces)
    fdtv.save(fdvtPath)

if __name__ == "__main__":
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
    cacheFilelist(args.config_file)

    
    