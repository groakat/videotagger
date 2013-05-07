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
        xy = np.round(copy(center))
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


if __name__ == "__main__":
    from skimage import data
    lena = data.lena()
    
    imView = imgViewer()
    
    imView.show(lena)
    
    imView.showPatch(lena, [200, 50], [50, 50], 2)
    plt.show()
