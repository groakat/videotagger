# Import the PyCUDA modules and initialize the CUDA device
import pycuda.autoinit
import pycuda.driver as cu
import pycuda.compiler as nvcc

import png
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

"""testingUtils.py
   This is a collection of functions used to test Poselet classifiers
   in the manner described in the following paper: 
   
   Lubomir Bourdev, Subhransu Maji, Thomas Brox,and Jitendra Malik. 
        Detecting People Using Mutually Consistent Poselet Activations, ECCV 2010.
        
   This file trains Poselets specifically using the labeled face parts data
   available from:
   < http://www.kbvt.com/LFPW/ >
   
   Please see the svmUtils.py file for more information about what you will need
   to have downloaded and what directory structure you'll need to get this working.
   
   This file assumes you have already trained Poselets using poseletUtils.py and
   you have used wither Pickle or the scikits.learn joblib to save the Python
   classifier objects.
   
   This script executes the poselet classifier on example images from the training data,
   forming binary and grayscale images of the same size, but which represent the
   poselet classification at each pixel location.
   
   This code is released as-is, with no warranty of any kind, under the
   GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""

#####
# CUDA kernels
#####
""" Below is the compilation of GPU kernel code. All of the
    PyCUDA kernel code is found in the file KernelSource.py.
"""

###
# HoG kernel 
###
patch_svm_kernel_source = KernelSource.patch_svm_kernel_source_code()
patch_svm_kernel_source_module = nvcc.SourceModule( patch_svm_kernel_source)
patch_svm_kernel = patch_svm_kernel_source_module.get_function( "patch_svm_kernel" )

#####
# Helper functions
#####

def get_local_file_name_from_url(this_indx,url_list,training_directory):
            
    cur_name = url_list[this_indx]       
    this_image_file_name = training_directory + str(this_indx) + "_" + cur_name.split("/")[-1]
        
    # Amend unusual file names or PNGs that were converted to JPGs
    if this_image_file_name.find('.') == -1:
        this_image_file_name = this_image_file_name + ".jpg"
    if this_image_file_name.find('.png') > -1 or this_image_file_name.find('.PNG') > -1:
        this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
    if this_image_file_name.find('.bmp') > -1 or this_image_file_name.find('.BMP') > -1:
        this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
    
    return this_image_file_name

def form_patch(ii,jj,patch_height,patch_width,height,width):
    ytop = max(0,ii - patch_height/2)
    ybot = ytop+patch_height
                
    if ybot >= height:
        ybot = height-1
        ytop = ybot - patch_height
        if ytop < 0:
            ytop = 0
                
                
    xleft = max(0,jj - patch_width/2)
    xright = xleft+patch_width
                
    if xright >= width:
        xright = width-1
        xleft = xleft - patch_width
        if xleft < 0:
            xleft = 0
            
    return pyl.int32(ytop), pyl.int32(ybot), pyl.int32(xleft), pyl.int32(xright) 


#####
# Main
#####


# Poselet parameters
num_poselets = 1
clf_name_prefix = "/home/ely/projects/faces/data/classifiers/poselets/poselet_"
clf_name_postfix = "-svm.pkl"

# Parameter setup and file I/O setup.
training_directory = "/home/ely/projects/faces/data/training/"
data_fname = "/home/ely/projects/faces/data/kbvt_lfpw_v1_train.csv"
data_file = open(data_fname)
data_lines = data_file.readlines()
    
url_list = []
repeat_flag = 0
for line in data_lines:
    line = line.split('\t')
    line[-1] = line[-1].split('\n')[0]
        
    if not line[0] == "imgurl":
        for iter in range(len(url_list)):
            if url_list[iter] == line[0]:
                repeat_flag = 1
                break
            else:
                repeat_flag = 0
                        
        if not repeat_flag:
            url_list.append(line[0])
    
url_list.sort()
data_file.close()
    
# Parse the line by tab separations
data_entries = [elem.split('\t') for elem in data_lines]
    
# Save the first line as a key for what each component semantically corresponds to.
legend = data_entries[0]  
data_entries = data_entries[1:]
file_exists = [0]*len(data_entries)
list_of_file_names = []

for kk in range(len(data_entries)):
        
    cur_name =  data_entries[kk][0]
    for iter in range(len(url_list)):
        if cur_name == url_list[iter]:
            this_indx = iter
        
    this_image_file_name = training_directory + str(this_indx) + "_" + cur_name.split("/")[-1]
        
    # Amend unusual file names or PNGs that were converted to JPGs
    if this_image_file_name.find('.') == -1:
        this_image_file_name = this_image_file_name + ".jpg"
    if this_image_file_name.find('.png') > -1 or this_image_file_name.find('.PNG') > -1:
        this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
    if this_image_file_name.find('.bmp') > -1 or this_image_file_name.find('.BMP') > -1:
        this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
        
    list_of_file_names.append(this_image_file_name)
    if os.path.isfile(this_image_file_name):
        file_exists[kk] = 1

# Loop over the poselets
for pose_indx in range(num_poselets):
    
    bin_dir = "/home/ely/projects/faces/data/performance/binary/poselet_" + str(pose_indx) + "/"
    score_dir = "/home/ely/projects/faces/data/performance/score/poselet_" + str(pose_indx) + "/"
    
    cmd1 = "mkdir " + bin_dir; cmd2 = "mkdir " + score_dir
    resp = os.system(cmd1); resp = os.system(cmd2);
    
    cur_clf_file = clf_name_prefix + str(pose_indx) + clf_name_postfix
    cur_clf = joblib.load(cur_clf_file)
    #cur_clf_in = open(cur_clf_file,'r')
    #cur_clf = pickle.load(cur_clf_in)
    #cur_clf_in.close()
    
    cur_pose_patch = "/home/ely/projects/faces/data/poselets/seed_patches/seed_"+str(pose_indx)+".png"
    patch_img = imread(cur_pose_patch)
    patch_height, patch_width = patch_img.shape
    
    # Loop over all of the images.
    num_file_success = 0
    num_images_to_test = 10
    while num_file_success < num_images_to_test:
        found_file = 0
        while not(found_file):
            test_indx = random.choice(range(len(url_list)))
            cur_file_name = get_local_file_name_from_url(test_indx,url_list,training_directory)
            if os.path.isfile(cur_file_name):
                found_file = 1
        
        
        original_image = imread(cur_file_name)
        if len(original_image.shape) == 3:
            original_image = clr.rgb2gray(original_image)
        
        height, width = original_image.shape
        
        binary_output = np.zeros((height,width))
        score_output = np.zeros((height,width))
       
        angles = original_image.ravel().astype(np.float32)
        hog_output = np.zeros((1,81)).ravel().astype(np.float32)

        angles_device = cu.mem_alloc(angles.nbytes)
        cu.memcpy_htod( angles_device,  angles )

        output_hog_device = cu.mem_alloc(hog_output.nbytes)
        cu.memcpy_htod( output_hog_device, hog_output)
        
        # Number of threads per block
        n_TPB_x = int(16)
        n_TPB_y = int(16)
        
        # Number of thread blocks
        n_blocks_x = int( np.ceil(width/n_TPB_x)  )
        n_blocks_y = int( np.ceil(height/n_TPB_y) )
        
        print "Blocks: (%d,%d) Threads: (%d,%d,1)"%(n_blocks_x,n_blocks_y,n_TPB_x,n_TPB_y)
        print "Processing %d x %d image" % (height,width)
        
        counter = 0
        st_time = time.time()
        
        x_gradient,y_gradient = np.gradient(original_image)
        gradient_mag = np.sqrt(x_gradient**2 + y_gradient**2)
        gradient_mag_device = cu.mem_alloc(gradient_mag.ravel().astype(np.float32).nbytes)
        cu.memcpy_htod(gradient_mag_device,gradient_mag.ravel().astype(np.float32) )
        
        angles = (np.arctan(np.divide(y_gradient,x_gradient+0.001))+np.pi/2)*180.0/np.pi
        
        angles_device = cu.mem_alloc(angles.ravel().astype(np.float32).nbytes)
        cu.memcpy_htod( angles_device, angles.ravel().astype(np.float32) )
        
        num_its = len(range(0,height-3,4))*len(range(0,width-3,4))-1
        for ii in range(0,height-3,4):
            for jj in range(0,width-3,4):
                it_st_time = time.time()
                ytop, ybot, xleft, xright = form_patch(ii,jj,patch_height,patch_width,height,width)
                
                # Execute the kernel
                patch_svm_kernel(angles_device, gradient_mag_device, ytop, ybot, xleft, xright, output_hog_device, 
                                 block=(n_TPB_x,n_TPB_y,1), grid=(n_blocks_x,n_blocks_y))
                

                cu.memcpy_dtoh(hog_output,output_hog_device)
                feat_vector = hog_output/np.sum(hog_output)
                
                this_prob = cur_clf.predict_proba([feat_vector])[0,1]
                this_prob_array = this_prob*np.ones(score_output[ii:ii+4,jj:jj+4].shape)
                score_output[ii:ii+4,jj:jj+4] = this_prob_array
                
                
                cu.memcpy_htod(angles_device, angles.ravel().astype(np.float32) )
                cu.memcpy_htod(gradient_mag_device,gradient_mag.ravel().astype(np.float32) )
                hog_output = np.zeros((1,81)).ravel().astype(np.float32)
                cu.memcpy_htod( output_hog_device, hog_output)
                
                it_ed_time = time.time() - it_st_time
                print "Finished iteration %d of %d in %f seconds. Class pred: %f ; Class 1 prob: %f"%(counter,num_its,it_ed_time,cur_clf.predict(feat_vector)[0],this_prob)
                counter = counter + 1
                
        binary_output = np.around(score_output)      
                
        im_out1 = open(bin_dir+str(pose_indx)+"_from_"+str(test_indx)+"bin.png",'w')
        im_out2 = open(score_dir+str(pose_indx)+"_from_"+str(test_indx)+"_score.png",'w')
        im_writer = png.Writer(width,height, greyscale=True)
        im_writer.write(im_out1, 255*binary_output)
        im_writer.write(im_out2, 255*score_output)
        im_out1.close()
        im_out2.close()
        ed_time = time.time() - st_time
        
        print "Finished poselet %d prediction on test image %d of %d in %f seconds"%(pose_indx, num_file_success, 9, ed_time)
        num_file_success = num_file_success + 1   
            
