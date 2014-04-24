"""
    interactive image viewer
    
    based on answer on
    http://stackoverflow.com/questions/5836560/color-values-in-imshow-for-matplotlib
"""
from matplotlib import pyplot as plt
from matplotlib.pyplot import *
import numpy as np
import matplotlib.image as mpimg
from copy import *
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, \
     AnnotationBbox
import matplotlib as mpl

class imgViewer(object):
    def show(self,  img):
        """
        Show an image using matplotlib. However this function extends the viewer
        with a functionality that returns the value of pixels on mouse click
        """
        self.img = plt.imshow(img, interpolation='nearest')
        self.fig = plt.gcf()
        self.ax = plt.gca()
        
        self.handler = EventHandler(self)        
        plt.show()     
        
        
    def showPatch(self, img, center, patchSize, patch_zoom=0.2, offsetX=0, 
                    offsetY=0.5, fig=None, no=0, patch=None):
        """
        Displays position of a patch and the patch itself in a zoomed version
        
        Args:
            img (ndarray):
                                image
            center ([int, int]):
                                center position of patch
            patchSize ([int, int]):
                                size of patch
            patch_zoom (float):
                                zoom factor of patch
            offsetX:
                                x offset of figure-axes (can be used to display
                                several axes within one figure)
            offsetY:
                                y offset of figure-axes (can be used to display
                                several axes within one figure)
            fig (matplotlib figure instance):
                                figure instance in which the axes will be drawn
                                if fig=None a new figure will be created
            no (int):
                                number (position) of plot. It can be used to
                                plot several plots within one figure. Each 
                                plot should have its unique number and will
                                be placed at this given position
            patch (ndarray):
                                Image to be shown as patch. If patch=None, patch
                                will be extracted from image (using center,
                                patchSize)
        """
        if fig == None:
            fig, tmp = subplots()
            
        ## create artificial border around the image to display 
        ## patchbox uncropped inline
        #border = fig.add_axes([0 + offsetX, 0 + offsetY, 1, 2.0])
        #border.axis('off')
        
        ## axis for image
        ax = fig.add_axes([offsetX,offsetY, 0.5, 1])
        
        im = ax.imshow(img)
        ax.axis('off')
        
        
        if patch == None:
            patch = self.extractPatch(img, center, patchSize)
        
        # conversion from numpy order to tuple order
        a = copy(center[0])
        center[0] = copy(center[1])
        center[1] = copy(a)
        
        ## create frame around patch
        xy = copy(center)
        xy[0] -= patchSize[0]/2
        xy[1] -= patchSize[1]/2
            
        rect = mpl.patches.Rectangle(xy,patchSize[0], patchSize[1])
        rect.set_fill(False)
        
        ax.add_patch(rect)
           
        ## display patch with zoom
        norm = mpl.colors.Normalize(vmin=np.min(img), vmax=np.max(img))
        imagebox = OffsetImage(patch, zoom=patch_zoom, norm=norm)

        ab = AnnotationBbox(imagebox, center,
                            xybox=(1.6, img.shape[0]-patchSize[0]-30),
                            xycoords='data',
                            boxcoords=("axes fraction", "data"),#"offset points",
                            pad=0.5,
                            arrowprops=dict(arrowstyle="->",
                                            connectionstyle="angle,angleA=0,angleB=90,rad=3")
                            )
        
        ax.add_artist(ab)   
        
        cax = fig.add_axes([0.4 + offsetX, 1, 0.02, 0.4])
        plt.colorbar(im, cax=cax)
        
    @staticmethod
    def extractPatch(img, center, patchSize):
        """
        Extracts savely a patch from an image. The patch is centered around 
        center and has height/ width as specified in patchSize
        
        Args:
            img (ndarray):
                                image
            center ([int, int]):
                                center position of patch
            patchSize ([int, int]):
                                size of patch
                                
        Returns:
            patch (ndarray):
                                extracted patch
        """
        
        rngX, rngY = imgViewer.getValidPatchRange(img, center, patchSize)
        
        return img[rngX, rngY]
    
    @staticmethod
    def getValidPatchRange(img, center, patchSize):      
        """
        Returns valid slices for patches to avoid exceeding of indeces of 
        image dimensions
        
        Args:
            img (ndarray):
                                image
            center ([int, int]):
                                center of patch
            patchSize ([int, int]):
                                size of patch
        
        Returns:
            xRng, yRng:
                                slices of x and y direction
        """  
        xy = np.round(copy(center)).astype(np.int)
        xy[0] -= patchSize[0]/2
        xy[1] -= patchSize[1]/2
        
        if xy[0] < 0:
            xy[0] = 0
        if xy[1] < 0:
            xy[1] = 0
            
        h = xy[0]+patchSize[0]
        if  h > img.shape[0]:
            h = img.shape[0]
            
        w = xy[1]+patchSize[1]
        if  w > img.shape[1]:
            w = img.shape[1]
            
        return slice(xy[0],h), slice(xy[1],w)
                
    
    @staticmethod
    def fig2np(fig):
        """
        Converts matplotlib figure in a numpy ndarray
        """
        # If we haven't already shown or saved the plot, then we need to
        # draw the figure first...
        fig.canvas.draw()

        # Now we can save it to a numpy array.
        data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        
        return data
    
    @staticmethod
    def createSuppressionMask(frame, center, patchSize):
        """
        creates a boolean mask with a "window" of the given patch size around 
        the center
        
        Args:   
            frame (ndarray):
                        input image, used for size reference only
            center (int, int):
                        center of the window
            patchSize ([int, int]):
                        size of the patch
                        
        Returns:
            ndarray (boolean): mask
                    
        """
        mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.bool)
        rngX, rngY = imgViewer.getValidPatchRange(mask, center, patchSize)
        # erase patch around fly
        mask[rngX, rngY] = 0
        
        return mask
        
    
 

