import numpy as np

class backgroundImage(np.ndarray):
    __array_priority__ = 100
    
    def __new__(cls,  img):
        obj = np.asarray(img).view(cls)
        obj.shiftList = []
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
        self.shiftList.append(shift)
        diff = np.subtract(*self.alignImgPairPadding(shift, img, self))
        
        if len(diff.shape) == 3:
            return np.sum(diff, axis=2)
        else:
            return diff 
        
    def getValidROI(self,  reset=False):
        ret = self.getValidSlices(self.shiftList, self.shape)
        if reset:
            self.resetShiftList()
        return ret
    
    @staticmethod
    def alignImgPair(shift, img, bg):      
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
    
    print "finished backgroundImage example"   
    
