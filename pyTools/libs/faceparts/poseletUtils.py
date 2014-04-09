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
import scikits.learn.grid_search as gs
from mahotas import imread
import pylab as pyl
import KernelSource
import os, time, random, geometry
#####

"""poseletUtils.py
   This is a collection of functions used to train Poselet classifiers
   in the manner described in the following paper: 
   
   Lubomir Bourdev, Subhransu Maji, Thomas Brox,and Jitendra Malik. 
        Detecting People Using Mutually Consistent Poselet Activations, ECCV 2010.
        
   This file trains Poselets specifically using the labeled face parts data
   available from:
   < http://www.kbvt.com/LFPW/ >
   
   Please see the svmUtils.py file for more information about what you will need
   to have downloaded and what directory structure you'll need to get this working.
   
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
# Every pixel HoG kernel 
###
every_pixel_hog_kernel_source = KernelSource.every_pixel_hog_kernel_source_code()
every_pixel_hog_kernel_source_module = nvcc.SourceModule( every_pixel_hog_kernel_source)
every_pixel_hog_kernel = every_pixel_hog_kernel_source_module.get_function( "every_pixel_hog_kernel" )

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

def inside_box(xtest, ytest, ytop, ybot, xleft, xright):
    if ytop <= ytest and ytest <= ybot and xleft <= xtest and xtest <= xright:
        return 1
    else:
        return 0


def retrieve_annotations(file_name, data_entries, url_list, training_directory):
   
    for kk in range(len(data_entries)):
        
        cur_name =  data_entries[kk][0]
        for iter in range(len(url_list)):
            if cur_name == url_list[iter]:
                this_indx = iter
                break
        
        this_image_file_name = training_directory + str(this_indx) + "_" + cur_name.split("/")[-1]
        
        # Amend unusual file names or PNGs that were converted to JPGs
        if this_image_file_name.find('.') == -1:
            this_image_file_name = this_image_file_name + ".jpg"
        if this_image_file_name.find('.png') > -1 or this_image_file_name.find('.PNG') > -1:
            this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
        if this_image_file_name.find('.bmp') > -1 or this_image_file_name.find('.BMP') > -1:
            this_image_file_name = this_image_file_name.split('.')[0] + ".jpg"
        
        if this_image_file_name == file_name:
            found_indx = kk
            break
    
    annotations = data_entries[found_indx]
    return annotations
        
def obtain_bounding_patch(xy_tuples,M,N):
    xs = [elem[0] for elem in xy_tuples]
    ys = [elem[1] for elem in xy_tuples]
    min_x = int(np.min(xs))
    max_x = int(np.max(xs))
    min_y = int(np.min(ys))
    max_y = int(np.max(ys))
    
    # Slightly enlarge the x-directions
    if min_x - 5 > 0:
        min_x = min_x - 5
    else:
        min_x = 0
        
    if max_x + 5 < N:
        max_x = max_x + 5
    else:
        max_x = N
    
    # Slightly enlarge the y-directions
    if min_y - 5 > 0:
        min_y = min_y - 5
    else:
        min_y = 0
        
    if max_y + 5 < M:
        max_y = max_y + 5
    else:
        max_y = M
        
    return [min_y, max_y, min_x, max_x]

def get_patch_visibilities(keys, seed_patch):
    
    visibility_list = [0]*len(keys)
    for i,keypoint in enumerate(keys):
        if seed_patch[2] <= keypoint[0] and keypoint[0] <= seed_patch[3] and seed_patch[0] <= keypoint[1] and keypoint[0] <= seed_patch[3]:
            if keypoint[2] == 0:
                visibility_list[i] = 1
            else:
                visibility_list[i] = 0
        else:
            visibility_list[i] = 0
            
    return visibility_list
    

def compute_poselet_distance(seed_key_vals, seed_keypoint_visibilities_inside_patch, t_key_vals, t_keypoint_visibilities_inside_patch):
        
    lambda_vis = 25.0
    
    visibility_intersection = [elem[0]*elem[1] for elem in zip(seed_keypoint_visibilities_inside_patch, t_keypoint_visibilities_inside_patch)]
    visibility_union = [max(elem) for elem in zip(seed_keypoint_visibilities_inside_patch, t_keypoint_visibilities_inside_patch)]    
    
    D_vis = lambda_vis * sum(visibility_intersection)/sum(visibility_union)
      
    # If there are more than 2 keypoints commonly visible, compute Procrustes distance.
    # Otherwise, set distance to a large number.
    if sum(visibility_intersection) > 2:
        seed_proc_xs = np.asarray([elem[0] for i,elem in enumerate(seed_key_vals) if visibility_intersection[i] == 1])
        seed_proc_ys = np.asarray([elem[1] for i,elem in enumerate(seed_key_vals) if visibility_intersection[i] == 1])
        seed_proc = np.vstack((seed_proc_xs,seed_proc_ys))
    
        t_proc_xs = np.asarray([elem[0] for i,elem in enumerate(t_key_vals) if visibility_intersection[i] == 1])
        t_proc_ys = np.asarray([elem[1] for i,elem in enumerate(t_key_vals) if visibility_intersection[i] == 1])
        t_proc = np.vstack((t_proc_xs,t_proc_ys))  
    
        A0 = np.matrix(seed_proc) - np.mean(np.matrix(seed_proc),1); 
        B0 = np.matrix(t_proc) - np.mean(np.matrix(t_proc),1);
        T = np.asarray(geometry.procrustes.best_orthogonal_transform(A0,B0))
        return np.sqrt(np.sum(np.asarray(np.dot(T,A0) - B0)**2)) + D_vis
    else:
        return D_vis + 500  
    
def train_svm(DATA,LABELS):
    """ train_svm(DATA, LABELS)
        Function that applies scikits.learn LIBSVM Python bindings to train a linear SVM classifier on labeled data.
        
        inputs:    DATA -- A NumPy matrix where each row is a feature vector.
                   LABELS -- A NumPy matrix where each row is a singleton value (+1 or -1) that labels the corresponding row of DATA.
                   
        outputs:   clf -- A scikits.learn native object / data structure containing the parameters for the trained SVM. Use pickling to
                          save this for persistence across different Python sessions.
    """
    
    # Run the scikits.learn setup and training commands; return the result.
    parameters = {'gamma':np.arange(0.1,2.0,0.1), 'C':np.arange(1,20,1)}
    clf = gs.GridSearchCV(svm.SVC(kernel='rbf', probability=True), parameters)
    clf.fit(np.asarray(DATA), np.asarray(LABELS))
    
    best_parameters, score = max(clf.grid_scores_, key=lambda x: x[1])
    new_gamma = best_parameters['gamma']
    new_C = best_parameters['C']
    
    print "Optimal parameters found: gamma %f and C %f"%(new_gamma,new_C)
    clf1 = svm.SVC(kernel='rbf', gamma=new_gamma, C=new_C, probability=True)
    clf1.fit(DATA,LABELS, class_weight='auto')
    
    return clf1
# END train_svm()
     
#####
# Main
#####

# List of the LFPW fiducials
fiducial_name_list = ["left_eyebrow_out", "right_eyebrow_out", "left_eyebrow_in", "right_eyebrow_in", "left_eyebrow_center_top", 
                      "left_eyebrow_center_bottom", "right_eyebrow_center_top", "right_eyebrow_center_bottom", "left_eye_out",
                      "right_eye_out", "left_eye_in", "right_eye_in", "left_eye_center_top", "left_eye_center_bottom", 
                      "right_eye_center_top", "right_eye_center_bottom", "left_eye_pupil", "right_eye_pupil", "left_nose_out",
                      "right_nose_out", "nose_center_top", "nose_center_bottom", "left_mouth_out", "right_mouth_out",
                      "mouth_center_top_lip_top", "mouth_center_top_lip_bottom", "mouth_center_bottom_lip_top", "mouth_center_bottom_lip_bottom", 
                      "left_ear_top", "right_ear_top", "left_ear_bottom", "right_ear_bottom", "left_ear_canal", "right_ear_canal", "chin"]

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
        
# Poselet training
total_number_of_poselets = 30
for num_poselets_trained in range(total_number_of_poselets):
    poselet_start_time = time.time()
    found_file = 0
    while not found_file:
        random_file = random.choice(list_of_file_names)
        if os.path.isfile(random_file):
            found_file = 1
    
    random_image = imread(random_file)
    M = random_image.shape[0]; N = random_image.shape[1];
    
    annotations = retrieve_annotations(random_file, data_entries, url_list, training_directory)
    key_vals = [(float(annotations[elem]),float(annotations[elem+1]), int(annotations[elem+2])) for elem in range(2,len(annotations),3)]
    
    
    # Select a random number K of features, then sample K features from the annotations for this image.
    # Form the smallest bounding box that encompasses those features (slightly enlarged) and that will be the seed patch.
    num_features_to_use = random.choice(range(2,11))
    rand_sample_vector = np.random.permutation(np.hstack( (np.ones(num_features_to_use), np.zeros(len(key_vals) - num_features_to_use)))).astype(np.int32)
        
    keypoints_to_use = [elem for i,elem in enumerate(key_vals) if rand_sample_vector[i] == 1]
    seed_patch = obtain_bounding_patch(keypoints_to_use,M,N)
    
    if len(random_image.shape) == 3:
        seed_patch_im = clr.rgb2gray(random_image)
    else:
        seed_patch_im = np.copy(random_image)
    
    seed_patch_im = 255 * seed_patch_im[seed_patch[0]:seed_patch[1],seed_patch[2]:seed_patch[3]]
    im_out = open("/home/ely/projects/faces/data/poselets/seed_patches/seed_"+str(num_poselets_trained)+".png",'w')
    im_writer = png.Writer(seed_patch_im.shape[1], seed_patch_im.shape[0], greyscale=True)
    im_writer.write(im_out, np.asarray(seed_patch_im))
    im_out.close()
    
    cur_poselet_dir = "/home/ely/projects/faces/data/poselets/close_training_patches/poselet_"+str(num_poselets_trained)+"/"
    cmd = "mkdir "+cur_poselet_dir
    os.system(cmd)
    
    
    
    keypoint_visibilities_inside_patch = get_patch_visibilities(key_vals, seed_patch) 
    
    
    # For every other image in the training data, compute the slightly enlarged patch that contains the same features and
    # store the Procrustes / poselet distance of that patch w.r.t. the seed patch.
    
    poselet_distances = []
    for file_indx in range(len(url_list)):
        
        cur_file_name = get_local_file_name_from_url(file_indx,url_list,training_directory)
        if os.path.isfile(cur_file_name):
            cur_file_name = get_local_file_name_from_url(file_indx,url_list,training_directory)
            if not(cur_file_name == random_file):
            
                t_image = imread(cur_file_name)
                t_M = t_image.shape[0]; t_N = t_image.shape[1];              
                t_annotations = retrieve_annotations(cur_file_name, data_entries, url_list, training_directory)
                t_key_vals = [(float(t_annotations[elem]),float(t_annotations[elem+1]), int(t_annotations[elem+2])) for elem in range(2,len(t_annotations),3)]
                t_keypoints_to_use = [elem for i,elem in enumerate(t_key_vals) if rand_sample_vector[i] == 1]
                t_patch = obtain_bounding_patch(t_keypoints_to_use,t_M,t_N)        
                t_keypoint_visibilities_inside_patch = get_patch_visibilities(t_key_vals, t_patch)
                
                poselet_distances.append(compute_poselet_distance(key_vals, keypoint_visibilities_inside_patch, t_key_vals, t_keypoint_visibilities_inside_patch))
                print "Finished dist-calc iteration %d of %d with poselet distance %f"%(file_indx,len(url_list)-1,poselet_distances[-1])
            else:
                poselet_distances.append(0)
                print "Finished dist-calc iteration %d of %d with poselet distance 0 b/c test image was the same as randomly selected image"%(file_indx,len(url_list)-1)
        else:
            poselet_distances.append(10000)
            print "Skipping dist-calc iteration %d of %d (file not found)"%(file_indx,len(url_list)-1)

    # Keep only the top 250 closest patches, and compute the HoG descriptor for each of these patches, with +1 label.
    dist_rankings = np.argsort(poselet_distances)
    close_poselet_indices = dist_rankings[0:250]
    
    DATA = []
    LABELS = []
    # Positive training
    for close_poselet_indx in range(len(close_poselet_indices)):
        # Start a timer
        gpu_start_time = cu.Event(); gpu_end_time = cu.Event(); gpu_start_time.record()
        
        cur_file_name = get_local_file_name_from_url(close_poselet_indices[close_poselet_indx],url_list,training_directory)
        t_image = imread(cur_file_name)
        t_M = t_image.shape[0]; t_N = t_image.shape[1]; 
        t_annotations = retrieve_annotations(cur_file_name, data_entries, url_list, training_directory)
        t_key_vals = [(float(t_annotations[elem]),float(t_annotations[elem+1]), int(t_annotations[elem+2])) for elem in range(2,len(t_annotations),3)]
        t_keypoints_to_use = [elem for i,elem in enumerate(t_key_vals) if rand_sample_vector[i] == 1]
        t_patch = obtain_bounding_patch(t_keypoints_to_use,t_M,t_N)
        
        # Set up device variables to run the patch-based HoG GPU code to extract a feature for this image.
        # patch_hog_kernel(float* input_image, int im_width, int im_height, int patch_top, int patch_bot, int patch_left, int patch_right, 
        #                        float* gaussian_array, float* x_gradient, float* y_gradient, float* gradient_mag, float* angles, float* output_array)
        if len(t_image.shape) == 3:
            t_image = clr.rgb2gray(t_image)
        gpu_image = t_image.ravel().astype(np.float32)
        
        t_patch_im = 255 * t_image[t_patch[0]:t_patch[1],t_patch[2]:t_patch[3]]
        im_out = open(cur_poselet_dir+"training_patch_"+str(close_poselet_indx)+".png",'w')
        im_writer = png.Writer(t_patch_im.shape[1], t_patch_im.shape[0], greyscale=True)
        im_writer.write(im_out, np.asarray(t_patch_im))
        im_out.close()
        
        gpu_image = t_image.ravel().astype(np.float32)
        
        height     = pyl.int32( t_image.shape[0] )
        width      = pyl.int32( t_image.shape[1] )
        num_pixels = width * height
        
        # Variables needed during the GPU computation
        gaussian_array = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        x_gradient = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        y_gradient = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        gradient_mag = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        angles = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        hog_output = np.zeros((1,81)).ravel().astype(np.float32)
        
        # Number of threads per block
        n_TPB_x = int(16)
        n_TPB_y = int(16)

        # Number of thread blocks
        n_blocks_x = int(np.ceil(width/n_TPB_x))
        n_blocks_y = int(np.ceil(height/n_TPB_y))
        
        # Create device variables
        input_im_device = cu.mem_alloc(gpu_image.nbytes)
        cu.memcpy_htod( input_im_device,  gpu_image )

        gaussian_array_device = cu.mem_alloc(gaussian_array.nbytes)
        cu.memcpy_htod( gaussian_array_device,  gaussian_array )

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
        patch_hog_kernel(input_im_device, width, height, pyl.int32(t_patch[0]), pyl.int32(t_patch[1]), pyl.int32(t_patch[2]), pyl.int32(t_patch[3]),
                         x_gradient_device, y_gradient_device, gradient_mag_device, angles_device, output_hog_device, 
                         block=(n_TPB_x,n_TPB_y,1), grid=(n_blocks_x,n_blocks_y))

        cu.memcpy_dtoh(hog_output,output_hog_device)
        feat_vector = hog_output/np.sum(hog_output)
        
        gpu_end_time.record(); gpu_end_time.synchronize(); 
        gpu_time_delta_seconds = gpu_start_time.time_till(gpu_end_time) * 1e-3
        
        DATA.append(feat_vector)
        LABELS.append(1)
        print "Finished close-poselet HoG extraction %d of %d in time %f"%(close_poselet_indx, len(close_poselet_indices)-1, gpu_time_delta_seconds)
        
    
    # Randomly select images and patches until you have desired number of negative training samples.
    num_neg_samples = 500
    for neg_indx in range(num_neg_samples):
        
        gpu_start_time = cu.Event(); gpu_end_time = cu.Event(); gpu_start_time.record()
        
        found_file = 0
        while not found_file:
            rand_neg_file_indx = random.choice(range(len(url_list)))
            random_neg_file = get_local_file_name_from_url(rand_neg_file_indx,url_list,training_directory)
            if os.path.isfile(random_neg_file):
                found_file = 1
        
        random_neg_image = imread(random_neg_file)
        n_M = random_neg_image.shape[0]; n_N = random_neg_image.shape[1]
        dim = min(n_M,n_N)
        rand_height = random.choice( range(int(np.floor(dim/6)), int(np.ceil(dim/4)))  )
        rand_width = int(np.floor(1.5*rand_height))
        
        rand_y_top = pyl.int32(random.choice( range(0,n_M - rand_height-1) ))
        rand_y_bot = pyl.int32(rand_y_top + rand_height)
        
        rand_x_left = pyl.int32(random.choice( range(0, n_N - rand_width-1) ))
        rand_x_right = pyl.int32(rand_x_left + rand_width)
        
        if len(random_neg_image.shape) == 3:
            t_image = clr.rgb2gray(random_neg_image)
        else:
            t_image = random_neg_image
            
        gpu_image = t_image.ravel().astype(np.float32)
        
        height     = pyl.int32( random_neg_image.shape[0] )
        width      = pyl.int32( random_neg_image.shape[1] )
        
        num_pixels = width * height
        
        # Variables needed during the GPU computation
        gaussian_array = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        x_gradient = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        y_gradient = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        gradient_mag = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        angles = np.zeros((t_image.shape[0],t_image.shape[1])).ravel().astype(np.float32)
        rand_hog_output = np.zeros((1,81)).ravel().astype(np.float32)
        
        # Number of threads per block
        n_TPB_x = int(16)
        n_TPB_y = int(16)

        # Number of thread blocks
        n_blocks_x = int(np.ceil(n_N/n_TPB_x))
        n_blocks_y = int(np.ceil(n_M/n_TPB_y))
        
        # Create device variables
        rand_input_im_device = cu.mem_alloc(gpu_image.nbytes)
        cu.memcpy_htod( rand_input_im_device,  gpu_image )

        rand_gaussian_array_device = cu.mem_alloc(gaussian_array.nbytes)
        cu.memcpy_htod( rand_gaussian_array_device,  gaussian_array )

        rand_x_gradient_device = cu.mem_alloc(x_gradient.nbytes)
        cu.memcpy_htod( rand_x_gradient_device, x_gradient )

        rand_y_gradient_device = cu.mem_alloc(y_gradient.nbytes)
        cu.memcpy_htod( rand_y_gradient_device,  y_gradient )

        rand_gradient_mag_device = cu.mem_alloc(gradient_mag.nbytes)
        cu.memcpy_htod( rand_gradient_mag_device,  gradient_mag )

        rand_angles_device = cu.mem_alloc(angles.nbytes)
        cu.memcpy_htod( rand_angles_device,  angles )

        rand_output_hog_device = cu.mem_alloc(rand_hog_output.nbytes)
        cu.memcpy_htod( rand_output_hog_device, rand_hog_output)
        
        # Execute the kernel
        patch_hog_kernel(rand_input_im_device, width, height, rand_y_top, rand_y_bot, rand_x_left, rand_x_right,
                         rand_x_gradient_device, rand_y_gradient_device, rand_gradient_mag_device, rand_angles_device, rand_output_hog_device, 
                         block=(n_TPB_x,n_TPB_y,1), grid=(n_blocks_x,n_blocks_y))

        cu.memcpy_dtoh(rand_hog_output,rand_output_hog_device)
        feat_vector = rand_hog_output/np.sum(rand_hog_output)
        
        gpu_end_time.record(); gpu_end_time.synchronize(); 
        gpu_time_delta_seconds = gpu_start_time.time_till(gpu_end_time) * 1e-3        
        
        DATA.append(feat_vector)
        LABELS.append(0)
        print "Finished rand-negative HoG extraction %d of %d in time %f"%(neg_indx, num_neg_samples-1, gpu_time_delta_seconds)
        

    # Train the svm on this labeled data and pickle it.
    
    print "Pickling data and labels..."
    Dfile = open("/home/ely/projects/faces/data/features/poselet_data/poselet_data_"+str(num_poselets_trained)+".pkl",'w')
    Lfile = open("/home/ely/projects/faces/data/features/poselet_labels/poselet_labels_"+str(num_poselets_trained)+".pkl",'w')
    
    pickle.dump(DATA,Dfile)
    pickle.dump(LABELS,Lfile)
    
    Dfile.close()
    Lfile.close()
    
    print "Training and pickling the SVM..."
    clf = train_svm(DATA,LABELS)
    #classifier_output_file = open("/home/ely/projects/faces/data/classifiers/poselets/poselet_" + str(num_poselets_trained) + "-svm.pkl",'w')
    classifier_output_file = "/home/ely/projects/faces/data/classifiers/poselets/poselet_" + str(num_poselets_trained) + "-svm.pkl"
    joblib.dump(clf, classifier_output_file)
    #classifier_output_file.close()
    
    poselet_end_time = time.time() - poselet_start_time
    print "Finished training poselet classifier %d of %d..."%(num_poselets_trained,total_number_of_poselets-1)
    print "Required %f seconds."%(poselet_end_time)
    

######################################################






