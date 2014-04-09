""" collect_kbvt_data.py
    Author: Ely M. Spears, 
            Harvard University School of Engineering and Applied Science
            people.seas.harvard.edu~/ely
    Date: 08/18/2011
    Version: Python 2.6 and Ubuntu Linux 11.04. The system calls rely on Unix functions, so you may need to do
             some modifications to make this work on non-Unix platforms.
    
    This is a utility file providing functions that collect images referenced by the KBVT LFPW dataset found here:
    < http://kbvt.com/LFPW/ >. The face parts recognition dataset is part of the following publication:
    < "Localizing Parts of Faces Using a Consensus of Exemplars,"
        Peter N. Belhumeur, David W. Jacobs, David J. Kriegman, Neeraj Kumar,
        Proceedings of the 24th IEEE Conference on Computer Vision and Pattern Recognition (CVPR),
        June 2011.>
        
    The functions here can grab the images from their web URLs (pending that the URLs are not yet broken) and organize them
    into training and test directories.
"""

#####
# Imports
#####

import os, sys, os.path, subprocess;

#####
# Function definitions
#####

def download_images_from_urls(csv_file_path,download_path):
    """ download_images_from_urls() - Function that strips urls from the KBVT .csv data files, fetches the image data from the url, 
        and saves into a specified directory. The program also creates a text file showing whether or not a given url was successfully
        used to download an image, allowing the user to ignore data for classifier training in the related url link is broken. This file
        is stored into the same download_path variable as the images, and is always named "__success_summary__.txt". 
        
        inputs: csv_file_path -- String specifying the relative path to the .csv file containing the KBVT data.
                download_path -- String specifying the relavtive path where the downloaded images will be placed.
    """
    
    # Open the csv file, parse the urls into a unique list. Loop over that list and try to use wget to download the corresponding image.
    # If the download succeeds, mark another list with a 1, or 'success' or something. After all urls have been attempted, print the unique
    # list of url names as well as the binary success/failure list to an additional file and save it in with the directory of images.
    
    csv_file = open(csv_file_path,'r')
    summary_file = open(download_path + "__success_summary__.txt",'w')
    
    url_list = []
    success_list = []
    repeat_flag = 0
    
    for line in csv_file:
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
                
    summary_file.write("#####\n")            
    summary_file.write("# Summary of attempts to read web image data.\n")
    summary_file.write("# Image name from URL \t \t Successfully read?\n")
    summary_file.write("#####\n")
    
    max_file_name_length = max([len(elem.split('/')[-1]) for elem in url_list])
    
    for iter in range(len(url_list)):
        img_name = str(iter) + "_" + url_list[iter].split('/')[-1]
        num_to_pad = max_file_name_length - len(img_name)
        img_name_summary = img_name + (' '*(num_to_pad+10))
        
    # Some websites require wget to authenticate as if it was from a broswer, hence the -U Mozilla. -T sets an upper bound on the amount of time to
    # wait before declaring a time-out (here it is 60 seconds). -t indicates how many attempts to make for each image (here it is 2 attempts before
    # moving on to the next image).
        ret_code = (subprocess.call("wget -U Mozilla -T 60 -t 2 --output-document " + download_path + img_name + " " + url_list[iter],shell=True) == 0)
        summary_file.write(img_name_summary + "\t " + str(ret_code) + "\n")
        
    summary_file.close()
        
     
# Used for testing only
if __name__ == "__main__":
    download_images_from_urls("/home/ely/projects/faces/data/kbvt_lfpw_v1_train.csv","/home/ely/projects/faces/data/training/")