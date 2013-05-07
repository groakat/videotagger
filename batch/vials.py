"""
.. module:: vials
   :platform: Unix, Windows
   :synopsis: This class is used to batch-process videos to retrieve fly positions 
        for each vial. 

.. codeauthor:: Peter Rennert <p.rennert@cs.ucl.ac.uk>


"""


import numpy as np
import png
from pyTools.imgProc.imgViewer import *
from pyTools.libs.fspecial import *
from pyTools.system.videoExplorer import *
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import datetime
import warnings
import pyTools.libs.tifffile as tf
import subprocess

shiftColor = {'red':   ((0.0, 0.0, 0.0),
                        (0.5, 0.0, 0.1),
                        (1.0, 1.0, 1.0)),

              'green': ((0.0, 0.0, 0.0),
                        (1.0, 0.0, 0.0)),

              'blue':  ((0.0, 0.0, 1.0),
                        (0.5, 0.1, 0.0),
                        (1.0, 0.0, 0.0))
             }  

class Vials(object):
    """
        Vials class
        
        This class is used to batch-process videos to retrieve fly positions 
        for each vial.        
    """
    def __init__(self,  rois=None, gaussWeight=1000, sigma=10, xoffsetFact=0.7, 
                updateLimit = 5000, clfyFunc=None, acceptPosFunc=None,
                acceptPosFuncArgs=None):
        """
        
        Args:            
            rois (2D-list of int):      
                                        list of x begining and ends of
                                        region of interests for each vial
            
            **Settings for distance matrix**
            
            This parameters control the bias of the distance matrix.
            The distance matrix is masked by a parabola and weigthed by a
            Gaussian kernel.
            
            The idea behind this concept is, that flies as well as their 
            shadows generate large responses in the difference image. 
            Therefore the search for the fly center (meanshiftMin) has to
            be biased towards away from the expected location of the shadows
            
            gaussWeight (int):  
                                multiplier used to give weighting of distance
                                matrix for mean-shift proper values (if this
                                value is too low, the mean-shift will converge
                                very slow, if too high the mean shift will 
                                constantly overshoot). To set this value is 
                                *tricky*. Try to generate the mask (see code)
                                by your self, until it gives you sensible
                                values.
            sigma (int):        
                                Sigma for the gaussian weighting on the 
                                distance matrix (used in mean-shift-min)
            xoffsetFact(int):   
                                vertical shift of mask of distance matrix
                                
            **Settings for the update procedure**
            
            The background will be updated constantly within a certain time
            interval. Within each interval the first reliable fly position
            in each vial is used to update the background model with the 
            current image (exclusive the fly)
                                
            updateLimit (int):
                                number of frames until the background model gets
                                updated.-1 for no update
                                
            clfyFunc (function):
                                function that is used to decide whether a 
                                fly position is reliable or not.
                                
                                - Input: This function takes an np.ndarray
                                - Return: This function has to return a bool
                                
                                have a look at :func:`checkIfPatchShowsFly`
                                for an example that could be used (has to
                                be wrapped into a lambda function)
                                
            acceptPosFunc (function):
                                if an alternative way than simply accepting
                                the strongest response from the background 
                                subtration should be used for determining
                                the position of the fly in a vial.
                                Exmaple: :func:`Vials.acceptPosFunc` does
                                maximum supression if response is not high
                                enough and the extracted patch cannot be
                                classified as fly.
                                
                                - Input: please refer to :func:`Vials.acceptPosFunc`
                                - Output: [int, int]
            
            acceptPosFuncArgs (dict):
                                dictionary carrying the additional arguments for
                                acceptPosFunc. 
        """
        self.rois = rois
        self.iV = imgViewer()
        distMat = self.generateDistanceMat([65, 65])
        gaussKernel = fspecial('gaussian', N=66, Sigma=sigma) * gaussWeight
        self.mask = [distMat[0] * self.generateParabola(xoffsetFact=xoffsetFact) * gaussKernel, 
                     distMat[1] * self.generateParabola(xoffsetFact=xoffsetFact) * gaussKernel]
        self.maskFlip = [self.mask[0], np.flipud(-self.mask[1])]
        self.update = None          # image that contains updated background
        self.updateLimit = updateLimit   # how often getFlyPositions has to get 
                                    # called before update gets uploaded to
                                    # the background image
        self.updateCnt = 0          # counter for the updateLimit        
        if rois is not None:
            self.wasUpdated = [False] * len(rois)
        else:
            self.wasUpdated = None  # boolean list that contains True or False
                                    # for each roi in rois
                                    # has to be reset when update is used the 
                                    # first time
                               
        self.baseSaveDir = None
        self.currentFile = None
        
        self.clfyFunc = clfyFunc    # used in getFlyPositions to determine if
                                    # detected fly should be used for an
                                    # update of the background
                                    
        self.acceptPosFunc = acceptPosFunc # used in replacement for localizeFly
        self.acceptPosFuncArgs = acceptPosFuncArgs # additional arguments
        
        self.bgModel = None         # will be set in extractPatches
        self.currentBgImg = None
        
    def batchProcessImage(self,  img,  funct,  args):
        """
            **Warning:** this function does not work
        
            processes function for each vial
            
            Args:
                img (numpy.array):       
                                    image that is going to be processed
                funct (function):   
                                    function that is batch processed
                args (dictionary):
                                    function arguments pass "vial" as argument 
                                    for image
        """
        key = args.keys()[args.values().index('vial')]
        for vial in self.rois:
            args[key] = img[vial[0]:vial[1]]            
            funct(**args)
            
    def getVialMin(self, diff):
        """
        Returns the minimum in diff(Image) for each vial. The returned 
        coordinates are with respect to the *vial* origin
        
        Args:        
            diff (ndarray):
                                    difference image 
                                            
        Returns:        
            List of [int, int] containing the [x,y] coordinates of the minimum
            in each vial        
            
        .. seealso::
            :func:`getVialMinGlobal`
        """        
        diffMin = [None] * len(self.rois)
        for i in range(len(self.rois)):            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]                        
            diffMin[i] = np.unravel_index(np.argmin(vDiff), vDiff.shape)      
            
        return diffMin
    
    def getVialMinGlobal(self, diff):
        """
        Returns the minimum in diff(Image) for each vial. The returned 
        coordinates are with respect to the *image* origin
        
        Args:        
            diff (ndarray):
                                    difference image 
                                            
        Returns:        
            List of [int, int] containing the [x,y] coordinates of the minimum
            in each vial        
            
        .. seealso::
            :func:`getVialMin`
        """
        diffMin = [None] * len(self.rois)
        for i in range(len(self.rois)):            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]                        
            diffMin[i] = np.unravel_index(np.argmin(vDiff), vDiff.shape)
            diffMin[i] = [diffMin[i][0], diffMin[i][1] + vial[0]]
            
        return diffMin
        
    def plotVialMin(self,  diff,  windowSize=[60, 60]):
        """
        Plots the vial minimum (strongest response from the difference image)
        in the context of the original difference image. The patches of the 
        given window size are slightly zoomed.
        
        Args:
            diff (np.ndarray):
                                    any numpy image 
            windowSize ([int, int]):
                                    size of patches that are getting 
                                    extracted and shown        
        """
        #figure, border = plt.subplots()
        figure = plt.figure(figsize=(11,7))
        diffMin = [None] * len(self.rois)
        for i in range(len(self.rois)):
            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]
                        
            diffMin[i] = np.unravel_index(np.argmin(vDiff), vDiff.shape)
            fig = self.iV.showPatch(vDiff, np.asarray(diffMin[i]), windowSize, 2, 
                            fig=figure,  offsetX=0.4 * i)
        
        #border.axis('off')
        ax = figure.add_axes([0.4 * (i+1), 0.3, 0.2, -0.02])
        ax.axis('off')
        plt.show()
        plt.draw()
        
        return diffMin
    
    def getFlyPositions(self, frame, bgImg, img=None, debug=False,
                        clfyFunc=None, patchSize=[64,64]):
        """
        Returns positions of flies within all vials.
        
        This function searches for the fly positions as well as it manages the
        update of the background.
        
        Args:
            frame (np.ndarray):
                                image on which the flies are searched in
            bgImg (pyTools.videoProc.backgroundImage):
                                background image for background subtraction
            patchSize ([int, int]):
                                size of extracted patch                                
            clfyFunc (function):
                                function that is used to decide whether a 
                                fly position is reliable or not.
                                
                                - Input: This function takes an np.ndarray
                                - Return: This function has to return a bool
                                
                                have a look at :func:`checkIfPatchShowsFly`
                                for an example that could be used (has to
                                be wrapped into a lambda function)
            
            **Debug options**
            
            img (np.ndarray):
                                original image (same as frame argument), for
                                backward compability
            debug (bool):
                                if True vial minima, as well as the meanshiftMin
                                procedure will be plotted for each vial
                                (very slow)
                                
        Returns:
            pos: 
                list of [int, int] the [x,y] position of the flies
            
            [pos, img]:
                if debug==True, it also returns the difference image from the 
                background subtraction:            
        
        """
        if clfyFunc is None:
            if self.clfyFunc is not None:
                clfyFunc = self.clfyFunc
            else:
                clfyFunc = lambda patch: np.min(patch.flatten()) < -250
        
        diffImg = bgImg.subtractStack(frame)
        if debug:
            plotIt = True
            retIt = True
        else:
            plotIt = False
            retIt = False
            
        initPos = self.getVialMinGlobal(diffImg)
        pos = []
        for i in range(len(initPos)):
            p = initPos[i]
            if self.acceptPosFunc is None:
                actPos = self.localizeFly(diffImg, p, img=img, 
                                        plotIterations=plotIt, retIt=retIt)
            else:
                actPos = self.acceptPosFunc(self, diffImg, p, i, img=img, 
                                        plotIterations=plotIt, retIt=retIt,
                                        args=self.acceptPosFuncArgs)
            if debug:
                pos.append(actPos[0])   
            else:
                pos.append(actPos)
                
            if self.updateLimit == -1:
                # do not update the background model at all
                continue
            
            if self.wasUpdated[i]:
                # if there is already a new update, do not bother to compute
                # everything again
                continue
            
            patch = self.iV.extractPatch(diffImg, 
                            [pos[i][0], pos[i][1]], patchSize)
            
            if clfyFunc(patch):
                #print("getFlyPositions - minVal", minVal)
                if self.currentBgImg is self.bgModel.getBgImg(frame,debug=True):
                    self.updateBackgroundMask(frame, bgImg, i, pos[i], 
                                              [300, 100])
                else:
                    # make sure that old update image is written at this frame
                    # (with the old content of course)
                    print("background changed, write update")
                    self.updateCnt = self.updateLimit
        
        self.updateCnt += 1
        if self.updateCnt >= self.updateLimit:
            self.updateBackgroundModel()
        
        if not debug:
            return pos
        else:
            return pos, diffImg
    
    def localizeFly(self, diffImg, startPos, img=None, plotIterations=False,
                    retIt=False):
        """        
        returns fly center given an intial start position. The function ensures 
        to correct for shadows occuring at the bottom and the top of the vial
        correctly by using a seperate mask for each case.
        
        The function employs :func:`meanShiftMin`, an iterative mean-shift 
        inspired method to find the center of the response in the difference
        image
        
        Args:
            diffImg (np.ndarray):
                                difference image
            startPos ([int, int]):
                                Intital position of optimization procedure. (see
                                also :func:`getVialMinGlobal`)
            
            **Debug options**
            
            img (np.ndarray):
                                original image, used for plotting the optimzation
                                steps. Needs to be given if plotIterations=True
            plotIterations (bool):
                                if True, :func:`meanShiftMin` will plot its 
                                iterations
            retIt (bool):
                                if True, :func:`meanShiftMin` iterations will
                                be returned as list (see :func:`meanShiftMin`)
                                
        Returns:
            list([int, int]):
                the [x,y] positions for each vial
            
            list of positions of each iteration:
                if retIt == True               
                
        .. seealso::
            :func:`meanShiftMin`, :func:`getVialMinGlobal`
        """
        if startPos[0] < 500:
            return self.meanShiftMin(diffImg, self.maskFlip, startPos, img=img,
                                     N=20, plotIterations=plotIterations, 
                                     retIt=retIt, viewer=self.iV)
        else:    
            return self.meanShiftMin(diffImg, self.mask, startPos, N=20, 
                                plotIterations=plotIterations, img=img,
                                retIt=retIt, viewer=self.iV)
                                
    def extractPatches(self, pathList, bgModel, baseSaveDir='/tmp/'):
        """
        extracts all fly locations from all videos in the path list and saves
        them as individual videos (centered around the flies) and position files
        in the given directory.
        
        It automatically chooses the right background model based on the time
        the video was captured.
        
        Args:
            pathList (list([datetime, string])):
                                list of videos that should be processed. The 
                                pathList can be generated with the methods of 
                                :mod:`pyTools.system.videoExplorer`
                                
                                - datetime: datetime object representing the 
                                            capture time of the video
                                - string:   path to video
                            
            bgModel (:class:`pyTools.videoProc.backgroundModel`):
                                model holding background images for different
                                times (currently just day and night)
            baseSaveDir (string):
                                folder that will hold the new video data
        
        """
        self.baseSaveDir = baseSaveDir
        self.bgModel = bgModel
        
        for p in pathList:
            #bgImg = bgModel.getBgImg(p[0].time(), debug=True)
            self.extractPatchesFromList([p[1]], baseSaveDir, bgModel, self)
            
    def updateBackgroundMask(self, frame, bgImg, vialNo, center, patchSize):
        """
        updates mask of background model. It will mask the area of the given
        vial exclusive the given patch size around the center (fly)
        
        The method manages updates done previously for other vials so that the 
        background model can be efficiently updated once.
                
        Args:
            frame (np.ndarray):
                                image (current frame)
            bgImg (:class:`pyTools.videoProc.backgroundModel`):
                                background image that will be updated
            vialNo (int):   
                                number of vial to update
            center ([int, int]):
                                center around patch (fly location)
            patchSize ([int, int]):
                                area around center that is excluded from the 
                                update (*make it generous, consider shadows*)
                                
        .. seealso::
            :func:`pyTools.videoProc.backgroundModel.createUpdatedBgImg`
        
        """
        mask = self.createBackgroundUpdateMask(frame, vialNo, center, patchSize)
        if self.update == None:            
            self.update = bgImg.createUpdatedBgImg(frame, mask)
            self.wasUpdated = [False] * len(self.rois)
            self.wasUpdated[vialNo] = True
        else:
            if self.wasUpdated[vialNo] is not True:
                self.update[mask == 1] = frame[mask == 1]
                self.wasUpdated[vialNo] = True        
        
        print("vials.updateBackgroundMask:", self.updateCnt, self.updateLimit, vialNo, center)            
        
    
    def createBackgroundUpdateMask(self, frame, vialNo, center, patchSize):
        """
            Creates a mask to cut the frame without the defined path
            
            Args:
                frame (ndimage):  
                                frame shape will be used as reference for mask
                vialNo (int):     
                                index for vial rois
                center (int, int): 
                                center of patch
                patchSize ([int, int]):
                                size of patch
                                
            Returns:
                boolean mask
        """
        mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.bool)
        vialRng = slice(self.rois[vialNo][0], self.rois[vialNo][1])
        rngX, rngY = self.iV.getValidPatchRange(mask, center, patchSize)
        
        # erase everything outside of the vial
        mask[:, 0:vialRng.start] = 0
        mask[:, vialRng.stop :] = 0
        
        # erase patch around fly
        mask[rngX, rngY] = 0
        
        return mask
        
        
    def updateBackgroundModel(self):
        self.updateCnt = 0
        if self.update is not None:
            self.currentBgImg.updateBackgroundModel(self.update)
            print "update backgroundmodel"
            
            if self.baseSaveDir is not None:                
                bgFilename = os.path.basename(self.currentFile).strip('.mp4')                    
                baseFolder = constructSaveDir(self.baseSaveDir, 
                                              self.currentFile)    
                bgFilename = baseFolder + '/' + bgFilename
                bgFilename += '-bg-{0}-{1}-{2}-{3}.png'
                plt.imsave(bgFilename.format(self.wasUpdated[0],
                                             self.wasUpdated[1],
                                             self.wasUpdated[2],
                                             self.wasUpdated[3]),
                            self.update)
            
            self.update = None
            
        self.wasUpdated = [False] * len(self.rois)
    
    @staticmethod
    def plotVialWithPatch(img,  vials):
        """
        Plots (and highlights) given areas in vials.
        
        Can be used to viualize fly detections.
        
        Args:
            img (np.ndarray):
                                image that is displayed underneath
            vials (list of dictionary):
                                patches that are displayed
                                (see next line for dictionary defintion)                    
                        *dictionary*:         
                                        
                        - 'roi':([int,int])         vial region of interests
                        - 'patch':(np.ndarray)      image of patch
                        - 'center':([int,int])      center of patch wrt roi
                        - 'patchSize':([int,int])   size of patch frame in roi
        
        """
        iV = imgViewer()
        figure = plt.figure(figsize=(11,7))
        i = 0
        for vial in vials:            
            roi = vial.get('roi')
            vialImg = img[:, roi[0]:roi[1]]
            
            #diffMin = np.unravel_index(np.argmin(vDiff), vDiff.shape)
            fig = iV.showPatch(vialImg, 
                                    center=vial.get('center'), 
                                    patchSize=vial.get('patchSize'), 
                                    patch_zoom=2, 
                                    fig=figure,  
                                    offsetX=0.4 * i, 
                                    patch=vial.get('patch'))
            i += 1
        
        #border.axis('off')
        ax = figure.add_axes([0.4 * (i+1), 0.3, 0.2, -0.02])
        ax.axis('off')
        plt.show()
        plt.draw()
        
    @staticmethod
    def getFlyPatches(bgImg, img, vial):  
        """
        Test function that extracts patches around the maxima responses of 
        background subtraction for each vial. No post processing is performed. 
        I.e. *no :func:`meanShiftMin` is used` to get fly center*
        
        Args:
            bgImg (pyTools.videoProc.backgroundImage):
                                background image
            img (np.ndarray):
                                image / frame
            vial (pyTools.batch.vials.Vials):
                                vials object
                                
        Return:
            patchesImg, patchesDiff:
            
                - image patch (of size [65,65]) around minimums in each vial
                - difference image patch (of size [65,65]) around minimums in each vial
        """
        bgFunc = bgModel.modelNight.backgroundSubtractionWeaverF
        bgModel.modelNight.configureStackSubtraction(bgFunc)
        diffImgTest = bgImg.subtractStack(img[0]) 
        
        minPos = vial.getVialMinGlobal(diffImgTest)
        
        #print minPos
        
        patchesImg = []
        patchesDiff = []
        for pos in minPos:
            patchesImg.append(imgViewer.extractPatch(img[0], 
                                                  np.asarray(pos), [65, 65]))
            patchesDiff.append(imgViewer.extractPatch(diffImgTest, 
                                                  np.asarray(pos), [65, 65]))
        
        return patchesImg, patchesDiff

    @staticmethod
    def generateDistanceMat(size=[65,65]):
        """
        generates a distance matrix of given size
        A distance matrix is a matrix with each coefficient
        being the distance from the patch center along either
        the horizontal or vertical axis
        """
        if (np.mod(size, 2) == [0,0]).all():
            raise ValueError("size has to be odd")
            
        horMat = np.zeros(tuple(size))
        vertMat = np.zeros(tuple(size))
        
        for i in range(vertMat.shape[0]):
            vertMat[i,:] = np.ones((1, vertMat.shape[1])) \
                            * (i - (vertMat.shape[0] - 1) / 2)
        
        for i in range(horMat.shape[1]):
            horMat[:,i] = np.ones((1, horMat.shape[0])) \
                            * (i - (horMat.shape[1] - 1) / 2)
            
        return [horMat, vertMat]
    
    @staticmethod
    def generateParabola(power=2, size=[65,65], xoffsetFact=0.7, width=60):
        r"""
        generates matrix of 1s in the area of the given
        parabola
        
        The parabola is generated with the formula: 
        :math:`\frac{1}{\text{width}}x^{\text{power}}` and shifted vertically
        by the xoffset.
        
        Args:
            power (int):
                                    power of parabola function
            size ([int, int]):
                                    size of patch
            xoffset (float: 0..1):
                                    vertical offset of parabola in per cent
            width (float):  
                                    denominator of factor before
        """
        a = np.zeros(tuple(size))
        for r in range(a.shape[0]):
            for c in range(a.shape[1]):
                if -(r - a.shape[0] * xoffsetFact) \
                 >= (np.abs(c - a.shape[1]/2)**power / width):
                    a[r,c] = 1
        return a
    
    @staticmethod
    def meanShiftMin(diffImg, mask, startPos, viewer, img=None, N=15,
                        plotIterations=False, retIt=False, patchSize=[65,65]):
        """
        fast optimization function that find a minimum within a 
        given patch

        diffImg will be used for the search and all values greater 
        than 0 will be clipped (minimization will be only done on
        negative values)

        Args:
            img  (np.ndarray):
                                image
            diffImg (np.array):
                                difference image (where min is searched for)
            mask (np.ndarray/binary):
                                weighting mask
            startPos ([float, float]):
                                initialization position for the optimization
            viewer (imageViewer):
                                any instance of an imageViewer object
            N  (int):
                                number of iterations
            patchSize ([int, int]):
                                size of patch
                            
            **Debug options**
            
            plotIterations (bool):
                                if True, iterations will be plotted
            retIt (boolean):
                                if True, iterations will be returned
                                as numpy arrays (images)
        
        Returns:
            pos (list([float],[float]))
            
            [pos, fig1]:
                if retIt == True, position as well as a figure with a plot 
                of the optimization steps
        """
        if (np.mod(patchSize, 2) == [0,0]).all():
            raise ValueError("size has to be odd")
        
        if retIt:
            plotIterations = True

        pos = startPos
        
        if plotIterations:
            if img == None:
                raise ValueError("img cannot be None if plotIterations = True")
            
            colMap = LinearSegmentedColormap("BlueRed", shiftColor, N=N)
            
            patchImg = viewer.extractPatch(img, np.asarray(pos), patchSize)
            patchDiff = viewer.extractPatch(diffImg, np.asarray(pos), patchSize)
        
            fig1 = plt.figure()
            #fig1, (ax1, ax2) = plt.subplots(nrows=2)
            ax1 = fig1.add_subplot(221)
            ax2 = fig1.add_subplot(222)
            fig1.set_size_inches(18.5,10.5)
            
            ax1.imshow(np.abs(patchDiff.clip(-np.Inf, 0)), 
                       interpolation='nearest')
            
            #diffFig = plt.figure()
            ax2.imshow(patchImg, interpolation='nearest')
            ax2.plot([patchDiff.shape[0] /2], [patchDiff.shape[1]/2], 'bo')
            
        patchPixNo = np.prod(patchSize)
        
        for i in range(N):
            #patchImg = viewer.extractPatch(img[0], np.asarray(pos), patchSize)
            patchDiff = viewer.extractPatch(diffImg, np.asarray(pos), patchSize)
            
            if (np.asarray(patchDiff.shape) != patchSize).any():
                warnings.warn("vials.meanShiftMin: detected position outside of image!")
                break
        
            a = np.abs(patchDiff.clip(-np.Inf, 0)) * mask[0]
            b = np.abs(patchDiff.clip(-np.Inf, 0)) * mask[1]
        
            horShift = np.sum(a.flatten()) / patchPixNo
            vertShift =  np.sum(b.flatten()) / patchPixNo#np.prod(b.shape)
            
            pos = [pos[0] + vertShift, pos[1] + horShift]
            
            if plotIterations:
                ax1.plot([patchDiff.shape[1] /2 - (startPos[1] - pos[1])], 
                         [patchDiff.shape[0] /2 - (startPos[0] - pos[0])], 'o', 
                         color=colMap(i))        
                ax2.plot([patchDiff.shape[1] /2 - (startPos[1] - pos[1])], 
                         [patchDiff.shape[0] /2 - (startPos[0] - pos[0])], 'o',
                         color=colMap(i))            
                #print pos
                
        if not retIt:
            return pos
        else:
            #figImg = viewer.fig2np(fig1)
            #plt.close(1)
            return [pos, fig1]
    
    @staticmethod
    def extractPatchesFromListDebug(fileList, baseSaveDir, bgImg, vE, viewer,
                                    vial, delTmpImg=False):
        """
        .. deprecated::  0.1.a1
            recent changes from :func:`extractPatchesFromList` were not updated
            in here
            
            use :func:`extractPatchesFromList` only
        
        """
        # build a rectangle in axes coords
        left, width = .25, .5
        bottom, height = .25, .5
        right = left + width
        top = bottom + height
        
        bgFunc = bgImg.backgroundSubtractionWeaverF
        bgImg.configureStackSubtraction(bgFunc)
        
        accPos = []
        for f in fileList:
            print f
            vE.setVideoStream(f, info=True, frameMode='RGB')
            cnt = 0
            for frame in vE: 
                #diffImg = bgImg.subtractStack(frame)    
                pos = vial.getFlyPositions(frame, bgImg, img=frame, debug=True)        
                baseName = baseSaveDir + os.path.basename(f).strip('.mp4') + '.v{0}.{1:05d}.png'
                
                for patchNo in range(len(pos)):
                    patch = viewer.extractPatch(frame, np.asarray(pos[patchNo][0]), [64, 64])
                    filename = baseName.format(patchNo, cnt)
                    #imsave(filename, patch)
                    fig = pos[patchNo][1]
                    ax3 = fig.add_subplot(223)
                    ax3.imshow(patch, interpolation='nearest')
                    ax4 = fig.add_subplot(224)
                    ax4.text(0.5*(left+right), 0.5*(bottom+top), '{0}'.format(cnt),
                            horizontalalignment='center',
                            verticalalignment='center',
                            fontsize=20, color='red',
                            transform=ax4.transAxes)
                    imsave(filename, viewer.fig2np(fig))
                    plt.close(fig)
                                    
                baseName = baseSaveDir + os.path.basename(f).strip('.mp4') + '.{0}{1}{2}'
                fl = open(baseName.format('', '', 'pos'), 'w')
                fl.write('{0}'.format(pos))
                fl.close()
                
                cnt += 1
            
            accPos.append([f, pos])
                        
            baseName = baseSaveDir + os.path.basename(f).strip('.mp4')# + '.{0}{1}.{2:05d}{3}'
            ffmpegCmd = "ffmpeg -y -i {0}.v{1}.%05d.png -c:v libx264 -preset veryslow -qp 0 -r 30 {0}.v{1}.mp4"
            for patchNo in range(len(pos)):
                p = subprocess.Popen(ffmpegCmd.format(baseName, patchNo)
                                    , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = p.communicate()[0]
            
            print("processed ", f)
            
        
        fl = open(baseSaveDir + '/all.pos', 'w')
        fl.write('{0}'.format(accPos))
        fl.close()
        
        if delTmpImg:
            baseName = baseSaveDir + os.path.basename(f[1]).strip('.mp4') + '.v*.*.png'
            for filePath in glob.glob(baseName):
                if os.path.isfile(filePath):
                    os.remove(filePath)
    
    @staticmethod
    def extractPatchesFromList(fileList, baseSaveDir, bgModel, vial, fps=30, 
                                 tmpBaseSaveDir='/tmp/', delTmpImg=True, 
                                 patchSize=[64, 64]):
        """
        extracts patches from a given list of files and encodes the patches
        in two versions ("lossless" mp4 and FFV1 (avi)) in the given folder.
        Furthermore this function saves a simple string version of the 
        positions from where the patches were extracted from in a file with
        the ending .pos
        
        Args:
            fileList (list(string)):
                                list of paths to videos
            baseSaveDir (string):
                                path to a directory that serves root for 
                                extracted videos
            bgImg (pyTools.videoProc.backgroundImage):
                                background image
            vial (pyTools.batch.vials.Vial):
                                vials object
            fps (int):
                                framerate for the output video
            tmpBaseSaveDir (string):
                                path to directory where patches will be saved
                                temporary 
            delTmpImg (bool):
                                if True temporary patch images will be deleted
            patchSize ([int, int]):
                                size of patches (area around detected location 
                                that is copied into the patches)
            
        
        """
        viewer = imgViewer()
        vE = videoExplorer()
        
        for f in fileList:
            # extract patches around flies for each frame
            patchPaths = []
            accPos = []
            
            vial.currentFile = f
            vE.setVideoStream(f, info=True, frameMode='RGB')
            cnt = 0
            for frame in vE:                 
                if cnt == 0:
                    # select correct background model
                    bgImg = bgModel.getBgImg(frame, debug=True)
                    if bgImg is not vial.currentBgImg:
                        bgFunc = bgImg.backgroundSubtractionWeaverF
                        bgImg.configureStackSubtraction(bgFunc)
                        vial.currentBgImg = bgImg
                  
                pos = vial.getFlyPositions(frame, bgImg, img=frame, debug=False)        
                baseName = tmpBaseSaveDir + os.path.basename(f).strip('.mp4') + \
                                                            '.v{0}.{1:05d}.tif'
                
                for patchNo in range(len(pos)):
                    patch = viewer.extractPatch(frame, np.asarray(pos[patchNo]),
                                                patchSize)
                    filename = baseName.format(patchNo, cnt)
                                         
                    tf.imsave(filename, patch)
                    patchPaths.append(filename)
                                    
                baseName = tmpBaseSaveDir + os.path.basename(f).strip('.mp4') + \
                                                                    '.{0}{1}{2}'
                
                cnt += 1
            
                accPos.append(pos)
            
            # at the last frame check if this background model is the same
            # as for the first frame. If not, probably a day/night switch 
            # occurred. So make sure that nothing of this minute is used
            # TODO
            if bgImg is not bgModel.getBgImg(frame, debug=True):
                print("background model changed this minute. DO SOMETHING")
                vial.updateBackgroundModel()
                
            # use ffmpeg to render frames into videos
            tmpBaseName = tmpBaseSaveDir + os.path.basename(f).strip('.mp4')
                        
            baseFolder = constructSaveDir(baseSaveDir, f)    
            baseName =  baseFolder + os.path.basename(f).strip('.mp4')
            
            # render images as avi for complete losslessness
            # ffmpeg -y -f image2 -r 29.97 -i /tmp/2013-02-19.00-01-00.v0.%05d.png -vcodec ffv1 -sameq /tmp/test.avi
            ffmpegCmd = "ffmpeg -y -f image2 -r {2} -i {3}.v{1}.%05d.tif -vcodec ffv1 -sameq -r {2} {0}.v{1}.avi"
            
            for patchNo in range(len(pos)):
                p = subprocess.Popen(ffmpegCmd.format(baseName, patchNo, fps, tmpBaseName),
                                    shell=True, stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)
                output = p.communicate()[0]
            
            # render images as mp4 for very fast playback
            #ffmpeg -y -f image2 -r 29.97 -i 2013-02-19.00-00-00.v0.%05d.tif -c:v libx264 -preset faster -qp 0 test.mp4
            ffmpegCmd = "ffmpeg -y -i {3}.v{1}.%05d.tif -c:v libx264 -preset faster -qp 0 -r {2} {0}.v{1}.mp4"
            for patchNo in range(len(pos)):
                p = subprocess.Popen(ffmpegCmd.format(baseName, patchNo, fps, tmpBaseName),
                                    shell=True, stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)
                output = p.communicate()[0]
                
            # delete images of frames
            if delTmpImg:
                for filePath in patchPaths:
                    os.remove(filePath)                    
            
            fl = open(baseFolder + os.path.basename(f).strip('.mp4') + '.pos', 'w')
            fl.write('{0}'.format(accPos))
            fl.close()
            
            print("processed ", f)
            
    @staticmethod
    def checkIfPatchShowsFly(patch, classifier, flyClass=1, debug=False):
        """
        Example definition of a clfyFunc (optional parameter in Vials.__init__)
        
        Args:
            patch (np.ndarray):
                                patch that is checked 
            classifier (sklearn classifier):
                                classifier that classifies a fly 
            flyClass (int):
                                class label representing a fly
            debug (bool):
                                printing out log data
        """
        if np.min(patch[30:35,30:35].flatten()) < -150:
            hog = computeHog(patch)
            clas = classifier.predict(hog)
            if  int(clas[0]) == flyClass:
                return True
            elif debug:
                print clas
                print "patch passed threshold, but classifier rejected it!"
        
        return False


    @staticmethod
    def acceptPosFunc(self, diffImg, startPos, vialNo, img, plotIterations, retIt, args):
        """
        Example function for a acceptPosFunc that can be defined in the 
        constructor of the class.
              
        Please have a look in the code how it works. Important are the input 
        arguments and the return value which should not be altered at all.
        
        
        In this case the classical fly localization is augmented with a sanity 
        check of the reported fly position. This is done by the use of a 
        previously trained SVM.
        
        The functions are defined outside and passed via the optional args.
        
        .. code-block:: python
        
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

            flyClassify = lambda patch: Vials.checkIfPatchShowsFly(patch, 
                                                                  flyClassifier,
                                                                  flyClass=1, 
                                                                  debug=True)
                                                                  
            acceptArgs = {'computeHog': computeHog, 
                          'noveltyClassfy': noveltyClassfy,
                          'flyClassify': flyClassify}
        
            Vials(roi, gaussWeight=2000, sigma=20,  xoffsetFact=0.6, 
                    clfyFunc=flyClassify, acceptPosFunc=acceptPosFunc,
                    acceptPosFuncArgs=acceptArgs)
        """
        computeHog = args['computeHog']
        noveltyClassfy = args['noveltyClassfy']
        flyClassify = args['flyClassify']
        
        for i in range(2):
            initPos = self.localizeFly(diffImg, startPos, img=img,
                                                plotIterations=plotIterations, retIt=retIt)

            patch = self.iV.extractPatch(diffImg, [initPos[0], initPos[1]], [64, 64])
            if np.min(patch) > -40:
                if not np.allclose(patch.shape, [64, 64]):
                    # patch is outside of the image
                    print "patch outside of image"
                    continue

                hog = computeHog(patch)
                if not(noveltyClassfy.predict(hog) == 1):
                    # hog features were not modelled, very likely to be background
                    continue

                if not(flyClassify is 1):
                    # position is valid
                    return initPos

                # do minimum suppresion
                diffImg[initPos[0]-32:initPos[0]+32, initPos[1]-32:initPos[1]+32] = 0
                startPos = self.getVialMinGlobal(diffImg)[vialNo]
            else:
                return initPos

        # return default position
        return [33, 33]

def constructSaveDir(baseSaveDir, filename):    
    folders = videoExplorer.splitFolders(filename)
    baseFolder = baseSaveDir + folders[-3] + "/" + folders[-2] + "/"
    
    if not os.path.exists(baseFolder):
        os.makedirs(baseFolder)
        
    return baseFolder

import pyTools.libs.faceparts.vanillaHogUtils as vanHog
from skimage.color import rgb2gray
import skimage.transform

def computeHog(patch):
    a = list(skimage.transform.pyramid_gaussian(patch, sigma=2, max_layer=1))
    return vanHog.hog(a[1], 9,3, 360, [0, 64, 0, 64])

if __name__ == "__main__":
#    from skimage import data
#    lena = data.lena()
#    
#    v = Vials()
#    
#    v1 = {  'roi':[0, 100], 'patch':lena[10:20, 10:20], 
#            'patchSize':[10, 10],  'center':[15, 15]}
#    v2 = {  'roi':[150, 250], 'patch':lena[10:40, 50:150], 
#            'patchSize':[10, 10],  'center':[15, 15]}
#    
#    v.plotVialWithPatch(lena, [v1, v2])

    
    import sys
    sys.path.append('/home/peter/code/pyTools/')

    import numpy as np
    from pyTools.system.videoExplorer import *
    from pyTools.videoProc.backgroundModel import *
    from pyTools.imgProc.imgViewer import *
    from time import time


    vE = videoExplorer()
    bgModel = backgroundModel(verbose=True, colorMode='rgb')
    viewer = imgViewer()
    roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
    vial = Vials(roi, gaussWeight=3000, sigma=15)
    
    import datetime as dt
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 21)
    rootPath = "/run/media/peter/Elements/peter/data/box1.0/"
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()

    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createDayModel(sampleSize=5)
    bgModel.createNightModel(sampleSize=10)

    testImg = vE.getRandomFrame(vE.getPathsOfList(vE.nightList), info=True, frameMode='RGB')
    
    testImg = vE.getRandomFrame(vE.getPathsOfList(vE.nightList), info=True, frameMode='RGB')
    bgImg = bgModel.modelNight
    img = testImg
    bgFunc = bgModel.modelNight.backgroundSubtractionWeaverF
    bgModel.modelNight.configureStackSubtraction(bgFunc)

    imgList = []
    diffImgList = []
    posList = []
    for i in range(50):
        figure(figsize=(20,20))
        filename = vE.nightList[i][1]
        testImg = vE.getFrame(filename, frameNo=0, info=False, frameMode='RGB')
        [testPos, diffImg] = vial.getFlyPositions(testImg, bgImg, img=testImg, debug=True)
        
        print(diffImg[testPos[0][0], testPos[0][1]], diffImg[testPos[1][0], testPos[1][1]], 
              diffImg[testPos[2][0], testPos[2][1]], diffImg[testPos[3][0], testPos[3][1]])
        
        imgList.append(testImg)
        diffImgList.append(diffImg)
        posList.append(testPos)
        
        title(filename)
