pyTools
=======

# Download:

    git clone https://github.com/groakat/pyTools.git


# Install


## Standalone VideoPlayer


The best way of getting this running is to use the anaconda python distribution (there is a free version available from their website):
https://store.continuum.io/cshop/anaconda/


This package needs the following external libraries:

* PyOpenGL (https://pypi.python.org/pypi/PyOpenGL)
* ffvideo (https://bitbucket.org/zakhar/ffvideo/wiki/Home)
* my fork of qimage2ndarray (https://github.com/groakat/qimage2ndarray)


Further, if using anaconda and linux (and mac?), one has to rename/delete the libm.so and all libm.x.so files. These files can be found in the lib folder of the anaconda installation. For example `/home/peter/anaconda/lib/`.
  
If using anaconda with KDE (under linux) there is another clash with Qt:

from https://github.com/ContinuumIO/anaconda-issues/issues/32:

    "here needs to be a qt.conf next to the executable that has this content: "[Paths]\nPlugins = '.'\n" "
  
Such a file can be found in the anaconda_fixes (qt.conf). In my case I copied this file into `/home/peter/anaconda/bin/`

Also:

    before creating the application object, one needs to do QtGui.QApplication.setLibraryPaths([]). The effect of the latter seems also be achievable by instead setting the environment variable "QT_PLUGIN_PATH" to an empty string.
  
To get this work, I edited the end of the .bashrc file in the home folder:

    # added by Anaconda 1.8.0 installer
    export PATH="/home/peter/anaconda/bin:$PATH"
    export QT_PLUGIN_PATH=""
    

## Interactive VideoPlayer
Communication to other services is done with zerorpc, which has additional dependencies:


* libzmq (`apt get install libzmq-dev`)
* `pip install pyzmq`
* headers of libffi (for ubuntu: `apt-get install libffi-dev`)
* `pip install cffi`
* `pip install zerorpc`
  
# User Guide

## VideoPlayer


The behaviour of the videoPlayer (in videoPlayer/videoPlayer.py) is controlled with a configuration file. There are some example configuration files in the videoPlayer/ folder. 

Once the videoPath is set, one should run

    python cacheFilelist.py -c <configuration file>
  
With `<configuration file>` being the filename of a configuration file. This will speed up the start up of the video player significantly.


The configuration files `fly_example.cfg` and `fly_videos.cfg` are commented and should be easy to change. Please let me know if anything is still unclear.

