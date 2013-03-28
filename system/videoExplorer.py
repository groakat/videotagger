from os import path
import os
import re
import datetime as dt
import random
from ffvideo import VideoStream

class videoExplorer(object):
    """
    Class for access of recorded video files
    ========================================
    Allows to filter video files in a root folder to be retrieved by date

    """
    def __init__(self,  verbose=False):
        self.rootPath = "/run/media/peter/Elements/peter/data/"
        self.start = 0
        self.end = 0
        self.fileList = []
        self.nightList = []
        self.dayList = []
        self.verbose = verbose
        
    def setTimeRange(self,  start,  end):
        """
            set range of video explorer
            INPUT:
                start:  <datetime object>
                end:    <datetime object>
        """
        self.start = start
        self.end = end
        
    def setRootPath(self,  root):
        self.rootPath = root
        
    def parseFiles(self):
        """
            parses files in the main path and returns list of all files fitting
            the start - end criteria
            
            make sure that before calling this function:
            -   start and end datetimes were set 
            -   mainPath is set
        """
        if self.start == 0 or self.end == 0:
            raise ValueError("start or end value not set properly")
        
        self.fileList = []
        
        for root,  dirs,  files in os.walk(self.rootPath):
            for fn in files:
                fileDT = self.fileName2DateTime(fn)
                
                if fileDT == -1:
                    ## file is no mp4 file of interest
                    continue
                
                if self.start <= fileDT and self.end >= fileDT:
                    ## if timestamp is within the given range, add to list
                    self.fileList.append([fileDT, root + r'/' + fn])
                    
        self.filterDayVideos()
        self.filterNightVideos()
        
                    
    def filterDayVideos(self):
        """
            generates list (self.nightList) of videos that were recorded during 
            day (between 10am and 10pm)
        """
        self.dayList = []
        
        for vid in self.fileList:
            hour = vid[0].hour
            if hour >= 10 and hour < 23:
                self.dayList.append(vid)
    
    def filterNightVideos(self):
        """
            generates list (self.nightList) of videos that were recorded during 
            night (between 10pm and 10am)
        """
        self.nightList = []
        
        for vid in self.fileList:
            hour = vid[0].hour
            if hour < 10 or hour >= 23:
                self.nightList.append(vid)
                
    def getPathsOfList(self,  list):
        """
            returns a list of pure filenames without the corresponding datetime
        """
        out = []
        for item in list:
            out.append(item[1])
            
        return out
                
        
    def fileName2DateTime(self,  fn):
        """
            converts filename of video file to python datetime object
            
            INPUT:
                fn      <String>    filename
                
            OUTPUT:
                out     <datetime object> conversion of filename
        """
        
        folders = re.split("/",  fn)
        parts = re.split("[.]",  folders[-1])
        date = re.split("[-]", parts[0])
        time = re.split("[-]", parts[1])
        
        if parts[-1] != "mp4":
            return -1        
        
        if len(date) != 3:
            raise ValueError("mp4 file without proper date part discovered")
            return -1
            
        if len(time) != 3:
            raise ValueError("mp4 file without proper time part discovered")
            return -1
        
        out = dt.datetime(int(date[0]), int(date[1]), int(date[2]), 
                          int(time[0]), int(time[1]), int(time[2]))
        
        return out 
        
                
    def getRandomFrame(self, pathList,  info=False, frameMode='L'):
        """
            returns the first frame from a random video of the list
            
            INPUT:
                pathList    <List of Strings>   paths to video files
                info        bool                return frame and filename
                frameMode  String              'RGB': color representation
                                                'L':   gray-scale representation
                                                'F':   ???
                
            OUT:
                frame       <ndarray>           decoded video frame
        """
        file = pathList[random.randint(0,  len(pathList) - 1)]            
        frameNo = random.randint(0,  1600)
        
        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)
        
        vs = VideoStream(file, frame_mode=frameMode)  
        
        frame = vs.next().ndarray()
        
        if info:
            return [frame, file]
        else:
            return frame
                
    def getFrame(self, file, frameNo=0, info=False, frameMode='L'):
        """
            returns the given frame from a given video
            
            INPUT:
                file        String              path to video file
                frameNo     int                 frame number to be returned
                info        bool                return frame and filename
                frameMode  String              'RGB': color representation
                                                'L':   gray-scale representation
                                                'F':   ???
                                                
                
            OUT:
                frame       <ndarray>           decoded video frame
        """
        
        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)
        
        vs = VideoStream(file, frame_mode=frameMode)  
        
        frame = vs.get_frame_no(frameNo).ndarray()
        
        if info:
            return [frame, file]
        else:
            return frame
        
        

if __name__ == "__main__":
    vE = videoExplorer()
    
    start = dt.datetime(2013, 02, 19, 16)
    end = dt.datetime(2013, 02, 19,  17)
        
    vE.setTimeRange(start, end)
    
    vE.parseFiles()
    
#    print vE,.fileList
    
    vE.filterDayVideos();
#    print vE.dayList
    
    print vE.getPathsOfList(vE.dayList)
    
