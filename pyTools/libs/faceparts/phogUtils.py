###
# Imports
###

import numpy as np
import scikits.image as img
import scikits.image.color as clr
from mahotas import imread
from scikits.image.filter import canny
from scipy.ndimage.measurements import label
#####

"""phogUtils.py
   A Python implementation of the Pyramidal Histogram of Oriented Gradients code
   that is provided by Anna Bosch and Andrew Zisserman at this link:
   < http://www.robots.ox.ac.uk/~vgg/research/caltech/phog.html >. This code is 
   released as-is, with no warranty of any kind, under the GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""


###
# Functions
###

###
# binMatrix -- Computes two arrays that are the same size as the input.
#    The first stores the angle-bin that pixel (i,j) belongs to and
#    and the second stores the gradient magnitude at (i,j).
###
def binMatrix(A,E,G,angle,bin):
    """ binMatrix -- Computes two arrays that are the same size as the input.
        The first stores the angle-bin that pixel (i,j) belongs to and
        and the second stores the gradient at (i,j).
        
        inputs:    A -- matrix containing angle values
                   E -- edge image
                   G -- matrix containing the gradient values
                   bin -- number of bins in the histogram
                   angle -- 180 or 360, depending on whether 
                            histogram is over half circle or whole circle.
                            
        outputs:   bm -- Matrix with histogram bin indices stored into each pixel (i,j)
                            where the bin is based on the angle.
                   bv -- Matrix with gradient values, essentially the magnitude that will
                            be added into the bin whose number appears in bm[i,j].
    """
    
    struct = np.ones((3,3))
    segments, n = label(E,structure=struct)
    
    X = E.shape[1]
    Y = E.shape[0]
    
    bm = np.zeros((Y,X))
    bv = np.zeros((Y,X))
    nAngle = angle/bin
    
    for i in range(n):
        pos = np.argwhere(segments==i)
        posX = [elem[1] for elem in pos]
        posY = [elem[0] for elem in pos]
        
        for j in range(len(posY)):
            pos_x = posX[j]
            pos_y = posY[j]
        
        
            b = np.ceil(A[pos_y,pos_x]/nAngle)
            if b == 0:
                bin = 1
            if G[pos_y,pos_x] > 0:
                bm[pos_y,pos_x] = b
                bv[pos_y,pos_x] = G[pos_y,pos_x]
                  
    return bm, bv
# END binMatrix

###
# phogDescriptor -- Formats histogram data into pyramid HoG descriptor. The algorithm
#    works by populating `bin` number of histogram components for each subwindow of the
#    image at level l, where l ranges over 1 to L. For l = 1, the whole original image
#    region is used. When l=2, a 2x2 grid of subwindows is imposed on the image region 
#    and `bin` number of histogram components are stored for each subwindow.
###
def phogDescriptor(bh,bv,L,bin):
    """ phogDescriptor -- Formats histogram data into pyramid HoG descriptor. The algorithm
        works by populating `bin` number of histogram components for each subwindow of the
        image at level l, where l ranges over 1 to L. For l = 1, the whole original image
        region is used. When l=2, a 2x2 grid of subwindows is imposed on the image region 
        and `bin` number of histogram components are stored for each subwindow.
        
        inputs:    bh -- Matrix where each pixel gives the index of the angle-bin of
                            of the histogram that that pixel belongs to.
                   bm -- Matrix where each pixels gives the gradient magnitude, i.e.
                            the magnitude that gets stored into the histogram.
                   L -- Number of levels in the pyramid.
                   bin -- Number of bins to use for each subwindow histogram.
                   
        outputs:   p -- A long vector containing the concatenated pHoG descriptor.
    """
    p = []
    for b in range(bin):
        p.append(np.sum(bv[bh==b]))

    cella = 1
    for l in range(1,L):
        x = np.fix(bh.shape[1]/2.0**l)
        y = np.fix(bh.shape[0]/2.0**l)
        
        xx = 0; yy = 0;
        
        while xx+x <= bh.shape[1]:
            while yy+y <= bh.shape[0]:
                bh_cella = []
                bv_cella = []
                
                bh_cella = bh[yy:yy+y,xx:xx+x]
                bv_cella = bv[yy:yy+y,xx:xx+x]
                
                for b in range(bin):
                    p.append(np.sum(bv_cella[bh_cella==b]))
                yy = yy + y
                
            cella = cella+1
            yy = 0
            xx = xx + x
    if np.sum(p):
        p = p/np.sum(p)
        
    return p
# END phogDescriptor 
            
###
# phog -- Function that prepares data structures and histogram indexing and then
#    calls other functions to execute the pryamidal histogram of gradient code.
###
def phog(image, bin, angle, L, roi):
    """ phog -- Function that prepares data structures and histogram indexing and then
        calls other functions to execute the pryamidal histogram of gradient code.
        
        inputs: image -- String that names the file path to the image to compute on.
                bin -- Number of components to use for each subwindow histogram
                angle -- 180 or 360 if you want half-circle or whole-circle angles, respectively.
                L -- Number of pyramid levels to use.
                roi -- List with 4 entries, [top_y, bottom_y, left_x, right_x], that bounds the
                       image region for which you want to compute the HoG feature.
                       
        outputs: p -- A long vector that contains the pHoG descriptor.
    """
    Img = imread(image)
    if len(Img.shape) == 3:
        G = clr.rgb2gray(Img)
    else:
        G = Img
    
    if np.sum(G) > 100:
        E = canny(G)
        GradientX, GradientY = np.gradient(np.double(G))
        
        Gr = np.sqrt(GradientX**2 + GradientY**2)
        GradientX[GradientX==0] = 1*10**(-5)
        
        YX = np.divide(GradientY,GradientX)
        if angle == 180:
            A = (np.arctan(YX + np.pi/2.0)*180)/np.pi
        if angle == 360:
            A = (np.arctan2(GradientY,GradientX)+np.pi)*180/np.pi
        
        # Function call
        bh, bv = binMatrix(A,E,Gr,angle,bin)
        
    else:
        bh = np.zeros((G.shape[0],G.shape[1]))
        bv = np.zeros((G.shape[0],G.shape[1]))
        
    bh_roi = bh[roi[0]:roi[1], roi[2]:roi[3]]
    bv_roi = bv[roi[0]:roi[1], roi[2]:roi[3]]
    
    # Function call to actually extract the HoG vector.
    p = phogDescriptor(bh_roi,bv_roi,L,bin)
    
    return p
# END phog

###
# phogDemo -- A function to execute a test case of the pHoG descriptor with
#    test parameters and print the output pHoG vector.
###
def phogDemo():
    """ phogDemo -- A function to execute a test case of the pHoG descriptor with
        test parameters and print the output pHoG vector. No inputs or outputs.
    """
    # You need to point this at an image on your machine for testing.
    I = "/home/ely/Software/vision/phog/image_0058.jpg"
    bin = 8
    angle = 360
    L = 3
    roi = [1, 130, 1, 200]
    p = phog(I,bin,angle,L,roi)
    print p
    print len(p)
# END phogDemo

###
# Testing
###
if __name__=="__main__":
    # Run the demo for a test.
    phogDemo()
