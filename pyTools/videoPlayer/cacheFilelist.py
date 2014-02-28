import pyTools.system.misc as systemMisc
import pyTools.misc.FrameDataVisualization as FDV
import json
import sys
import argparse
import textwrap

if __name__ == "__main__":
    parser = argparse.ArgumentParser(\
    formatter_class=argparse.RawDescriptionHelpFormatter,\
    description=textwrap.dedent(\
    """
    Parses configuration file of videoPlayer and creates a cache file that
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
    "bhvr-cache": "/home/peter/phd/code/pyTools/videoPlayer/bhvrList.json"
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
    
    if args.config_file == None:
        print textwrap.dedent(\
            """
            Expect configuration file (-c option). 
            Run 'python videoPlayer_pySide.py -h' for more information
            """)
        sys.exit()
        
    import ConfigParser    
    config = ConfigParser.ConfigParser()
    config.read(args.config_file)
    
    def configSectionMap(section):
        " https://wiki.python.org/moin/ConfigParserExamples"
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1
        
    videoPath = configSectionMap('Video')['videopath']
    bhvrCachePath = configSectionMap('Video')['bhvr-cache']    
    fdvtPath = configSectionMap('Video')['frame-data-visualization-path']
    
    print "start parsing"
    bhvrList = systemMisc.providePosList(videoPath, ending='.bhvr')
    
    with open(bhvrCachePath, "w") as f:
        json.dump(bhvrList, f)
        
    print "finished caching"
    
    print "cache behaviour visualization"    
    annotations = json.loads(configSectionMap('Annotation')['annotations'])
    try:
        selectedVial = [config.getint('Video','vial')]
    except:
        selectedVial = None
        
    fdtv = FDV.FrameDataVisualizationTreeBehaviour()
    fdtv.importAnnotations(bhvrList, annotations, selectedVial)
    fdtv.save(fdvtPath)
    
    