class EventHandler:
    def __init__(self,  iV):
        self.iV = iV
        iV.fig.canvas.mpl_connect('button_press_event', self.onpress)

    def onpress(self, event):
        if event.inaxes != self.iV.ax:
            return
        xi, yi = (int(round(n)) for n in (event.xdata, event.ydata))
        value = self.iV.img.get_array()[yi, xi]
        
        if np.isscalar(value):
            ## if image is grayscale print also colour of displayed colour map
            color = self.iV.img.cmap(self.iV.img.norm(value))
            print "(x:{0}, y:{1}) value: {2} | colormap: {3}".format(xi,
                                                                     yi,
                                                                     value,
                                                                     color)
        else:
            ## otherwise just print rgb values
            print "(x:{0}, y:{1}) value: {2}".format(xi,yi,value)

def computeDistancesFromPosList(posList, fileList):
    """
    Compute minute-wise differences of trajectories in the poslist
    
    Args:
        posList (list of list of [int, int]):
                            list of frame positions, which are a 
                            lists of pairwise positions for each vial
        fileList (list of strings):
                            list of file names of the videos that the
                            positions refer to (usually retrieved from
                            the names of the position files)
                            The .mp4 is not necessary, it is just used
                            to get the timestamp of each minute
    
    Returns:
        dists (list([vialNo]np.array(minutes)):
                            list containing long continuous vector of differences
                            for each vial
    """
    ## smooth the positions
    # first make long arrays for each vial and direction 
    
    sequence =  [[] for i in range(8)]
    for minute in posList:
        for pos in minute:
            for v in range(len(pos)):
                sequence[v * 2].append(pos[v][0])
                sequence[v * 2 + 1].append(pos[v][1])
                
                
    # smooth out localization errors
    from scipy.signal import medfilt    
    filteredPos = []
    for a in sequence:
        filteredPos.append(medfilt(a, 31))
        
    # compute differences between frames
    diff  =  []
    for p in filteredPos:
        diff.append(np.convolve([1,-1], p))
    
    dists = [[] for i in range(4)]
    for i in range(4):
        dists[i] = np.sqrt(diff[i*2] ** 2 + diff[i*2 + 1] ** 2)
        
        
    return dists
    
