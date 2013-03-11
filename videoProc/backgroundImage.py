import numpy as np

class backgroundImage(object):
    def __init__(self, img):
        self.setImage(img)
        
    def setImage(self, img):
        if img.dtype.kind in ('u',  'i'):
            self.bgImg = np.int32(img)
        else:
            self.bgImg = img
            
    def __sub__(self,  other):
        return self.substractImg(other)
        
    def __rsub__(self,  other):
        return self.substractImg(other)    
        
    def substractImg(self, img, offsetX=0, offsetY=0):
        diff = np.subtract(*self.alignImgPair([offsetX,  offsetY], 
                                              img, 
                                              self.bgImg))
        
        if len(diff.shape) == 3:
            return np.sum(diff, axis=2)
        else:
            return diff            
    
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
            
if __name__ == "__main__":
    from skimage import data
    import pylab as plt
    from skimage.color import rgb2gray
    
    lena = data.lena()
    
    ## rgb version
    bgImg = backgroundImage(lena)    
    diff = bgImg.substractImg(lena, 0, 0)    
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    ## gray version
    ## make sure
    grayLena = rgb2gray(lena)
    bgImg = backgroundImage(grayLena)
    diff = bgImg.substractImg(grayLena, -1, 0)    
    plt.figure(figsize=(10, 10))
    plt.imshow(diff)
    plt.show()
    
    ## overloaded - operator
    diff1 = grayLena - bgImg
    diff2 = bgImg - grayLena
    
    print not np.any(((diff == diff1) == diff2) != True)
    
    
