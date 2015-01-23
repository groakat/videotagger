from os import path
import os
import re
import datetime as dt
import random
from ffvideo import VideoStream, SEEK_ANY
import ffvideo

class videoExplorer(object):
    """
    Class for access of recorded video files

    Allows to filter video files in a root folder to be retrieved by date

    """
    def __init__(self,  verbose=False, rootPath="/run/media/peter/Elements/peter/data/"):
        """

        Args:
            verbose (bool):
                                switch verbosity on (prints some status messages)
            rootPath (string):
                                root directory to be scanned for video files
        """
        self.rootPath = rootPath
        self.start = 0
        self.end = 0
        self.fileList = []
        self.nightList = []
        self.dayList = []
        self.verbose = verbose
        self.vs = None

    def setTimeRange(self,  start,  end):
        """
        set range of video explorer (works similar to a slice())

        :note:`The range is inclusive for the lower and upper end of the range`

        Args:
            start (datetime object):
                                beginning of time range
            end(datetime object):
                                end of time range
        """
        self.start = start
        self.end = end

    def setRootPath(self,  root):
        """
        Set root path of object

        Test:
            asdad
        """
        self.rootPath = root

    def parseFiles(self):
        """
        parses files in the main path and returns list of all files fitting
        the start - end criteria

        make sure that before calling this function:

            - start and end datetimes were set
            - mainPath is set

        .. seealso::
            :func:`setTimeRange()`
            :func:`setRootPath()`
        """
        if self.start == 0 or self.end == 0:
            raise ValueError("start or end value not set properly")

        self.fileList = []

        for root,  dirs,  files in os.walk(self.rootPath):
            for fn in files:
                ################################################################ TODO: sort files by file name
                fileDT = self.fileName2DateTime(fn)

                if fileDT == -1:
                    ## file is no mp4 file of interest
                    continue
                ################################################################ TODO: add option to load files without filter

                if self.start <= fileDT and self.end >= fileDT:
                    ## if timestamp is within the given range, add to list
                    self.fileList.append([fileDT, root + r'/' + fn])

        self.filterDayVideos()
        self.filterNightVideos()


    def filterDayVideos(self):
        """
        generates list (self.nightList) of videos that were recorded during
        day (between 10am and 11pm)
        """
        self.dayList = []

        for vid in self.fileList:
            hour = vid[0].hour
            if hour >= 10 and hour < 23:
                self.dayList.append(vid)

    def filterNightVideos(self):
        """
        generates list (self.nightList) of videos that were recorded during
        night (between 11pm and 10am)
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

    def getDatesOfList(self,  list):
        """
        returns a list of pure datetime without the corresponding paths
        """
        out = [item[0] for item in list]

        return out


    def fileName2DateTime(self,  fn, ending="mp4"):
        """
        converts filename of video file to python datetime object

        Args:
            fn (string):
                                filename

        Returns:
            out (datetime object):
                                conversion of filename
        """

        basename = os.path.basename(fn)
        parts = re.split("[.]",  basename)
        date = re.split("[-]", parts[0])
        time = re.split("[-]", parts[1])

        if fn[-len(ending):] != ending:
            return -1

        if len(date) != 3:
            raise ValueError("mp4 file without proper date part discovered")
            return -1

        if len(time) < 3:
            raise ValueError("mp4 file without proper time part discovered")
            return -1

        out = dt.datetime(int(date[0]), int(date[1]), int(date[2]),
                          int(time[0]), int(time[1]), int(time[2]))

        return out


    def findInteruptions(self, fileList):
        """
        separates the filelist into ranges of consequent films, i.e. each
        range represents a batch of videos that share the same background model

        :note:`it is assumed that each consequtive file is 1 min long`

        Args:
            fileList (list of [datetime, path])
                                each element of this list can be generated by
                                :func:`fileName2DateTime`

        Returns:
            ranges of datetime that can be passed directly into
            :func:`setTimeRange`
        """
        # set file chunk size to 1 minute
        chunkSize = dt.time(0, 1)

        fileList = sorted(fileList)

        rngs = []
        start = None
        stop = None

        if len(fileList) < 2:
            raise ValueError("There are less then 2 files in the list. That usually means that a wrong folder was selected.")

        for i in range(len(fileList) - 1):
            if start is None:
                start = fileList[i][0]
                if (not (fileList[i + 1][0] - fileList[i][0]) <= dt.timedelta(minutes=1))\
                    or fileList[i + 1][0].second != 0:
                    stop = fileList[i][0]

            elif (not (fileList[i + 1][0] - fileList[i][0]) == dt.timedelta(minutes=1))\
                    or fileList[i + 1][0].second != 0:
                stop = fileList[i][0]

            if stop is not None:
                rngs += [[start, stop, i]]
                start = None
                stop = None

        stop = fileList[i+1][0]
        rngs += [[start, stop, i]]

        return rngs

    def getRandomFrame(self, pathList,  info=False, frameMode='L'):
        """
        returns the first frame from a random video of the list

        Args:
            pathList (List of Strings):
                                paths to video files
            info (bool):
                                return frame and filename
            frameMode (String):
                                Switch of color mode:

                                - 'RGB': color representation
                                - 'L':   gray-scale representation
                                - 'F':   ???

        Returns:
            frame (ndarray):
                                decoded video frame
        """
        file = pathList[random.randint(0,  len(pathList) - 1)]
        frameNo = random.randint(0,  1600 - 1)

        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)

        self.vs = VideoStream(file, frame_mode=frameMode, exact_seek=True)

        frame = self.vs.next().ndarray()

        if info:
            return [frame, file]
        else:
            return frame

    def getFrame(self, file, frameNo=0, info=False, frameMode='L'):
        """
        returns the given frame from a given video

        Args:
            file (String):
                                path to video file
            frameNo (int):
                                frame number to be returned
            info (bool):
                                return frame and filename
            frameMode (String):
                                Switch of color mode:

                                - 'RGB': color representation
                                - 'L':   gray-scale representation
                                - 'F':   ???


        Returns:
            frame (ndarray):
                                decoded video frame
        """

        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)

        self.vs = VideoStream(file, frame_mode=frameMode, exact_seek=True)
        
        frame = self.vs.get_frame_no(frameNo).ndarray()
        
        if info:
            return [frame, file]
        else:
            return frame
                
    def next(self):
        """
        returns next frame in opened video file
        Call getFrame() or getRandomFrame() first
        
        Args:
            info (bool):
                                return frame and filename
                                
        .. seealso::
            :func:`getFrame`
            :func:`getRandomFrame`
        """
        
        if self.vs is None:
            raise AttributeError("no video stream defined. (It might be that" +\
                                 " the last frame was captured before)")
        
        try:
            frame = self.vs.next().ndarray()
        except ffvideo.NoMoreData:
            self.vs = None
            frame = None
            raise StopIteration
            
        return frame
        
    
    def setVideoStream(self, file,  info=False, frameMode='L'):
        """
        returns the first frame from a random video of the list
        
        Args:
            pathList (List of Strings):
                                paths to video files
            info (bool):
                                return frame and filename
            frameMode (String):
                                Switch of color mode:
                                
                                - 'RGB': color representation
                                - 'L':   gray-scale representation
                                - 'F':   ???
            
        Returns:
            frame (ndarray):
                                decoded video frame
        """       
        frameNo = random.randint(0,  1600 - 1)
        
        if self.verbose:
            print "processing frame {0} of video {1}".format(frameNo,  file)
        
        self.vs = VideoStream(file, frame_mode=frameMode, exact_seek=True)
        
    def __iter__(self):
        # rewind ffvideo thingy
        self.vs.__iter__()
        
        return self
    
    @staticmethod
    def splitFolders(path):
        """
        splits path into its folders and returns them 
        in a list. 

        .. note::
            Last entry of the returned list will be the
            basename of the path if applicable

        Args:
            path (string):
                            path to split

        Returns:
            folders (list of strings):
                            list of folders in path
                            
        Source:
            http://stackoverflow.com/questions/3167154/how-to-split-a-dos-path-into-its-components-in-python
        """
        folders=[]
        while 1:
            path,folder=os.path.split(path)

            if folder!="":
                folders.append(folder)
            else:
                if path!="":
                    folders.append(path)

                break

        folders.reverse()

        return folders

    @staticmethod
    def retrieveVideoLength(filename, initialStepSize=10000):
        """
        Finds video length by accessing it bruteforce

        """
        idx = 0
        modi = initialStepSize
        vE = videoExplorer()

        while modi > 0:
            while True:
                try:
                    vE.getFrame(filename, frameNo=idx, frameMode='RGB')
                except StopIteration:
                    break

                idx += modi

            idx -= modi

            print modi, idx
            modi /= 2


        return idx + 1 # + 1 to make it the same behaviour as len()


    @staticmethod
    def findFileInList(lst, filename):
        """
        returns the position of the file within the list of paths
        """
        return [a for a,b in enumerate(lst) if b[1].endswith(filename)]
        
    @staticmethod
    def findClosestDate(dateList, date):
		min(DTlist,key=lambda date : abs(dt-date))
        

def providePosList(path, ending=None):
    if not ending:
        ending = '.pos.npy'
    
    fileList  = []
    for root,  dirs,  files in os.walk(path):
        for f in files:
            if f.endswith(ending):
                path = root + '/' + f
                fileList.append(path)
                
    fileList = sorted(fileList)
    return fileList
    
if __name__ == "__main__":
    vE = videoExplorer()
    
    start = dt.datetime(2013, 02, 19, 16)
    end = dt.datetime(2013, 02, 19,  17)
       
    vE.setTimeRange(start, end)
    
    
    vE.parseFiles()
    
#    print vE,.fileList
    
    vE.filterDayVideos();
#    print vE.dayList
    
    print vE.getPathsOfList(vE.dayList)[0]
    
    # iterate through all frames of a video file
    vE.setVideoStream(vE.getPathsOfList(vE.dayList)[0])
    for frame in vE:
        print frame
    