def computeAccumulativeDistance(posList, dists):
    """
    Compute minute-wise sum of trajectories in the poslist (it sums up
    the differences within each field in the posList
    
    Args:
        posList (list of list of [int, int]):
                            list of frame positions, which are a 
                            lists of pairwise positions for each vial
        dists (list of np.arrays):
                            output of :func:`computeDistancesFromPosList`       
    
    Returns:
        accDist (np.array(n,2*vialNo)):
                            matrix with the differences of each minute
                            each vial is representated with 2 columns  
    """
    # delete distance that are obvious errors
    for d in dists:
        d[d > 25] = 0
        
    # accumulate distances for each minute
    accDist = [[] for i in range(4)]
    cnt = 0
    for minute in posList:
        rng = slice(cnt, cnt+len(minute))
        for i in range(len(accDist)):
            accDist[i].append(np.sum(dists[i][rng]))
            
        cnt += len(minute)
        
    accDist = np.asarray(accDist)
    
    return accDist
    
def filterJumps(posList, dists, thresh):
    """
    Compute returns boolean arrays indicating if distances are greater than
    *thresh*
    
    Args:
        posList (list of list of [int, int]):
                            list of frame positions, which are a 
                            lists of pairwise positions for each vial
        dists (list of np.arrays):
                            output of :func:`computeDistancesFromPosList`  
        thresh (float/int):
                            threshold
    
    Returns:
        filterList (np.array(n,2*vialNo)):
                            boolean matrix with the differences of each minute
                            each vial is representated with 2 columns  
    """
    # build filter list
    filterList = [[] for i in range(4)]
    cnt = 0
    for minute in posList:
        rng = slice(cnt, cnt+len(minute))
        for i in range(len(filterList)):
            filterList[i].append(np.asarray(dists[i][rng]) > thresh)
        
        cnt += len(minute)
        
    return filterList

def getJumpPositions(filterList, minute):    
    """
    Get frame numbers where *filterList* is True within the given *minute*
    
    Args:
        filterList:
                            output of :func:`filterJumps`
        minute (int):
                            selected minute
        
    Returns:
        frame numbers (np.array):
                            frames where filterList is True in the given *minute*
    """
    b = np.zeros((filterList[0][minute].shape), dtype=np.bool)
    for i in range(4):
        x = filterList[i][minute]
        b = np.logical_or(b,x)
        
    return np.arange(len(b))[b]

def plotTrajectorySummery(accDist, fileList, ax, spanPos, vE, spanWidth=3):
    """
    plot actogram
    
    Args:
        accDist (np.array):
                            accDist, output fron :func:`computeTrajectorySummary`
                            
        fileList (list of strings):
                            fileList (list of strings):
                            list of file names of the videos that the
                            positions refer to (usually retrieved from
                            the names of the position files)
                            The .mp4 is not necessary, it is just used
                            to get the timestamp of each minute
        ax (matplotlib axis):
                            axis to plot in
        spanPos (int):
                            position of needle/pointer
        vE (videoExplorer):
                            used to convert filenames into date-time stamps
        spanWidth (int):
                            amount of days the needle/pointer covers
    """
    import numpy as np
    import pylab as plt
    
    color = ['r', 'g', 'y', 'b']
    name = ['Ab +RU', 'Ab -RU', 'dilp', 'wDah']
    for i in range(3,-1,-1):
        v = accDist[i]
        
        smoothLen = 31.0
        m = np.convolve(v, np.ones(smoothLen)/smoothLen, 'same')
        
        #[val, filenames] = zip(*diff)
        
        ax.plot(np.arange(m.shape[0]), m, color[i], label=name[i])
        
        plt.ylim([0, 3500]) 
        plt.xlim([0, m.shape[0]]) 
    
        
    rng = range(0,m.shape[0], 60)
    rng.append(m.shape[0]-1)    
    
    #ax.set_xticklabels(rng, [vE.fileName2DateTime(fileList[i], ending='npy') for i in rng], rotation=45, ha='right')
    plt.xticks(rng, [vE.fileName2DateTime(fileList[i], ending='npy') for i in rng], rotation=45, ha='right')
    ax.set_ylabel('Movement in mm / min')
    
    # plot night times
    ax.axvspan(0, 60*10, ymin=0, ymax=3500, color='#CCCCCC')
    ax.axvspan(60*13 + 60*10, 60*13 + 60*20, ymin=0, ymax=3500, color='#CCCCCC')
    ax.axvspan(60*13*2 + 60*10*2, len(fileList), ymin=0, ymax=3500, color='#CCCCCC')
    
    # plot position needle/pointer
    ax.axvspan(spanPos, spanPos + 3, ymin=0, ymax=3500, color='#FF4500')
    ax.legend()
    
    
