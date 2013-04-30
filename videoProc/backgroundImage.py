import numpy as np
import scipy.weave as weave
from copy import copy

class backgroundImage(np.ndarray):
    __array_priority__ = 100
    
    def __new__(cls,  img):
        if img.dtype.kind in ('u'): 
            obj = np.asarray(img, dtype=np.int16).view(cls)
        else: 
            obj = np.asarray(img).view(cls)        
        obj.shiftList = []
        obj.bgStackF = []
        obj.subtractStackFunc = 0
        obj.fortranStyle = False
        obj.stackIdx = 0
        obj.bgStack = backgroundImage.calculateBackgroundStack(obj)
        
        return obj
        
    def resetShiftList(self):
        self.shiftList = []
        
    def subtractImg(self, img, offsetX=0, offsetY=0):
        diff = np.subtract(*self.alignImgPair([offsetX,  offsetY], 
                                              img, 
                                              self))
        
        if len(diff.shape) == 3:
            return np.sum(diff, axis=2)
        else:
            return diff   
            
    def subtractImgPadding(self, img, shift=[0, 0]):
        """
            subtract image from background image with any given shift using 
            padding to return an image of the same size as the input images
            INPUT:
                img             nd-array                image
                shift           [x, x]                  shift of image
                
            OUTPUT:
                difference image
        """
        self.shiftList.append(shift)
        diff = np.subtract(*self.alignImgPairPadding(shift, img, self))
        
        if len(diff.shape) == 3:
            return np.sum(diff, axis=2)
        else:
            return diff 
        
    def getValidROI(self,  reset=False):
        """
            returns ROI that is used by all shifted background images
        """
        ret = self.getValidSlices(self.shiftList, self.shape)
        if reset:
            self.resetShiftList()
        return ret
    
    def createBackgroundStack(self, fortranStyle=False, new=True):
        self.fortranStyle = fortranStyle
        if new:
            self.bgStack = self.calculateBackgroundStack(self)
        
        if(fortranStyle):
            self.bgStackF = copy(self.bgStack)
            if type(self.bgStackF) is list:
                for i in range(len(self.bgStackF)):
                    self.bgStackF[i] = self.bgStackF[i].reshape(
                                                (self.bgStackF[i].shape[1], -1),
                                                order='F')
            else:
                self.bgStackF = self.bgStackF.reshape(
                                                    (self.bgStack.shape[1], -1),
                                                    order='F')                
        #else:
            #self.bgStack = self.calculateBackgroundStack(self)
            
    def updateBackgroundStack(self):
        self.createBackgroundStack(self.fortranStyle, new=False)
        
    def configureStackSubtraction(self, func):
        """
            configures the backgroundImage object to call subtractStack function
            
            it will recreate the background stack (appropriate for the function
            to be called)
            
            Input:
                func    function pointer        a pointer to either
                                                - backgroundSubstractionStack
                                                - backgroundSubstractionWeaver
                                                - backgroundSubstractionWeaverF
        """
        if func == self.backgroundSubtractionStack:
            if self.bgStack == []:
                self.createBackgroundStack()
            self.subtractStackFunc = \
                lambda img: self.backgroundSubtractionStack(img, self.bgStack)
                
        elif func == self.backgroundSubtractionWeaver:
            if self.bgStack == []:
                self.createBackgroundStack()
            self.subtractStackFunc = \
                lambda img: self.backgroundSubtractionWeaver(img, self.bgStack)
                
        elif func == self.backgroundSubtractionWeaverF:
            if self.bgStackF == []:
                self.createBackgroundStack(fortranStyle=True)
            self.subtractStackFunc = \
               lambda img: self.backgroundSubtractionWeaverF(img, self.bgStackF)
               
        else:
            raise ValueError("func is not a background subtraction function" + 
                                "involving bgStack. Use help for more info")  
    
    def configureStackSubtractionCustom(self, func, fortranStyle=False):
        if fortranStyle:
            if self.bgStackF == []:
                self.createBackgroundStack(fortranStyle=True)
            self.subtractStackFunc = \
               lambda img: func(img, self.bgStackF)
        else:
            if self.bgStack == []:
                self.createBackgroundStack()
            self.subtractStackFunc = \
               lambda img: func(img, self.bgStack)
        
        
    def subtractStack(self, img):
        """
            Background subtraction using background stack for robust background
            subtraction. To configure the backgroundImage object, first call
            configureStackSubtraction() once before. 
            
            Input:
                img         nd array                image
        """
        if not self.subtractStackFunc == 0:
            return self.subtractStackFunc(img)
        else:
            raise RuntimeError("configureStackSubtraction() was not called" + 
                                "before calling this function")
                                
    def createUpdatedBgImg(self, frame, mask):
        """
            replace frame where mask == False with the backgroundImage
            
            Args:
                frame (ndarray):    input image
                mask (ndarray):     boolean mask
                
            Returns:
                ndarray:
                    updated frame
        """
        update = np.zeros(tuple(frame.shape), dtype=np.uint8)
        
        if len(update.shape) > 2:
            for i in range(update.shape[2]):
                update[:,:,i] = self.bgStack[i][self.stackIdx, :].reshape(tuple(mask.shape))
        else:
            update[:,:] = self.bgStack[self.stackIdx, :].reshape(tuple(mask.shape))            
        
        update[mask == 1] = frame[mask == 1]
        
        return update
    
    def updateBackgroundModel(self, update, level=-1):
        """
            inserts update into the existing background models
            
            Args:
                update (ndarray):
                            image that is to be inserted into the background 
                            model
                level (int):
                            position (in the background stack) where the image
                            is to be inserted. If level=-1, the backgroundImage
                            object will manage the level by itself, by iterating
                            trough the stack
        """
        if level == -1:
            level = self.stackIdx
            self.stackIdx = (self.stackIdx + 1) % self.bgStack[0].shape[0]
        
        for i in range(self.shape[2]):
            self.bgStack[i][level, :] = np.int16(update[:,:,i].flatten())
        self.updateBackgroundStack()
    
    
    @staticmethod
    def alignImgPair(shift, img, bg):      
        """
            aligns two images (incorporating the shift)
            useful to speed up algorithms that require to do operations on 
            neighbour pixels
        """
        if img.shape != bg.shape:
            raise ValueError("image dimension does not match background dimension")
                
        xShift = np.round(shift[0])
        yShift = np.round(shift[1])
        
        if xShift >= 0:
            bgRngX = slice(0,bg.shape[0] - xShift)
            imgRngX = slice(xShift, img.shape[0])        
        else:
            bgRngX = slice(-xShift, bg.shape[0])
            imgRngX = slice(0, img.shape[0] + xShift)
            
        if yShift >= 0:
            bgRngY = slice(0, bg.shape[1] - yShift)
            imgRngY = slice(yShift, img.shape[1])
        else:
            bgRngY = slice(-yShift, bg.shape[1])
            imgRngY = slice(0, img.shape[1] + yShift)
            
        if len(img.shape) == 3:
            return img[imgRngX,imgRngY, :], bg[bgRngX, bgRngY, :]
        else: 
            return img[imgRngX,imgRngY],  bg[bgRngX, bgRngY]
    
    @staticmethod
    def alignImgPairPadding(shift, img, bg):      
        """
            aligns two images (incorporating the shift)
            useful to speed up algorithms that require to do operations on 
            neighbour pixels however, it copies a blank padding border around 
            the output image so that it remains the same size as the input images
        """
        if img.shape != bg.shape:
            raise ValueError("image dimension does not match background dimension")
                
        xShift = np.round(shift[0])
        yShift = np.round(shift[1])
        
        if xShift >= 0:
            bgRngX = slice(0, bg.shape[0] - xShift)
            padX = slice(xShift, img.shape[0])        
        else:
            bgRngX = slice(-xShift, bg.shape[0])
            padX = slice(0, img.shape[0] + xShift)
            
        if yShift >= 0:
            bgRngY = slice(0, bg.shape[1] - yShift)
            padY = slice(yShift, img.shape[1])
        else:
            bgRngY = slice(-yShift, bg.shape[1])
            padY = slice(0, img.shape[1] + yShift)
            
        padBg = np.zeros(bg.shape, dtype=bg.dtype)
            
        if len(img.shape) == 3:
            padBg[padX, padY, :] = bg[bgRngX, bgRngY, :]
            return img, padBg
        else: 
            padBg[padX, padY] = bg[bgRngX, bgRngY]
            return img,  padBg
            
    @staticmethod
    def getValidSlices(shifts,  shape):
        """
            Ensures that slices have valid range (i.e. are within the boundaries
            of the image)
            
            INPUT:
                shifts      <list of [int, int]>        list of shifts
                shape       [int, int]                  shape of image
        """
        
        npShifts = np.asarray(shifts)
        
        if len(npShifts.shape) > 1:
            minV = np.min(npShifts,  axis=0)
            maxV = np.max(npShifts,  axis=0)
        else:
            minV = maxV = npShifts
        
        offsetX = [0, shape[0]]
        offsetY = [0, shape[1]]
            
        if maxV[0] > 0:
            offsetX[0] = maxV[0]
        if maxV[1] > 0:
            offsetY[0] = maxV[1]
        
        if minV[0] < 0:
            offsetX[1] = shape[0] + minV[0]
        if minV[1] < 0:
            offsetY[1] = shape[1] + minV[1]
        
        rngX = slice(*offsetX)
        rngY = slice(*offsetY)
        
        return rngX,  rngY
    
    @staticmethod
    def backgroundSubtractionShiftsNaive(img, bgImg, rngX=range(-2, 3), 
                                            rngY=range(-2, 3)):
        """
            Naive background subtraction employing shifts of background to 
            make subtraction robust to small changes in the background
            
            This method is very slow and is interally only used as reference
            for tests. Perhaps also the most easy to understand.
            
            All other background subtraction methods working with stacks, employ
            the same principle. But they operate on a precomputed background
            stack and implement further optimizations.
            
            Input:
                img         np.array            image
                bgImg       np.array            background image
                rngY        range               list of vertical shifts to be 
                                                performed by background
                rngX        range               list of horizontal shifts to be 
                                                performed by background
                                                
            Output:
                difference image
        """
                                         
        stack = np.zeros((img.shape[0], img.shape[1], len(rngX) * len(rngY)), dtype=bgImg.dtype)
        cnt = 0
        bgImg.resetShiftList()
        
        for x in rngX:
            for y in rngY:
                stack[:,:,cnt] = bgImg.subtractImgPadding(img, [x, y])
                cnt += 1
                
        diffImg = np.max(stack, axis=2)
        
        return diffImg
    
    @staticmethod
    def calculateBackgroundStack(bgImg, rngX=range(-2, 3), rngY=range(-2, 3)): 
        """
            precompute a stack of background images that can be used for
            robust background subtraction
        """
        
        bgImg.resetShiftList()  
        if len(bgImg.shape) > 2:
            bgStack = []
            for i in range(bgImg.shape[2]):
                bgStack.append(np.zeros((len(rngX) * len(rngY), 
                                         len(bgImg.flatten()) / bgImg.shape[2]), 
                                         dtype=bgImg.dtype))
            cnt = 0
            for x in rngX:
                for y in rngY:
                    curBg = bgImg.alignImgPairPadding([x, y], bgImg, bgImg)[1]
                    for i in range(bgImg.shape[2]):
                        bgStack[i][cnt, :] = curBg[:,:,i].flatten()
                    cnt += 1
                    
        else:
            bgStack = np.zeros((len(rngX) * len(rngY), len(bgImg.flatten())), 
                                dtype=bgImg.dtype)
            cnt = 0
            for x in rngX:
                for y in rngY:
                    bgStack[cnt, :] = \
                        bgModel.modelNight.alignImgPairPadding([x, y], 
                                                                bgImg, 
                                                                bgImg)[1].flatten()
                    cnt += 1              

        return bgStack
    
    @staticmethod
    def backgroundSubtractionStack(img, bgStack):
        """
            simple function to operate on precomputed background stacks 
            
            This method uses numpy functions only and is not very fast
            
            background gets subtracted from foreground (foreground objects 
            should appear negative on the output)
            
            Input:
                img         nd array                input image
                bgStack     stack of background  (see calculateBackgroundStack()
                            images                for computation)
                            !! needs to generated with fortranStyle=False !!
                            
            Output:
                difference image
        """
        
        ## This method has to look for the minimum and return the negative diff image, because it needs 
        ## to keep the background images on the left hand side of the subtraction
        if type(bgStack) is list:
            ## following line of code compresses logic of commented code:
            # diffStack = np.zeros(bgStack[0].shape, dtype=bgStack[0].dtype)
            # for i in range(len(bgStack)):
            #     diffStack += bgStack[i] - img[:,:,i].flatten()        
            # diffImg = np.min(diffStack, axis=0).reshape((img.shape[0], img.shape[1]))        
            diffImg = np.min((bgStack[0] - img[:,:,0].flatten()) +  
                            (bgStack[1] - img[:,:,1].flatten()) + 
                            (bgStack[2] - img[:,:,2].flatten()),
                            axis=0).reshape((img.shape[0], img.shape[1]))
        else:
            diffImg = np.min(bgStack - img.flatten(), axis=0).reshape(img.shape)
        
        return -diffImg

    @staticmethod
    def backgroundSubtractionWeaver(img, bgStack, test=False):
        """
            background subtraction using C++ code works on non-fortran style 
            background stacks, is less efficient than 
            backgroundSubtractionWeaverF
            
            Input:
                img         nd array                input image
                
                bgStack     stack of background  (see calculateBackgroundStack()
                            images                for computation)
                            !! needs to generated with fortranStyle=False !!
                            
                test        bool                    if result should get 
                                                    compared to the output of
                                                    backgroundSubstractionStack
                            
            Output:
                difference image
        """
        im0 = img[:,:,0].flatten()
        im1 = img[:,:,1].flatten()
        im2 = img[:,:,2].flatten()
        
        bg0 = bgStack[0]
        bg1 = bgStack[1]
        bg2 = bgStack[2]    
        
        # (very wide string)
        subtractionCode = \
        """
            // subtraction on all color layers 
            short val = 0;
            for (int i = 0; i < bgn; ++i){
                for (int k = 0; k < bgx; k += 16){
                    diff[k] = ((im0[k] - bg0[k + i * imLen]) + (im1[k] - bg1[k + i * imLen]) + (im2[k] - bg2[k + i * imLen]) > diff[k]) ? (im0[k] - bg0[k + i * imLen]) + (im1[k] - bg1[k + i * imLen]) + (im2[k] - bg2[k + i * imLen]) : diff[k];
                    diff[k + 1] = ((im0[k + 1] - bg0[k + 1 + i * imLen]) + (im1[k + 1] - bg1[k + 1 + i * imLen]) + (im2[k + 1] - bg2[k + 1 + i * imLen]) > diff[k + 1]) ? (im0[k + 1] - bg0[k + 1 + i * imLen]) + (im1[k + 1] - bg1[k + 1 + i * imLen]) + (im2[k + 1] - bg2[k + 1 + i * imLen]) : diff[k + 1];
                    diff[k +2] = ((im0[k +2] - bg0[k +2 + i * imLen]) + (im1[k +2] - bg1[k +2 + i * imLen]) + (im2[k +2] - bg2[k +2 + i * imLen]) > diff[k +2]) ? (im0[k +2] - bg0[k +2 + i * imLen]) + (im1[k +2] - bg1[k +2 + i * imLen]) + (im2[k +2] - bg2[k +2 + i * imLen]) : diff[k +2];
                    diff[k + 3] = ((im0[k + 3] - bg0[k + 3 + i * imLen]) + (im1[k + 3] - bg1[k + 3 + i * imLen]) + (im2[k + 3] - bg2[k + 3 + i * imLen]) > diff[k + 3]) ? (im0[k + 3] - bg0[k + 3 + i * imLen]) + (im1[k + 3] - bg1[k + 3 + i * imLen]) + (im2[k + 3] - bg2[k + 3 + i * imLen]) : diff[k + 3];
                    diff[k + 4] = ((im0[k + 4] - bg0[k + 4 + i * imLen]) + (im1[k + 4] - bg1[k + 4 + i * imLen]) + (im2[k + 4] - bg2[k + 4 + i * imLen]) > diff[k + 4]) ? (im0[k + 4] - bg0[k + 4 + i * imLen]) + (im1[k + 4] - bg1[k + 4 + i * imLen]) + (im2[k + 4] - bg2[k + 4 + i * imLen]) : diff[k + 4];
                    diff[k + 5] = ((im0[k + 5] - bg0[k + 5 + i * imLen]) + (im1[k + 5] - bg1[k + 5 + i * imLen]) + (im2[k + 5] - bg2[k + 5 + i * imLen]) > diff[k + 5]) ? (im0[k + 5] - bg0[k + 5 + i * imLen]) + (im1[k + 5] - bg1[k + 5 + i * imLen]) + (im2[k + 5] - bg2[k + 5 + i * imLen]) : diff[k + 5];
                    diff[k + 6] = ((im0[k + 6] - bg0[k + 6 + i * imLen]) + (im1[k + 6] - bg1[k + 6 + i * imLen]) + (im2[k + 6] - bg2[k + 6 + i * imLen]) > diff[k + 6]) ? (im0[k + 6] - bg0[k + 6 + i * imLen]) + (im1[k + 6] - bg1[k + 6 + i * imLen]) + (im2[k + 6] - bg2[k + 6 + i * imLen]) : diff[k + 6];
                    diff[k + 7] = ((im0[k + 7] - bg0[k + 7 + i * imLen]) + (im1[k + 7] - bg1[k + 7 + i * imLen]) + (im2[k + 7] - bg2[k + 7 + i * imLen]) > diff[k + 7]) ? (im0[k + 7] - bg0[k + 7 + i * imLen]) + (im1[k + 7] - bg1[k + 7 + i * imLen]) + (im2[k + 7] - bg2[k + 7 + i * imLen]) : diff[k + 7];
                    diff[k + 8] = ((im0[k + 8] - bg0[k + 8 + i * imLen]) + (im1[k + 8] - bg1[k + 8 + i * imLen]) + (im2[k + 8] - bg2[k + 8 + i * imLen]) > diff[k + 8]) ? (im0[k + 8] - bg0[k + 8 + i * imLen]) + (im1[k + 8] - bg1[k + 8 + i * imLen]) + (im2[k + 8] - bg2[k + 8 + i * imLen]) : diff[k + 8];
                    diff[k + 9] = ((im0[k + 9] - bg0[k + 9 + i * imLen]) + (im1[k + 9] - bg1[k + 9 + i * imLen]) + (im2[k + 9] - bg2[k + 9 + i * imLen]) > diff[k + 9]) ? (im0[k + 9] - bg0[k + 9 + i * imLen]) + (im1[k + 9] - bg1[k + 9 + i * imLen]) + (im2[k + 9] - bg2[k + 9 + i * imLen]) : diff[k + 9];
                    diff[k + 10] = ((im0[k + 10] - bg0[k + 10 + i * imLen]) + (im1[k + 10] - bg1[k + 10 + i * imLen]) + (im2[k + 10] - bg2[k + 10 + i * imLen]) > diff[k + 10]) ? (im0[k + 10] - bg0[k + 10 + i * imLen]) + (im1[k + 10] - bg1[k + 10 + i * imLen]) + (im2[k + 10] - bg2[k + 10 + i * imLen]) : diff[k + 10];
                    diff[k + 11] = ((im0[k + 11] - bg0[k + 11 + i * imLen]) + (im1[k + 11] - bg1[k + 11 + i * imLen]) + (im2[k + 11] - bg2[k + 11 + i * imLen]) > diff[k + 11]) ? (im0[k + 11] - bg0[k + 11 + i * imLen]) + (im1[k + 11] - bg1[k + 11 + i * imLen]) + (im2[k + 11] - bg2[k + 11 + i * imLen]) : diff[k + 11];
                    diff[k + 12] = ((im0[k + 12] - bg0[k + 12 + i * imLen]) + (im1[k + 12] - bg1[k + 12 + i * imLen]) + (im2[k + 12] - bg2[k + 12 + i * imLen]) > diff[k + 12]) ? (im0[k + 12] - bg0[k + 12 + i * imLen]) + (im1[k + 12] - bg1[k + 12 + i * imLen]) + (im2[k + 12] - bg2[k + 12 + i * imLen]) : diff[k + 12];
                    diff[k + 13] = ((im0[k + 13] - bg0[k + 13 + i * imLen]) + (im1[k + 13] - bg1[k + 13 + i * imLen]) + (im2[k + 13] - bg2[k + 13 + i * imLen]) > diff[k + 13]) ? (im0[k + 13] - bg0[k + 13 + i * imLen]) + (im1[k + 13] - bg1[k + 13 + i * imLen]) + (im2[k + 13] - bg2[k + 13 + i * imLen]) : diff[k + 13];
                    diff[k + 14] = ((im0[k + 14] - bg0[k + 14 + i * imLen]) + (im1[k + 14] - bg1[k + 14 + i * imLen]) + (im2[k + 14] - bg2[k + 14 + i * imLen]) > diff[k + 14]) ? (im0[k + 14] - bg0[k + 14 + i * imLen]) + (im1[k + 14] - bg1[k + 14 + i * imLen]) + (im2[k + 14] - bg2[k + 14 + i * imLen]) : diff[k + 14];
                    diff[k + 15] = ((im0[k + 15] - bg0[k + 15 + i * imLen]) + (im1[k + 15] - bg1[k + 15 + i * imLen]) + (im2[k + 15] - bg2[k + 15 + i * imLen]) > diff[k + 15]) ? (im0[k + 15] - bg0[k + 15 + i * imLen]) + (im1[k + 15] - bg1[k + 15 + i * imLen]) + (im2[k + 15] - bg2[k + 15 + i * imLen]) : diff[k + 15];
                }
            }
        """
        diff = np.ones((img.shape[0], img.shape[1]), dtype=bgStack[0].dtype) * \
                                                np.iinfo(bgStack[0].dtype).min
        imLen = img.shape[0] * img.shape[1]
        bgn = bg0.shape[0]
        bgx = bg1.shape[1]
        weave.inline(subtractionCode, 
                                ['diff', 'bg0', 'bg1', 'bg2', 'im0',
                                 'im1', 'im2', 'imLen', 'bgn', 'bgx'],
                                 extra_compile_args=['-march=corei7', 
                                                     '-O3', '-fopenmp'], 
                                 headers=['<omp.h>'],
                                 extra_link_args=['-lgomp'], 
                                 compiler='gcc')
        
        if test:
            print 'Difference: ', np.sum(np.abs(self.backgroundSubstractionStack(img,bgStack) - diff).flatten())

        return diff
    
    @staticmethod
    def backgroundSubtractionWeaverF(img, bgStackF, test=False, vSkip = 3, hSkip = 3):
        """
            background subtraction using C++ code works on _fortran style_ 
            background stacks, 
            
            IS THE FASTEST APPROACH SO FAR
            
            Input:
                img         nd array                input image
                
                bgStackF    stack of background  (see calculateBackgroundStack()
                            images                for computation)
                            !! needs to generated with fortranStyle=True !!
                            
                test        bool                    if result should get 
                                                    compared to the output of
                                                    backgroundSubstractionStack
                            
            Output:
        """
                
        im0 = img[:,:,0].flatten()
        im1 = img[:,:,1].flatten()
        im2 = img[:,:,2].flatten()
        
        bg0 = bgStackF[0]
        bg1 = bgStackF[1]
        bg2 = bgStackF[2]
        
        subtractionCode = \
        """
        // subtraction on all color layers 
        short val = 0;
        short val2 = 0;
        int shifts = Nbg0[1];
        """
        subtractionCode += \
        "for (int k = 0; k < Nbg0[0]; k+={0}){{".format(hSkip+1)
        subtractionCode += \
        """
            if (k % 1920 == 0){
        """
        subtractionCode += \
                "k += 1920 * {0};".format(vSkip+1)
        subtractionCode += \
        """
            }
            int pos = k * shifts;
            short img0 = im0[k];
            short img1 = im1[k];
            short img2 = im2[k];

            val = (img0 - bg0[pos]) + (img1 - bg1[pos]) + (img2 - bg2[pos]); 
        """
        for i in range(bg0.shape[1]):
            subtractionCode +=\
        """
            pos++;
            val2 = (img0 - bg0[pos]) + (img1 - bg1[pos]) + (img2 - bg2[pos]);                
            if (val2 > val){
                val = val2;
            }
        """
        subtractionCode += \
        """
            diff[k] = val;
        }
        """
        diff = np.zeros((img.shape[0], img.shape[1]), dtype=bgStackF[0].dtype)
        weave.inline(subtractionCode, 
                    ['diff', 'bg0', 'bg1', 'bg2', 'im0', 'im1', 'im2'], 
                    extra_compile_args=['-march=corei7', '-O3', '-fopenmp'],
                    headers=['<omp.h>'],
                    extra_link_args=['-lgomp'], 
                    compiler='gcc')

            
        if test:
            print 'Difference: ', np.sum(np.abs(backgroundSubstractionStack(img,bgStack) - diff).flatten())

        return diff

    
    def testStackProcessing(self, img):
        from time import time
    
        print "start benchmarking stack approaches, be patient..."   
        
        sumT = 0
        for i in range(10):
            t = time()
            diffImgNaive = self.backgroundSubtractionShiftsNaive(img, self)
            sumT += time() - t
        print 'naive implementation of background subtraction using shifts', sumT / i

        sumT = 0
        bgFunc = self.backgroundSubtractionStack
        self.configureStackSubtraction(bgFunc)
        # make sure it is comiled
        diffImgFast = self.subtractStack(img)
        for i in range(10):
            t = time()
            diffImgFast = self.subtractStack(img)
            sumT += time() - t
        print 'execution of precomputed background subtraction using numpy', sumT / i

        sumT = 0
        bgFunc = self.backgroundSubtractionWeaver
        self.configureStackSubtraction(bgFunc)
        # make sure it is comiled
        diffImgFaster = self.subtractStack(img)
        for i in range(10):
            t = time()
            diffImgFaster = self.subtractStack(img)
            sumT += time() - t
        print 'execution of precomputed background subtraction using C++', sumT / i

        sumT = 0
        bgFunc = self.backgroundSubtractionWeaverF
        self.configureStackSubtraction(bgFunc)     
        # make sure it is comiled
        diffImgFastest = self.subtractStack(img)       
        for i in range(10):
            t = time()
            diffImgFastest = self.subtractStack(img)
            sumT += time() - t
        print 'execution of precomputed background subtraction using C++ and transpose', sumT / i

        sumT = 0
        for i in range(10):
            t = time()
            diffImgSimple = img - self
            sumT += time() - t
        print 'single background substraction takes', sumT / i

        sumT = 0
        for i in range(10):
            t = time()
            diffImgSum = np.sum(img - self, axis=2)
            sumT += time() - t
        print 'single background substraction summed at axis=2', sumT / i

        print 'Difference in the result of backgroundSubstractionStack and naive shift implementation', np.sum(np.abs((diffImgNaive - diffImgFast).flatten()))
        print 'Difference in the result of backgroundSubtractionWeaver and naive shift implementation', np.sum(np.abs((diffImgNaive - diffImgFaster).flatten()))
        print 'Difference in the result of backgroundSubtractionWeaverF and naive shift implementation', np.sum(np.abs((diffImgNaive - diffImgFastest).flatten()))
        
        return [diffImgNaive, diffImgFast, diffImgFaster, diffImgFastest]
    
    
        
        
            
