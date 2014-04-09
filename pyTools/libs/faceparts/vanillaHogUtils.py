###
# Imports
###

import numpy as np
import skimage as img
import skimage.color as clr
from pylab import *
from skimage.filter import canny
from scipy.ndimage.measurements import label
#####

"""vanillaHogUtils.py
   A Python implementation of a very basic Histogram of Oriented Gradients
   extractor. This code is released as-is, with no warranty of any kind, under the
   GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""


# Function that returns the Histogram of Oriented Gradient vector
# given an input image and parameters.
def hog(img, bins, num_spatial_bins, max_angle, roi):
    """ hog(img, bins, num_spatial_bins, max_angle, roi)
        inputs:    img - a grayscale image stored in a NumPy array
                   bins - number of angular bins to use.
                   num_spatial_bins - number of spatial bins to use in each direction
                   max_angle - maxium angle for histogram calculation, either 180 or 360
                   roi - List of ytop, ybottom, xleft, xright describing the bounding box
                         of the region of interest for HoG to be computed in.
    """
    # Initialize
    hog_vector = np.zeros(bins*num_spatial_bins**2)
    
    image = img[roi[0]:roi[1],roi[2]:roi[3]]
    height,width = image.shape
    hist_indx = np.zeros((height,width)).astype(np.int32)
    angle_step = max_angle/bins
    
    # Compute gradients
    dx,dy = np.gradient(image)
    grad_mag = np.sqrt(dx**2 + dy**2)
    
    # Compute gradient angles
    if max_angle == 180:
        A = (np.arctan(np.divide(dy,dx+0.0001) + np.pi/2.0)*180)/np.pi
    if max_angle == 360:
        A = (np.arctan2(dy,dx)+np.pi)*180/np.pi
    
    # Each pixel is assigned a spatial bin index    
    for ii in range(height):
        for jj in range(width):
            
            for h_indx in range(num_spatial_bins):
                if jj >= h_indx*width/num_spatial_bins and jj < (h_indx+1)*width/num_spatial_bins:
                    for v_indx in range(num_spatial_bins):
                        if ii >= v_indx*height/num_spatial_bins and ii < (v_indx+1)*height/num_spatial_bins:
                            hist_indx[ii,jj] = h_indx + num_spatial_bins*v_indx
                            break
                    break
                            
    # Each pixel is assigned an angle bin index and then the gradient magnitude is
    # added to the appropriate place is the HoG vector, which depends on the hist index
    # and the bin index.
    for ii in range(height):
        for jj in range(width):
            angle_val = A[ii,jj]
            angle1 = 0.0;
            min_dist = abs(angle_val - angle1)
            bin_indx = 0
    
            for kk in range(bins):
                angle1 = angle1 + angle_step
                this_dist = abs(angle_val - angle1)
                if this_dist < min_dist:
                    min_dist = this_dist
                    bin_indx = kk
                         
            # The linear index here is the spatial bin multiplied by bin size plus the number that the current angle bin
            # is. This of it like a 2D array that is bins*num_spatial_bins wide and num_spatial_bins tall.
            hog_vector[bins*hist_indx[ii,jj] + bin_indx] = hog_vector[bins*hist_indx[ii,jj] + bin_indx] + grad_mag[ii,jj]
    
    return hog_vector/np.sum(hog_vector)

###
# hogDemo -- A function to execute a test case of the pHoG descriptor with
#    test parameters and print the output pHoG vector.
###
def hogDemo():
    """ hogDemo -- A function to execute a test case of the HoG descriptor with
        test parameters and print the output pHoG vector. No inputs or outputs.
    """
    # You need to point this as an image on your machine for testing.
    I = "/home/peter/code/pyTools/libs/faceparts/demo_big.png"
    img = imread(I)
    if len(img.shape) == 3:
        img = clr.rgb2gray(img)
    
    bins = 9; max_angle = 180
    num_spatial_bins = 3
    roi = [1, 130, 1, 200]
    
    p = hog(img, bins, num_spatial_bins, max_angle, roi)
    print p
    print len(p)
# END phogDemo
                
                
##
# Testing
###
if __name__=="__main__":
    # Run the demo for a test.
    hogDemo()
    