def saveScatters(accDist, fileList, posList, idx, 
                    savePath="/tmp/scatter_{0:05d}.png"):
    """
    Save scatterplot of two minutes of trajectories over actogram
    
    Args:
        accDist (np.array):
                            accDist, output fron :func:`computeTrajectorySummary`
                            
        fileList (list of strings):
                            fileList (list of strings):
                            list of file names of the videos that the
                            positions refer to (usually retrieved from
                            the names of the position files)
                            The .mp4 is not necessary, it is just used
                            to get the timestamp of each minute
        posList (list of list of [int, int]):
                            list of frame positions, which are a 
                            lists of pairwise positions for each vial
        idx (int):
                            position in posList to be plotted
        savePath (string):
                            path where to save the figure (can have a format
                            {0} that will be filled with *idx* - number
    """
    #%pylab #inline
    import pylab as plt
    import numpy as np
    from time import time
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.gridspec as gridspec
    print idx
    
    shiftColor =  {'red':   ((0.0+0.0*0.25, 0.5, 0.2),# 1st vial
                            (0.0+0.9*0.25, 0.5, 0.5),
                            (0.0+1.0*0.25, 1.0, 1.0), 
                            (0.25+0.0*0.25, 0.0, 0.0),# 2nd vial
                            (0.25+0.0*0.25, 0.0, 0.0),
                            (0.25+1.0*0.25, 0.0, 0.0), 
                            (0.50+0.0*0.25, 0.1, 0.1),# 3rd vial
                            (0.50+0.9*0.25, 0.5, 0.5),
                            (0.50+1.0*0.25, 1.0, 1.0), 
                            (0.75+0.0*0.25, 0.0, 0.0),# 4th vial
                            (0.75+0.9*0.25, 0.0, 0.0),
                            (0.75+1.0*0.25, 0.0, 0.0), 
                            ),
                  'green': ((0.0+0.0*0.25, 0.0, 0.0),# 1st vial
                            (0.0+0.9*0.25, 0.0, 0.0),
                            (0.0+1.0*0.25, 0.0, 0.0), 
                            (0.25+0.0*0.25, 0.1, 0.1),# 2nd vial
                            (0.25+0.9*0.25, 0.5, 0.5),
                            (0.25+1.0*0.25, 1.0, 1.0), 
                            (0.50+0.0*0.25, 0.1, 0.1),# 3rd vial
                            (0.50+0.9*0.25, 0.5, 0.5),
                            (0.50+1.0*0.25, 1.0, 1.0), 
                            (0.75+0.0*0.25, 0.05, 0.05),# 4th vial
                            (0.75+0.9*0.25, 0.2, 0.2),
                            (0.75+1.0*0.25, 0.5, 0.5), 
                            ),
                  'blue':  ((0.0+0.0*0.25, 0.2, 0.2), # 1st vial
                            (0.0+0.9*0.25, 0.1, 0.1),
                            (0.0+1.0*0.25, 0.0, 0.0),  
                            (0.25+0.0*0.25, 0.0, 0.0),# 2nd vial
                            (0.25+0.0*0.25, 0.0, 0.0),
                            (0.25+1.0*0.25, 0.0, 0.0), 
                            (0.50+0.0*0.25, 0.0, 0.0),# 3rd vial
                            (0.50+0.9*0.25, 0.0, 0.0),
                            (0.50+1.0*0.25, 0.0, 0.0), 
                            (0.75+0.0*0.25, 0.1, 0.1),# 4th vial
                            (0.75+0.8*0.25, 0.6, 0.6),
                            (0.75+1.0*0.25, 1.0, 1.0), 
                            )
                 } 
    
    #figure(figsize=(29.93,11.11))
    #fig = plt.figure(figsize=(29.75,11.15))
    fig = plt.figure(figsize=(29.93,11.11))
    
    gs = gridspec.GridSpec(2, 1, height_ratios=[1,0.3], width_ratios=[1,1])
    
    #ax = axes(axisbg='black')    
    
    # [left, bottom, width, height]
    video = [0.0, 0.2, 1.0, 0.8]
    gobalPlot = [0., 0.0, 1.0, 0.2]
    
    ax = fig.add_subplot(gs[0], axisbg='black') 
    t = time()
    
    x = [posList[idx][k][i][1] for k in range(len(posList[idx])) for i in range(4)]
    x += [posList[idx+1][k][i][1] for k in range(len(posList[idx+1])) for i in range(4)]
    x += [posList[idx+2][k][i][1] for k in range(len(posList[idx+2])) for i in range(4)]
    y = [posList[idx][k][i][0] for k in range(len(posList[idx])) for i in range(4)]
    y += [posList[idx+1][k][i][0] for k in range(len(posList[idx+1])) for i in range(4)]
    y += [posList[idx+2][k][i][0] for k in range(len(posList[idx+2])) for i in range(4)]
    
    
    noVials = 4
    
    N = len(x) / noVials
    colMap = LinearSegmentedColormap("BlueRed", shiftColor, N=N*noVials)
    
    # build indexing range that indexes the colormap for each data point to
    # encode color of vial and position
    b = [[i + k * N] for i in range(N) for k in range(noVials)]
    from itertools import chain 
    colRng = list(chain.from_iterable(b))
    #colRng = range(N) * 4
    
    ax.scatter(x, y, s=5, c=colRng, cmap=colMap,lw = 0) 
    plt.xlim(0,1920)
    plt.ylim(0,1080)
    plt.gca().invert_yaxis()
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])    
    
    plt.text(400, 1050, r"A$\beta$ $+$RU", color="#FF2222", fontsize=20)
    plt.text(750, 1050, r"A$\beta$ $-$RU", color="#22FF22", fontsize=20)
    plt.text(1100, 1050, r"dilp", color="#FFFF00", fontsize=20)
    plt.text(1380, 1050, r"wDah", color="#0088FF", fontsize=20)
    
    plt.text(0.5, 0.95, vE.fileName2DateTime(fileList[idx], ending='npy'), color="#AAAAAA", fontsize=18, horizontalalignment='center', transform = ax.transAxes)
    
    
    #title("{0}".format(idx))
    
    ax2 = fig.add_subplot(gs[1])#plt.axes(gobalPlot)    
    plotTrajectorySummery(accDist, fileList, ax2, spanPos=idx, vE=vE, spanWidth=2)
       
    fig.tight_layout()
    
    plt.savefig(savePath.format(idx), pad_inches=0, bbox_inches='tight', dpi=100)
    
    plt.close("all")
    plt.clf()
    print idx, time() - t
    


