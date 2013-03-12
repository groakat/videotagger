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
        self.img = plt.imshow(img, interpolation='nearest')
        self.fig = plt.gcf()
        self.ax = plt.gca()
        
        self.handler = EventHandler(self)        
        plt.show()     
        
        
    def showPatch(self, img, center, patchSize, patch_zoom=0.2, offsetX=0, offsetY=0.5, fig=None, no=0, patch=None):
        if fig == None:
            fig, tmp = subplots()
            
        ## create artifical border around the image to display 
        ## patchbox uncroped inline
        #border = fig.add_axes([0 + offsetX, 0 + offsetY, 1, 2.0])
        #border.axis('off')
        
        ## axis for image
        ax = fig.add_axes([offsetX,offsetY, 0.5, 1])
        
        im = ax.imshow(img)
        ax.axis('off')
        
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
        if patch == None:
            if xy[0] < 0:
                xy[0] = 0
            if xy[1] < 0:
                xy[1] = 0
                
            h = xy[1]+patchSize[1]
            if  h > img.shape[0]:
                h = img.shape[0]
                
            w = xy[0]+patchSize[0]
            if  w > img.shape[1]:
                w = img.shape[1]
                    
            patch = img[xy[1]:h, xy[0]:w]

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


if __name__ == "__main__":
    from skimage import data
    lena = data.lena()
    
    imView = imgViewer()
    
    imView.show(lena)
    imView.showPatch(lena, [200, 50], [50, 50], 2)
