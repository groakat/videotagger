import numpy as np
from pyTools.imgProc.imgViewer import *
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pyTools.libs.fspecial import *

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
    def __init__(self,  rois=None, gaussWeight=1000, sigma=10):
        """
            INPUT:
                rois    2D-list of int      list of x begining and ends of
                                            region of interests for each vial
        """
        self.rois = rois
        self.iV = imgViewer()
        distMat = self.generateDistanceMat([65, 65])
        gaussKernel = fspecial('gaussian', N=66, Sigma=sigma) * gaussWeight
        self.mask = [distMat[0] * self.generateParabola() * gaussKernel, 
                     distMat[1] * self.generateParabola() * gaussKernel]
        self.maskFlip = [self.mask[0], np.flipud(-self.mask[1])]
        
    def batchProcessImage(self,  img,  funct,  args):
        """
            processes function for each vial
            INPUT:
                img     <numpy.array>       image that is going to be processed
                funct   <function handle>   function that is batch processed
                args    <dictionary>        function arguments 
                                            pass "vial" as argument for image
        """
        key = args.keys()[args.values().index('vial')]
        for vial in self.rois:
            args[key] = img[vial[0]:vial[1]]            
            funct(**args)
            
    def getVialMin(self, diff):
        diffMin = [None] * len(self.rois)
        for i in range(len(self.rois)):            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]                        
            diffMin[i] = np.unravel_index(np.argmin(vDiff), vDiff.shape)      
            
        return diffMin
    
    def getVialMinGlobal(self, diff):
        diffMin = [None] * len(self.rois)
        for i in range(len(self.rois)):            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]                        
            diffMin[i] = np.unravel_index(np.argmin(vDiff), vDiff.shape)
            diffMin[i] = [diffMin[i][0], diffMin[i][1] + vial[0]]
            
        return diffMin
        
    def plotVialMin(self,  diff,  windowSize=[60, 60]):
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
    
    def getFlyPositions(self, diffImg, img=None, debug=False):
        if debug:
            plotIt = True
            retIt = True
        else:
            plotIt = False
            retIt = False
            
        initPos = self.getVialMinGlobal(diffImg)
        pos = []
        for p in initPos:
            pos.append(self.localizeFly(diffImg, p, img=img, 
                                        plotIterations=plotIt, retIt=retIt))            
        return pos
    
    def localizeFly(self, diffImg, startPos, img=None, plotIterations=False,
                    retIt=False):
        if startPos[0] < 500:
            return self.meanShiftMin(diffImg, self.maskFlip, startPos, img=img,
                                     N=20, plotIterations=plotIterations, 
                                     retIt=retIt, viewer=self.iV)
        else:    
            return self.meanShiftMin(diffImg, self.mask, startPos, N=20, 
                                plotIterations=plotIterations, img=img,
                                retIt=retIt, viewer=self.iV)
                                
    def extractPatches(pathList):
        return Null
        
    
    @staticmethod
    def plotVialWithPatch(img,  vials):
        """
            Input:
                img     <np.ndarray>        image that is displayed underneath
                vials   <list of dictionary>    patches that are displayed
                                                see next line for dictionary
                                                definition
                        dictionary:         
                            'roi':[int,int]         vial region of interests
                            'patch':<np.ndarray>    image of patch
                            'center':[int,int]      center of patch wrt roi
                            'patchSize':[int,int]   size of patch frame in roi
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
            returns patches around minimums in each vial
            returns patch of image and difference image
        """
        bgFunc = bgModel.modelNight.backgroundSubtractionWeaverF
        bgModel.modelNight.configureStackSubtraction(bgFunc)
        diffImgTest = bgImg.subtractStack(img[0]) 
        
        minPos = vial.getVialMinGlobal(diffImgTest)
        
        #print minPos
        
        patchesImg = []
        patchesDiff = []
        for pos in minPos:
            patchesImg.append(viewer.extractPatch(img[0], 
                                                  np.asarray(pos), [65, 65]))
            patchesDiff.append(viewer.extractPatch(diffImgTest, 
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
        """
            generates matrix of 1s in the area of the given
            parabola

                (1/ width) * x ^ power
        
            INPUT:
                power     int        power of parabola function
                size      [int, int] size of patch
                xoffset   [0..1]     vertical offset of parabola
                                    in per cent
                width     float      denominator of factor before
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

            INPUT:
                img          np.array       image
                diffImg      np.array       difference image
                                            (where min is searched for)
                mask                        weighting mask
                startPos    [float, float]  initialization position for
                                            the optimization
                N           int             number of iterations
                plotIterations boolean      if True, iterations will be plotted
                retIt       boolean         if True, iterations will be returned
                                            as numpy arrays (images)
                patchSize   [int, int]      size of patch
                viewer      imageViewer     any instance of an imageViewer object
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
            
        
        for i in range(N):
            #patchImg = viewer.extractPatch(img[0], np.asarray(pos), patchSize)
            patchDiff = viewer.extractPatch(diffImg, np.asarray(pos), patchSize)
        
            a = np.abs(patchDiff.clip(-np.Inf, 0)) * mask[0]
            b = np.abs(patchDiff.clip(-np.Inf, 0)) * mask[1]
        
            horShift = np.sum(a.flatten()) / np.prod(a.shape)
            vertShift =  np.sum(b.flatten()) / np.prod(b.shape)
            
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
                diffImg = bgImg.subtractStack(frame)    
                pos = vial.getFlyPositions(diffImg, img=frame, debug=True)        
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
    def extractPatchesFromList(fileList, baseSaveDir, bgImg, bgImg, vE, viewer,
                                    vial, fps=30, delTmpImg=True):
        # build a rectangle in axes coords
        left, width = .25, .5
        bottom, height = .25, .5
        right = left + width
        top = bottom + height
        
        bgFunc = bgImg.backgroundSubtractionWeaverF
        bgImg.configureStackSubtraction(bgFunc)
        
        accPos = []
        for f in fileList:
            # extract patches around flies for each frame
            patchPaths = []
            vE.setVideoStream(f, info=True, frameMode='RGB')
            cnt = 0
            for frame in vE: 
                diffImg = bgImg.subtractStack(frame)    
                pos = vial.getFlyPositions(diffImg, img=frame, debug=False)        
                baseName = baseSaveDir + os.path.basename(f).strip('.mp4') + \
                                                            '.v{0}.{1:05d}.png'
                
                for patchNo in range(len(pos)):
                    patch = viewer.extractPatch(frame, np.asarray(pos[patchNo]),
                                                [64, 64])
                    filename = baseName.format(patchNo, cnt)
                    imsave(filename, patch)
                    patchPaths.append(filename)
                                    
                baseName = baseSaveDir + os.path.basename(f).strip('.mp4') + \
                                                                    '.{0}{1}{2}'
                fl = open(baseName.format('', '', 'pos'), 'w')
                fl.write('{0}'.format(pos))
                fl.close()
                
                cnt += 1
            
            accPos.append([f, pos])
            
            # use ffmpeg to render frames into videos
            baseName = baseSaveDir + os.path.basename(f).strip('.mp4')
            ffmpegCmd = "ffmpeg -y -i {0}.v{1}.%05d.png -c:v libx264 -preset veryslow -qp 0 -r {0} {1}.v{2}.mp4"
            for patchNo in range(len(pos)):
                p = subprocess.Popen(ffmpegCmd.format(fps, baseName, patchNo),
                                    shell=True, stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)
                output = p.communicate()[0]
                
            # delete images of frames
            if delTmpImg:
                for filePath in patchPaths:
                    os.remove(filePath)                    
            
            print("processed ", f)
            
        
        fl = open(baseSaveDir + '/all.pos', 'w')
        fl.write('{0}'.format(accPos))
        fl.close()

if __name__ == "__main__":
    from skimage import data
    lena = data.lena()
    
    v = Vials()
    
    v1 = {  'roi':[0, 100], 'patch':lena[10:20, 10:20], 
            'patchSize':[10, 10],  'center':[15, 15]}
    v2 = {  'roi':[150, 250], 'patch':lena[10:40, 50:150], 
            'patchSize':[10, 10],  'center':[15, 15]}
    
    v.plotVialWithPatch(lena, [v1, v2])
