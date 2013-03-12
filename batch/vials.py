import numpy as np
from pyTools.imgProc.imgViewer import *
import matplotlib.pyplot as plt

class Vials(object):
    def __init__(self,  rois=None):
        """
            INPUT:
                rois    2D-list of int      list of x begining and ends of
                                            region of interests for each vial
        """
        self.rois = rois
        self.iV = imgViewer()
        
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
            
    def plotVialMin(self,  diff,  windowSize=[60, 60]):
        #figure, border = plt.subplots()
        figure = plt.figure(figsize=(11,7))
        for i in range(len(self.rois)):
            
            vial = self.rois[i]
            vDiff = diff[:, vial[0]:vial[1]]
                        
            diffMin = np.unravel_index(np.argmin(vDiff), vDiff.shape)
            fig = self.iV.showPatch(vDiff, np.asarray(diffMin), windowSize, 2, 
                            fig=figure,  offsetX=0.4 * i)
        
        #border.axis('off')
        ax = figure.add_axes([0.4 * (i+1), 0.3, 0.2, -0.02])
        ax.axis('off')
        plt.show()
        plt.draw()
    
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


if __name__ == "__main__":
    from skimage import data
    lena = data.lena()
    
    v = Vials()
    
    v1 = {  'roi':[0, 100], 'patch':lena[10:20, 10:20], 
            'patchSize':[10, 10],  'center':[15, 15]}
    v2 = {  'roi':[150, 250], 'patch':lena[10:40, 50:150], 
            'patchSize':[10, 10],  'center':[15, 15]}
    
    v.plotVialWithPatch(lena, [v1, v2])