import matplotlib.pyplot as plt
import sys, os, glob
sys.path.append('/home/peter/code/pyTools/')

import numpy as np
from pyTools.system.videoExplorer import *
from matplotlib.colors import LinearSegmentedColormap
import os
from time import time
def plotTrajectories(folder='/run/media/peter/Elements/peter/data/tmp-20130506/'):
    """
    Example how trajectory plotting works using the clusters of IPython notebook
    """

    vE = videoExplorer()
    fileList  = []
    posList = []

    t = time()
    for root,  dirs,  files in os.walk(folder):
        files = files
        for f in files:
            if f.endswith('npy'):
                #fl = open(root + '/' + f, 'r')
                path = root + '/' + f
                fileList.append(path)
                posList.append(np.load(path))            

    #sort both lists based on the file name
    posList = [x for y, x in sorted(zip(fileList, posList))]
    fileList = sorted(fileList)
    print time() - t
    
    
    from IPython.parallel import Client
    rc = Client()
    print rc.ids
    dview = rc[:]
        
    dview.block=True
    dview['accDist'] = accDist
    dview['fileList'] = fileList
    dview['posList']= posList
    dview['saveScatters'] = saveScatters
    dview['plotTrajectorySummery'] = plotTrajectorySummery
    dview['vE'] = vE
    
    t = time()
    lview = rc.load_balanced_view()
    lview.block = True
    res = lview.map(lambda x: saveScatters(x), range(0, len(posList)-2), chunksize=10)
    print time() - t
    
if __name__ == "__main__":
    from skimage import data
    lena = data.lena()
    
    imView = imgViewer()
    
    imView.show(lena)
    
    imView.showPatch(lena, [200, 50], [50, 50], 2)
    plt.show()
