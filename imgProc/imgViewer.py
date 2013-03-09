"""
    interactive image viewer
    
    based on answer on
    http://stackoverflow.com/questions/5836560/color-values-in-imshow-for-matplotlib
"""
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.image as mpimg

class imgViewer(object):
    def show(self,  img):
        self.img = plt.imshow(img, interpolation='nearest')
        self.fig = plt.gcf()
        self.ax = plt.gca()
        
        self.handler = EventHandler(self)        
        plt.show()     

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
    img = mpimg.imread('stinkbug.png')
    
#    img = np.random.rand(10,10)*255
    
    imView = imgViewer()
    
    imView.show(img)
