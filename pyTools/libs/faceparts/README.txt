README for FaceParts CS 205 Project

################################################################################
Author: Ely M. Spears
ely@seas.harvard.edu
http://people.seas.harvard.edu/~ely

Date: Dec. 5, 2011

#####
Note: All of this code assumes you have successfully downloaded the LFPW
data set, preprocessed the images into JPG format, removed any broken
links or corrupted image downloads, and have modified any scripts provided
to reflect the directory structure you use (or make your directory structure
mimic that which is used in the code).
#####

All code is provided as-is with no warranty of any kind. A copy of the
GNU Public License is included with this code.

COPYRIGHT (C) 2011 Ely M. Spears.
You are free to modify and distribute this code without restriction.
###############################################################################

#####
#Misc. Notes:
#####

Please consult each of the included files for more detailed descriptions of what 
they are used for.

This software assumes the following:
Python 2.7, SciPy/NumPy 1.5.1, Matplotlib 0.99.3, Mahotas and FreeImagePy
PyGeometry, scikits.learn version 0.8.0, scikits.image, PyCUDA version 2011.1.2
and PyPNG.

I also made use of the os.system() function to execute external C code in some
places. This was successful on Ubuntu 11.04, but not tested in other operating
systems.
#####

#####
# Python Contents:
#####
collect_kbvt_data.py -- A script for downloading the annotated LFPW data set.

svmUtils.py -- A script for using the Dalal and Triggs C HoG extractor to train
	       SVMs that recognize single-fiducials from the LFPW data set.

vanillaHogUtils -- A collection of functions implementing a very basic
		   Histogram of Oriented gradients (HoG) serial version.

phogUtils -- A collection of functions implementing the pyramidal HoG descriptor.

poseletUtils -- A script that uses the GPU kernels to extract HoG features for
		the LFPW data and then forms poselets and trains SVM classifiers
		for these poselets.

testingUtils -- A script that uses the GPU kernels to run a classifer on every pixel
		of some example test images and stores the results for visualization.

KernelSource.py -- A file that stores all of the GPU kernel code for the various
		   implementations of the HoG descriptor.

timing.py -- A script that executes the serial and GPU HoG extractors and times them
	     for performance comparison on included image files. Assuming that
	     you have a CUDA device with compute capability 1.1 (so that it is fine
	     to use floats instead of doubles), then this script should work
	     out-of-the-box. Note that it will not necessarily work with newer GPU devices
	     such as those on the cluster (resonance).

#####
# Non-Python Contents
#####

There are 5 included image files, demo_{medium,large,big,huge,mega}.jpg, intended to be
used with the script timing.py and appropriate GPU devices.

The precompiled 'hog' executable is included. This comes from the Dalal and Triggs code
availble from < http://pascal.inrialpes.fr/soft/olt/ >. I have also included the
uncompiled source in the file  HOG_linux.tar.gz in case the precompiled binary does not
work. Note that you need the Boost library and there may be some other dependencies.