if __name__ == "__main__":
    from skimage import data
    import pylab as plt
    from skimage.color import rgb2gray
    
    lena = data.lena()
    grayLena = rgb2gray(lena)
    
    ## rgb version
    bgImg = backgroundImage(lena)    
    diff = bgImg.subtractImg(lena, 0, 0)    
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    ## gray version
    ## make sure
    shift = [-10,  -5]
    bgImg = backgroundImage(grayLena)
    diff = bgImg.subtractImg(grayLena, *shift)    
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    ## subtraction with padded border
    shift = [-10,  -5]
    bgImg = backgroundImage(grayLena)
    diff = bgImg.subtractImgPadding(grayLena, shift)    
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    
    ### manual version ###
    ## using padded shift function
    diff = np.subtract(*backgroundImage.alignImgPairPadding(shift, 
                                                            grayLena, grayLena)) 
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    ## display image in valid range
    shiftList = []
    shiftList.append(shift)
    shiftList.append([10,  5])
    rngX,  rngY = backgroundImage.getValidSlices(shiftList, grayLena.shape)
        
    plt.figure(figsize=(10, 10))
    plt.imshow(diff[rngX,  rngY])
    plt.show()
    
    ## overloaded - operator
    diff1 = grayLena - bgImg
    diff2 = bgImg - grayLena
    
    print 'Difference in the result of right and lefthand subtraction: ',np.sum(np.abs((diff2 - diff1).flatten()))
                                    
    ## perform benchmark of different background subtraction methods using
    ## the stack approach
    
    import sys
    sys.path.append('/home/peter/code/pyTools/')

    import numpy as np
    from pyTools.system.videoExplorer import *
    from pyTools.videoProc.backgroundModel import *
    from pyTools.imgProc.imgViewer import *
    from pyTools.batch.vials import *
    from time import time


    vE = videoExplorer()
    bgModel = backgroundModel(verbose=True, colorMode='rgb')
    viewer = imgViewer()
    roi = [[350, 660], [661, 960], [971, 1260], [1270, 1600]]
    vial = Vials(roi)
    
    import datetime as dt    
    start = dt.datetime(2013, 02, 19)
    end = dt.datetime(2013, 02, 21)
    rootPath = "/run/media/peter/Elements/peter/data/"
    vE.setTimeRange(start, end)
    vE.setRootPath(rootPath)
    vE.parseFiles()

    bgModel.getVideoPaths(rootPath, start,  end)
    bgModel.createNightModel(sampleSize=10)

    testImg = img, fileName = vE.getRandomFrame(vE.getPathsOfList(vE.nightList), info=True, frameMode='RGB')
    
    bgModel.modelNight.testStackProcessing(testImg[0])
    
    
    print "finished backgroundImage example"   
    
