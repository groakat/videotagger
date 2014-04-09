####
# Imports
####
import numpy as np, Image
import cPickle as pickle
from scikits.learn import svm
import os, os.path, hog
import time
from random import choice

import matplotlib.pyplot as plt 
import matplotlib.cm as cm

"""svmUtils.py
   This is a collection of functions used for processing data and
   annotations from the LFPW dataset. The code assumes you already
   have this data and have pre-processed it, converted all images
   to JPG format, removed any broken url links, and have changed the
   directories listed below to reflect the places where the data
   is located on your local machine.
   
   The functions prepare data and labels for training single-keypoint
   SVM classifiers. Several snippets of demo code are at the bottom
   of the file and they are commented out. Uncomment them and make
   appropriate directory structure changes to train your own
   classifiers.
   
   Note that this code depends upon the Dalal and Triggs HoG extractor
   that can be found here:
   < http://pascal.inrialpes.fr/soft/olt/ > 
   
   This code is released as-is, with no warranty of any kind, under the
   GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""


#####
# Function definitions
#####

# Function that takes in the name of an image and a trained classifier
# and then uses external C code to compute HoG feature description at every
# location in the image, classify every point according to the given classifier
# and returns two image-sized maps that contain the binary classification result
# and the probability result. The classifier should be organized such that the
# '0' class is a positive example of what is being detected, and '1' class is a
# negative example.
def local_detector_c(image_name,clf=None):
    # Make a tmp keypoint list with every pixel in this image listed.
    image = Image.open(image_name).convert("L")
    img = np.asarray(image)
    R,C = img.shape
    clas_output = np.zeros((R,C))
    prob_output = np.zeros((R,C))
    
    keypoint_file = open("tmp.kps",'w')
    x_iter_range = range(0,C)
    y_iter_range = range(0,R)
    total_iters = int(len(x_iter_range)*len(y_iter_range))
    
    for xx in x_iter_range:
        for yy in y_iter_range:
            keypoint_file.write("%d %d \n"%(xx,yy))
    keypoint_file.close()
    
    # Execute the C++ hog code to extract HoG features at every point, which are then stored in an output file
    print "Executing hog C code on an %d by %d image..."%(R,C)
    cmd = "./hog -i " + image_name + " -k tmp.kps -p 32 -o tmp.hog" 
    os.system(cmd)
    print "Finished storing HoG features"
    
    # Loop over every image location and parse the output file for the corresponding HoG vector.
    hog_file = open("tmp.hog",'r'); line_counter = 0; 
    num_components = int(hog_file.readline().split('\n')[0]); line_counter = 1; 
    num_lines = R*C; hog_file.readline(); line_counter = 2;
    
    # Run the libsvm classifier on that HoG vector and store the detection result (1 or 0) and the probability into two output maps.
    if clf:
        this_iter = 0
        
        for xx in x_iter_range:
            for yy in y_iter_range:
                line = hog_file.readline().split(' ')
                tmp_hog_vector = [float(elem) for elem in line[3:-1]]
                
                clas_output[yy,xx] = clf.predict([tmp_hog_vector])[0]
                prob_output[yy,xx] = clf.predict_proba([tmp_hog_vector])[0][1]
                print clf.predict_proba([tmp_hog_vector])
                
                print "Finished classifier iteration %d of %d"%(this_iter,total_iters-1)
                print "Classification results were: class: %f  probability %f"%(clas_output[yy,xx], prob_output[yy,xx])
                this_iter = this_iter + 1
                
                
        # Delete the keypoints file and the HoG file.
        hog_file.close()
        cmd = "rm tmp.kps; rm tmp.hog;" 
        os.system(cmd)
                
        return clas_output, prob_output
            
# train_svm() -- Function for training a linear SVM with scikits.learn
def train_svm(DATA,LABELS):
    """ train_svm(DATA, LABELS)
        Function that applies scikits.learn LIBSVM Python bindings to train a linear SVM classifier on labeled data.
        
        inputs:    DATA -- A NumPy matrix where each row is a feature vector.
                   LABELS -- A NumPy matrix where each row is a singleton value (+1 or -1) that labels the corresponding row of DATA.
                   
        outputs:   clf -- A scikits.learn native object / data structure containing the parameters for the trained SVM. Use pickling to
                          save this for persistence across different Python sessions.
    """
    
    # Run the scikits.learn setup and training commands; return the result.
    clf = svm.SVC(kernel='rbf',gamma=0.5,C=1.0,probability=True)
    clf.fit(DATA, LABELS)
    return clf
# END train_svm()

# prepare_data() -- Function that computes and arranges feature vectors from raw image data.
def prepare_data(fiducial_name):
    """ prepare_data(fiducial_name)
        Function that searches the Belhumeur data for labeled examples of the fiducial type indicated in the input, computes feature
        vectors for these examples, and arranges the feature vectors in a DATA matrix. Capability is also available for handling negative
        training examples as well.
        
        inputs:    fiducial_name -- A string that names the fiducial type to train for, from the Belhumeur data (e.g. left_eyebrow_out, right_ear_top, ...).
                                    See http://kbvt.com/LFPW/ for more details on the fiducial names.
        
        outputs:   DATA -- A matrix whose rows are the feature vectors for the specified fiducial data. Use pickling to save this so that it does not need to
                           be re-computed.
                   LABELS -- A list of 1's and 0's that labels the rows of DATA.
        
    """
        
    # Number of times to repeat a training image for purpose of drawing random negative examples.
    # The value of this will determine how many more negative examples there are than positive. If it
    # is set to 1, then there will be the same number of positive examples as negative ones.
    num_repeats = 1
    
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
    for indx in range(len(legend)):
        if fiducial_name == legend[indx]:
            fid_indx = indx
    
    data_entries = data_entries[1:]
    file_exists = [0]*len(data_entries)
    
    DATA = []
    LABELS = []
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
        
        print "On iteration %d the file is %s"%(kk,this_image_file_name)
        list_of_file_names.append(this_image_file_name)
        if os.path.isfile(this_image_file_name):
            file_exists[kk] = 1
            keypoint_file = open("tmp.kps",'w')
            # Ensure the image is an array of floats.
            image = Image.open(this_image_file_name).convert("L")
            img = np.asarray(image)
            L,C = img.shape
    
            # Add this feature x,y to the tmp list of keypoints.
            feat_x = np.floor(float(data_entries[kk][fid_indx]))
            feat_y = np.floor(float(data_entries[kk][fid_indx+1]))
            
            print "Current keypoint location: x: %d, y: %d"%(feat_x,feat_y)
            
            keypoint_file.write("%d %d \n"%(feat_x,feat_y))
            keypoint_file.close()
    
            # Execute the C++ hog code to extract HoG features at the feature point.
            print "Executing hog C code on an %d by %d image..."%(L,C)
            cmd = "./hog -i " + this_image_file_name + " -k tmp.kps -p 32 -o tmp.hog" 
            os.system(cmd)
    
            # Loop over every image location and parse the output file for the corresponding HoG vector.
            hog_file = open("tmp.hog",'r');
            hog_file.readline(); hog_file.readline(); # Skip the top two lines.
            feature_vec = [float(elem) for elem in hog_file.readline().split(' ')[3:-1]]
            hog_file.close()
            
            # Delete the keypoints file and the HoG file.
            cmd = "rm tmp.kps; rm tmp.hog;" 
            os.system(cmd)
            
            # Add this HoG vector to the training data, and a positive '1' label to the training labels.
            DATA.append(feature_vec)
            LABELS.append(1)
        print "Finished positive feature extraction iteration %d of %d"%(kk,len(data_entries))
        
    # Now we need to move randomly through the data, use the locations of the fiducials to guide us to
    # make negative training samples. The negative examples need to be some fixed distance away from the fiducial point.
    # Other than that, they can be randomly generated.
    for kk in range(len(list_of_file_names)):
        this_image_file_name = list_of_file_names[kk]
        if file_exists[kk]:
            for reps in range(num_repeats):
                # Load the image and make it an array
                image = Image.open(this_image_file_name).convert("L")
                img = np.asarray(image)
                keypoint_file = open("tmp.kps",'w')
                # Dimensions of image
                L,C = img.shape
                
                # Add this feature x,y to the tmp list of keypoints.
                feat_x = int(np.floor(float(data_entries[kk][fid_indx])))
                feat_y = int(np.floor(float(data_entries[kk][fid_indx+1])))
                win_size = 32
                
                # Make permissible vector of x values to draw for a negative sample
                if feat_x - win_size > 1 and feat_x + win_size < C-1:
                    x_range = range(0,feat_x - win_size)+range(feat_x + win_size,int(C))
                elif feat_x - win_size > 1 and feat_x + win_size > C-1:
                    x_range = range(0,feat_x-win_size)
                elif feat_x - win_size < 1 and feat_x + win_size < C-1:
                    x_range = range(feat_x + win_size,int(C))
                else:
                    x_range = range(0,int(C))
                    
                # Make permissible vector of y values to draw for a negative sample
                if feat_y - win_size > 1 and feat_y + win_size < L-1:
                    y_range = range(0,feat_y - win_size)+range(feat_y + win_size,int(L))
                elif feat_y - win_size > 1 and feat_y + win_size > L-1:
                    y_range = range(0,feat_y-win_size)
                elif feat_x - win_size < 1 and feat_y + win_size < L-1:
                    y_range = range(feat_y + win_size,int(L))
                else:
                    y_range = range(0,int(L))
                    
                this_x = choice(x_range)
                this_y = choice(y_range)
                    
                keypoint_file.write("%d %d \n"%(this_x,this_y))
                keypoint_file.close()
    
                # Execute the C++ hog code to extract HoG features at the feature point.
                print "Executing hog C code on an %d by %d image..."%(L,C)
                cmd = "./hog -i " + this_image_file_name + " -k tmp.kps -p 32 -o tmp.hog" 
                os.system(cmd)
    
                # Loop over every image location and parse the output file for the corresponding HoG vector.
                hog_file = open("tmp.hog",'r');
                hog_file.readline(); hog_file.readline(); # Skip the top two lines.
                feature_vec = [float(elem) for elem in hog_file.readline().split(' ')[3:-1]]
                hog_file.close()
            
                # Delete the keypoints file and the HoG file.
                cmd = "rm tmp.kps; rm tmp.hog;" 
                os.system(cmd)
            
                # Add this HoG vector to the training data, and a negative '0' label to the training labels.
                DATA.append(feature_vec)
                LABELS.append(0)
                print "Finished negative feature extraction iteration %d of %d"%(kk,len(list_of_file_names))
        
        
    #tmpdata = np.zeros((len(DATA),len(DATA[0])))
    #for kk in range(tmpdata.shape[0]):
    #    tmpdata[kk,:] = DATA[kk].T

    return DATA,LABELS
# END prepare_data()
    
 # plot_fiducial_overlay -- Function for plotting labeled fiducial locations over top of the image they label.   
def plot_fiducial_overlay(img_fname,img_indx,fiducial_name):
    """ plot_fiducial_overlay(img_fname,img_indx,fiducial_name)
        Function for plotting labeled fiducial locations over top of the image they label.
        
        inputs:     img_fname -- File name of the image to be displayed
                    img_indx -- Index used for finding this file name in the list of urls from the training data
                    fiducial_name -- String that names the particular face part to be plotted.
                   
        outputs:    None. Uses matplotlib to make a plot appear on the screen.
    """
    
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
    
    data_entries = [elem.split('\t') for elem in data_lines]
    # Save the first line as a key for what each component semantically corresponds to.
    legend = data_entries[0]
    for indx in range(len(legend)):
        if fiducial_name == legend[indx]:
            fid_indx = indx
    
    data_entries = data_entries[1:]
    print url_list[img_indx]
    
    cur_x = []
    cur_y = []
    for kk in range(len(data_entries)):
        if data_entries[kk][0] == url_list[img_indx]:
            cur_x.append(np.floor(float(data_entries[kk][fid_indx])))
            cur_y.append(np.floor(float(data_entries[kk][fid_indx+1])))
            
    image = Image.open(img_fname).convert("L")
    img = np.asarray(image)
    plt.imshow(img,cmap=cm.gray)
    plt.scatter(cur_x,cur_y,s=30, c='b')
    plt.show()
# END plot_fiducial_overlay()
    
    
#####    
# For Testing
#####
if __name__ == '__main__':
    """
    ##########
    # Testing
    st_time = time.time()
    test_file = "/home/ely/projects/faces/data/training/0_true-lies.jpg"
    local_detector_c(test_file)
    ed_time = time.time();
    print "Elapsed time is %f"%(ed_time-st_time)
    """
    
    
    #####
    # Set up parameters for test plotting overlays
    #####
    """
    # List of the LFPW fiducials
    fiducial_name_list = ["left_eyebrow_out_x", "right_eyebrow_out_x", "left_eyebrow_in_x", "right_eyebrow_in_x", "left_eyebrow_center_top_x", 
                          "left_eyebrow_center_bottom_x", "right_eyebrow_center_top_x", "right_eyebrow_center_bottom_x", "left_eye_out_x",
                          "right_eye_out_x", "left_eye_in_x", "right_eye_in_x", "left_eye_center_top_x", "left_eye_center_bottom_x", 
                          "right_eye_center_top_x", "right_eye_center_bottom_x", "left_eye_pupil_x", "right_eye_pupil_x", "left_nose_out_x",
                          "right_nose_out_x", "nose_center_top_x", "nose_center_bottom_x", "left_mouth_out_x", "right_mouth_out_x",
                          "mouth_center_top_lip_top_x", "mouth_center_top_lip_bottom_x", "mouth_center_bottom_lip_top_x", "mouth_center_bottom_lip_bottom_x", 
                          "left_ear_top_x", "right_ear_top_x", "left_ear_bottom_x", "right_ear_bottom_x", "left_ear_canal_x", "right_ear_canal_x", "chin_x"]
    
    # Choose a fiducial for test plotting
    fiducial_name = fiducial_name_list[0]
    #print fiducial_name
    
    # Choose a training image for test plotting and parse its file name index.
    #test_file = "/home/ely/projects/faces/data/training/12_wa.jpg"
    test_file = "/home/ely/projects/faces/data/training/0_true-lies.jpg"
    test_indx = int(test_file.split("/")[-1].split("_")[0])
    
    #####
    # End of set up parameters; plotting command on next line.
    #####
    
    # Plot the desired fiducial as an overlay on the image
    # Comment this out to avoid the test plotting.
    # plot_fiducial_overlay(test_file,test_indx,fiducial_name)
    
    ##########
    """
    """
    #####
    # Code for pickling the data into the right array formats.
    #####
    fiducial_training_name = "left_eyebrow_out_x"
    st_time = time.time();
    DATA,LABELS = prepare_data(fiducial_training_name)
    ed_time = time.time(); print "Preparing training data took %d sec."%(ed_time - st_time)

    print "Pickling data"
    st_time = time.time();
    data_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-data.pkl",'w')
    label_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-label.pkl",'w')
    pickle.dump(DATA, data_output_file)
    pickle.dump(LABELS, label_output_file)
    data_output_file.close()
    label_output_file.close()
    ed_time = time.time()
    print "Done pickling in %f sec"%(ed_time - st_time)
    ##########
    """
    
    
    #####
    # Code for actually building the classifier from pickled data and then saving the classifier with pickling.
    #####
    # import cPickle as pickle; from scikits.learn import svm; fiducial_training_name = "left_eyebrow_out_x"; 
    # data_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-data.pkl",'r'); 
    # label_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-label.pkl",'r')
    # DATA = pickle.load(data_output_file); LABELS = pickle.load(label_output_file); data_output_file.close(); label_output_file.close()
    # Above stuff is to copy and paste when tinkering in command line Python
    #####
    """
    fiducial_training_name = "left_eyebrow_out_x"
    data_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-data.pkl",'r')
    label_output_file = open("/home/ely/projects/faces/data/features/" + fiducial_training_name + "-label.pkl",'r')
    
    DATA = pickle.load(data_output_file)
    LABELS = pickle.load(label_output_file)
    
    data_output_file.close()
    label_output_file.close()
    
    print "Training classifier..."
    st_time = time.time();
    clf = train_svm(DATA,LABELS)
    classifier_output_file = open("/home/ely/projects/faces/data/classifiers/" + fiducial_training_name + "-svm.pkl",'w')
    pickle.dump(clf, classifier_output_file)
    classifier_output_file.close()
    ed_time = time.time()
    print "Done training in %f sec"%(ed_time - st_time)
    ##########
    """    
    
    #####
    # Code for loading a classifier and testing it on an example.
    #####
    fiducial_training_name = "left_eyebrow_out_x"
    classifier_output_file = open("/home/ely/projects/faces/data/classifiers/" + fiducial_training_name + "-svm.pkl",'r')
    clf = pickle.load(classifier_output_file)
    classifier_output_file.close()
    
    test_file = "/home/ely/projects/faces/data/training/0_true-lies.jpg"
    image = Image.open(test_file).convert("L")
    img = np.asarray(image)
    L,C = img.shape
    
    det_map,prob_map = local_detector_c(test_file,clf)
    
    fig1 = plt.figure()
    ax1 = fig1.add_subplot(131)
    ax1.imshow(det_map,cmap=cm.gray)
    ax2 = fig1.add_subplot(132)
    ax2.imshow(img,cmap=cm.gray)
    ax3 = fig1.add_subplot(133)
    ax3.imshow(prob_map,cmap=cm.gray)
    plt.show()
    
    