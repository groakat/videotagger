# Import the PyCUDA modules and initialize the CUDA device
import pycuda.autoinit
import pycuda.driver as cu
import pycuda.compiler as nvcc

import png, phogUtils as phog
import vanillaHogUtils as vhog
import numpy as np
import scikits.image as img
import scikits.image.color as clr
import cPickle as pickle
from scikits.learn import svm
from scikits.learn.externals import joblib
from mahotas import imread
import pylab as pyl
import KernelSource
import os, time, random, geometry
#####

"""timing.py
   Simple Python script to test the timing of the CPU Histogram
   of Gradient functions vs. GPU kernels for the same functions. 
   
   This file assumes the existence of the test images listed after
   the GPU kernel compilations. These should have been included
   in the download. Check back at
   < http://people.seas.harvard.edu/~ely/faceparts/index.html >
   for missing files.
   
   This code is released as-is, with no warranty of any kind, under the
   GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""

#####
# CUDA kernels
#####

###
# Keypoint-based HoG kernel 
###
keypoint_hog_kernel_source = KernelSource.keypoint_hog_kernel_source_code()
keypoint_hog_kernel_source_module = nvcc.SourceModule( keypoint_hog_kernel_source)
keypoint_hog_kernel = keypoint_hog_kernel_source_module.get_function( "keypoint_hog_kernel" )

###
# Patch-based HoG kernel
###
patch_hog_kernel_source = KernelSource.patch_hog_kernel_source_code()
patch_hog_kernel_source_module = nvcc.SourceModule( patch_hog_kernel_source)
patch_hog_kernel = patch_hog_kernel_source_module.get_function( "patch_hog_kernel" )
##########


# Make test images of increasing size
img_prefix = "/home/ely/projects/faces/src/demo_"
img_names = ["medium.jpg", "large.jpg", "big.jpg", "huge.jpg", "mega.jpg"]
img_sizes = [64, 128, 256, 512, 1024]

# Set HoG parameters, number of bins, maximum angle, and number of pyramid levels
bins = 9; angle = 180; L = 3; num_spatial_bins = 3;
phog_times = []; vhog_times = []; triggs_times = [];
gpu_keypoint_times = []; gpu_patch_times = [];
num_plots = 5

# Get timing info for each of the patch-based CPU versions
print "Timing the CPU versions ..."
for indx in range(len(img_sizes)):
    cur_image = imread(img_prefix+img_names[indx])
    if len(cur_image.shape) == 3:
        cur_image = clr.rgb2gray(cur_image)
    height, width = cur_image.shape
    
    st_time = time.time()
    p = phog.phog(img_prefix+img_names[indx], bins, angle, L, [0,height,0,width])
    ed_time = time.time() - st_time
    phog_times.append(ed_time)
    
    st_time = time.time()
    v = vhog.hog(cur_image, bins, num_spatial_bins, angle, [0,height,0,width])
    ed_time = time.time() - st_time
    vhog_times.append(ed_time)
    
    
# Get timing info for the Dalal and Triggs CPU C-code version.
# For this, only use the huge demo image and increase the size of the
# window around a single keypoint in the middle of the image.
im_size = 512
keypoint_file = open("tmp.kps",'w')
feat_x = np.floor(im_size/2)
feat_y = np.floor(im_size/2)
                   
keypoint_file.write("%d %d \n"%(feat_x,feat_y))
keypoint_file.close()


# Time the GPU kernels and save the output.
print "Timing the GPU version ..."
for indx in range(len(img_sizes)):
    cur_image = imread(img_prefix+img_names[indx])
    if len(cur_image.shape) == 3:
        cur_image = clr.rgb2gray(cur_image)
    height, width = cur_image.shape
    
    t_image = np.copy(cur_image).ravel().astype(np.float32)
    x_gradient = np.zeros((height,width)).ravel().astype(np.float32)
    y_gradient = np.zeros((height,width)).ravel().astype(np.float32)
    gradient_mag = np.zeros((height,width)).ravel().astype(np.float32)
    angles = np.zeros((height,width)).ravel().astype(np.float32)
    hog_output = np.zeros((height,width)).ravel().astype(np.float32)


    # Number of threads per block
    n_TPB_x = int(16)
    n_TPB_y = int(16)

    # Number of thread blocks
    n_blocks_x = int(np.ceil(width/n_TPB_x))
    n_blocks_y = int(np.ceil(height/n_TPB_y))


    ###
    # Patch-based HoG kernel
    ###    
    
    # Start the timer
    gpu_start_time = cu.Event(); gpu_end_time = cu.Event(); gpu_start_time.record()
    
    # Create device variables
    input_im_device = cu.mem_alloc(t_image.nbytes)
    cu.memcpy_htod( input_im_device, t_image )


    x_gradient_device = cu.mem_alloc(x_gradient.nbytes)
    cu.memcpy_htod( x_gradient_device, x_gradient )

    y_gradient_device = cu.mem_alloc(y_gradient.nbytes)
    cu.memcpy_htod( y_gradient_device,  y_gradient )

    gradient_mag_device = cu.mem_alloc(gradient_mag.nbytes)
    cu.memcpy_htod( gradient_mag_device,  gradient_mag )

    angles_device = cu.mem_alloc(angles.nbytes)
    cu.memcpy_htod( angles_device,  angles )

    output_hog_device = cu.mem_alloc(hog_output.nbytes)
    cu.memcpy_htod( output_hog_device, hog_output)
            
    # Execute the kernel
    patch_hog_kernel(input_im_device, pyl.int32(width), pyl.int32(height), pyl.int32(0), pyl.int32(height), pyl.int32(0), pyl.int32(width),
                     x_gradient_device, y_gradient_device, gradient_mag_device, angles_device, output_hog_device, 
                     block=(n_TPB_x,n_TPB_y,1), grid=(n_blocks_x,n_blocks_y))
    
    cu.memcpy_dtoh(hog_output,output_hog_device)
                   
    # Record the times
    gpu_end_time.record(); gpu_end_time.synchronize(); 
    gpu_time_delta_seconds = gpu_start_time.time_till(gpu_end_time) * 1e-3
    gpu_patch_times.append(gpu_time_delta_seconds)    
   
    
    ###
    # Keypoint-based HoG kernel
    ###
    
    num_keypoints = pyl.int32(1)
    keypoint_xs = np.asarray([width/2]).astype(np.float32)
    keypoint_ys = np.asarray([height/2]).astype(np.float32)
    window_size = pyl.int32(img_sizes[indx])
    
    # Start the timer
    gpu_start_time = cu.Event(); gpu_end_time = cu.Event(); gpu_start_time.record()
    
    # Create device variables
    input_im_device = cu.mem_alloc(t_image.nbytes)
    cu.memcpy_htod( input_im_device, t_image )

    xs_device = cu.mem_alloc(keypoint_xs.nbytes)
    cu.memcpy_htod(xs_device, keypoint_xs) 
    
    ys_device = cu.mem_alloc(keypoint_ys.nbytes)
    cu.memcpy_htod(ys_device, keypoint_ys) 

    x_gradient_device = cu.mem_alloc(x_gradient.nbytes)
    cu.memcpy_htod( x_gradient_device, x_gradient )

    y_gradient_device = cu.mem_alloc(y_gradient.nbytes)
    cu.memcpy_htod( y_gradient_device,  y_gradient )

    gradient_mag_device = cu.mem_alloc(gradient_mag.nbytes)
    cu.memcpy_htod( gradient_mag_device,  gradient_mag )

    angles_device = cu.mem_alloc(angles.nbytes)
    cu.memcpy_htod( angles_device,  angles )

    output_hog_device = cu.mem_alloc(hog_output.nbytes)
    cu.memcpy_htod( output_hog_device, hog_output)
        
    # Execute the kernel
    keypoint_hog_kernel(input_im_device, pyl.int32(width), pyl.int32(height), xs_device, ys_device, num_keypoints, window_size,
                     x_gradient_device, y_gradient_device, gradient_mag_device, angles_device, output_hog_device, 
                     block=(n_TPB_x,n_TPB_y,1), grid=(n_blocks_x,n_blocks_y))

    cu.memcpy_dtoh(hog_output,output_hog_device)
    
    # Record the times
    gpu_end_time.record(); gpu_end_time.synchronize(); 
    gpu_time_delta_seconds = gpu_start_time.time_till(gpu_end_time) * 1e-3
    gpu_keypoint_times.append(gpu_time_delta_seconds)
    
## END of timing code

#####    
# Plot the results
#####
fig = pyl.figure()
ax = fig.add_subplot(111)
plist = []
   
time_lists = [phog_times, vhog_times, gpu_keypoint_times, gpu_patch_times]
colors = ['rx--','k>-','b+--','g>-']
legend_labels = ["pHOG-CPU", "vHOG-CPU", "keypoint-GPU", "patch-GPU"]

for indx in range(len(time_lists)):
    plist.append(ax.plot(img_sizes, np.log10(time_lists[indx]), colors[indx]))
    
ax.legend(plist,legend_labels,loc=0)
ax.set_xlabel("Image dimension")
ax.set_ylabel("Time (log base 10) seconds")

pyl.show() 

time_data_file = "/home/ely/projects/faces/src/timing_data/times.pkl"
tfile = open(time_data_file,'w')
pickle.dump([img_sizes,time_lists],tfile)
tfile.close()
   
    