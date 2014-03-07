# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import pyTools.system.misc as systemMisc
import pyTools.misc.FrameDataVisualization as FDV
import json
import sys
import argparse
import textwrap

# <codecell>

vols = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
exps = ["00", "01", "02", "03"]
vial = 3
bhvrPathOrg = "/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v{v}_exp{exp}.json"
treePathOrg = "/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v{v}_exp{exp}_vol{vol}.npy"
cfgPath = "/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/fly_exp{exp}_vol{vol}.cfg"

# <codecell>

cfgString = r"""
# Example config file for fly videos
# ---------------------------------------------------
# | Please run                                      |
# |                                                 |
# | python cacheFilelist.py -c <this file>          |
# |                                                 |
# | To precompute the file structure of the videos  |
# ---------------------------------------------------
#
# make sure to change all links

[Video]
# Video related settings

# No. of vial to be viewed (0, 1, 2, or 3)
vial: {v}

# Region of interest of vials
# (only x- values)
#           vial 1     vial2      vial3       vial4
vialROI: [ [350,660], [661,960], [971,1260], [1290,1590] ]

# Path to static background image
background: /media/peter/Elements/peter/data/tmp-20130506/20130219/00/2013-02-19.00-02-00-bg-True-False-True-True.png

# Path to _parent_ folder of videos                 \!/
# 1. fly videos are saved in a structure such as 'parent/days/hours/*.avi')
# 2. other videos are saved in such a structure: 'parent/*.avi')
# in the 2. case, switch `files-running-indices` below to True
videoPath: /media/peter/Elements/peter/data/tmp-20130506/

# path to behaviour visualization tree (can be selected in frameVisualizationView as well)
frame-data-visualization-path: /home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v{v}_exp{exp}_vol{vol}.npy

# file to cache of file structure (can be generated with python cacheFilelist.py -c <this file>)
bhvr-cache: /home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v{v}_exp{exp}.json

# (part of) name of first video to be shown after start-up
#startVideo: 2013-02-19.10-05-00

# set to true if video are cropped patches (foreground extraction)
# set to false if video is a standard video
cropped-video: true


# Buffer settings
# number of frames hold by each buffer (larger means faster playback, longer time to jump)
bufferWidth:  50
# number of buffers to be used (larger uses more threads, longer time to jump)
bufferLength: 1


# set false for self-captured data
# set true if video was split with ffmpeg into minute-chunks
files-running-indices: false


# rewind after having submitted requests
rewind-on-click: false


[ActiveLearning]
# Address to active learning server
remote-request-server: tcp://127.0.0.1:4242


[KeyMap]
# Key bindings for navigation and annotation
#
# The values have to be a value from the Qt::Key enum:
# http://qt-project.org/doc/qt-4.8/qt.html#Key-enum
# Without the C++ namespace
# I.e. Qt::Key_Escape has to be Key_Escape

# keys for annotation
# -------------------
# open/close annotation block
anno-1: Key_1
anno-2: Key_2
anno-3: Key_3
anno-4: Key_4
# escape open annotation
escape: Key_Escape
# toggle between adding/erasing mode
erase-anno: Key_Q

# keys for navigation
# -------------------
# continuous backward navigation (different speeds)
bwd-1: Key_E
bwd-2: Key_X
bwd-3: Key_Z
bwd-4: Key_Backslash
bwd-5: Key_S
bwd-6: Key_A
# continuous forward navigation (different speeds)
fwd-1: Key_T
fwd-2: Key_V
fwd-3: Key_B
fwd-4: Key_N
fwd-5: Key_H
fwd-6: Key_J
info: Key_I
# framewise backward navigation
step-b: Key_D
# framewise forward navigation
step-f: Key_G
# stopping continuous navigation
stop: Key_F
        
        
[StepSize]
# Defines how many frames should the player go ahead or 
# back during navigation in each speed step
bwd-1: -1
bwd-2: -2
bwd-3: -5
bwd-4: -10
bwd-5: -30
bwd-6: -60
fwd-1: 1
fwd-2: 2
fwd-3: 5
fwd-4: 10
fwd-5: 30
fwd-6: 60
step-b: -1
step-f: 1
stop: 0
# If false, step-b and step-f will not be framewise
# but a continuous navigation 
allow-steps: true


[Annotation]
# annotation settings
# list of dictionaries in JSON style
# each dictionary has to have the keys
#       "annot": (String) -- Name of annotator
#       "behav": (String) -- Name of behaviour
annotations: {a}
"""#.format(a=annotations, v=vial, exp="{exp}", vol="{vol}")

# <codecell>

for vol in vols:
    annotations = [
        {
            "annot": "volunteer {0}".format(vol),
            "behav": "negative",
            "color": "#ff0000"
        },
        {
            "annot": "volunteer {0}".format(vol),
            "behav": "airborne",
            "color": "#00ff00"
        },
        {
            "annot": "volunteer {0}".format(vol),
            "behav": "struggling",
            "color": "#0000ff"
        }
    ]
    
    for exp in exps:
        bhvrPath = bhvrPathOrg.format(v=vial, exp="{exp}")
        treePath = treePathOrg.format(v=vial, exp="{exp}", vol="{vol}")

        with open(bhvrPath.format(exp=exp), "r") as f:
            bhvrList = json.load(f)
            
        fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
        fdtv00.importAnnotations(bhvrList, annotations, [vial])
        fdtv00.save(treePath.format(exp=exp, vol=vol))
        
        with open(cfgPath.format(exp=exp, vol=vol), "w") as f:
            f.write(cfgString.format(a=json.dumps(annotations), v=vial, exp=exp, vol=vol))

# <codecell>


# <codecell>

# exp = "01"
# with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
#     bhvrList = json.load(f)
    
# fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
# fdtv00.importAnnotations(bhvrList, annotations, [vial])
# fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

# exp = "02"
# with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
#     bhvrList = json.load(f)
    
# fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
# fdtv00.importAnnotations(bhvrList, annotations, [vial])
# fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

# exp = "03"
# with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
#     bhvrList = json.load(f)
    
# fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
# fdtv00.importAnnotations(bhvrList, annotations, [vial])
# fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

# fdtv00.tree['meta']

# <codecell>

cfgString = r"""
# Example config file for fly videos
# ---------------------------------------------------
# | Please run                                      |
# |                                                 |
# | python cacheFilelist.py -c <this file>          |
# |                                                 |
# | To precompute the file structure of the videos  |
# ---------------------------------------------------
#
# make sure to change all links

[Video]
# Video related settings

# No. of vial to be viewed (0, 1, 2, or 3)
vial: {v}

# Region of interest of vials
# (only x- values)
#           vial 1     vial2      vial3       vial4
vialROI: [ [350,660], [661,960], [971,1260], [1290,1590] ]

# Path to static background image
background: /media/peter/Elements/peter/data/tmp-20130506/20130219/00/2013-02-19.00-02-00-bg-True-False-True-True.png

# Path to _parent_ folder of videos                 \!/
# 1. fly videos are saved in a structure such as 'parent/days/hours/*.avi')
# 2. other videos are saved in such a structure: 'parent/*.avi')
# in the 2. case, switch `files-running-indices` below to True
videoPath: /media/peter/Elements/peter/data/tmp-20130506/

# path to behaviour visualization tree (can be selected in frameVisualizationView as well)
frame-data-visualization-path: /home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v{v}_exp{exp}_vol{vol}.npy

# file to cache of file structure (can be generated with python cacheFilelist.py -c <this file>)
bhvr-cache: /home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v{v}_exp{exp}.json

# (part of) name of first video to be shown after start-up
#startVideo: 2013-02-19.10-05-00

# set to true if video are cropped patches (foreground extraction)
# set to false if video is a standard video
cropped-video: true


# Buffer settings
# number of frames hold by each buffer (larger means faster playback, longer time to jump)
bufferWidth:  50
# number of buffers to be used (larger uses more threads, longer time to jump)
bufferLength: 1


# set false for self-captured data
# set true if video was split with ffmpeg into minute-chunks
files-running-indices: false


# rewind after having submitted requests
rewind-on-click: false


[ActiveLearning]
# Address to active learning server
remote-request-server: tcp://127.0.0.1:4242


[KeyMap]
# Key bindings for navigation and annotation
#
# The values have to be a value from the Qt::Key enum:
# http://qt-project.org/doc/qt-4.8/qt.html#Key-enum
# Without the C++ namespace
# I.e. Qt::Key_Escape has to be Key_Escape

# keys for annotation
# -------------------
# open/close annotation block
anno-1: Key_1
anno-2: Key_2
anno-3: Key_3
anno-4: Key_4
# escape open annotation
escape: Key_Escape
# toggle between adding/erasing mode
erase-anno: Key_Q

# keys for navigation
# -------------------
# continuous backward navigation (different speeds)
bwd-1: Key_E
bwd-2: Key_X
bwd-3: Key_Z
bwd-4: Key_Backslash
bwd-5: Key_S
bwd-6: Key_A
# continuous forward navigation (different speeds)
fwd-1: Key_T
fwd-2: Key_V
fwd-3: Key_B
fwd-4: Key_N
fwd-5: Key_H
fwd-6: Key_J
info: Key_I
# framewise backward navigation
step-b: Key_D
# framewise forward navigation
step-f: Key_G
# stopping continuous navigation
stop: Key_F
        
        
[StepSize]
# Defines how many frames should the player go ahead or 
# back during navigation in each speed step
bwd-1: -1
bwd-2: -2
bwd-3: -5
bwd-4: -10
bwd-5: -30
bwd-6: -60
fwd-1: 1
fwd-2: 2
fwd-3: 5
fwd-4: 10
fwd-5: 30
fwd-6: 60
step-b: -1
step-f: 1
stop: 0
# If false, step-b and step-f will not be framewise
# but a continuous navigation 
allow-steps: true


[Annotation]
# annotation settings
# list of dictionaries in JSON style
# each dictionary has to have the keys
#       "annot": (String) -- Name of annotator
#       "behav": (String) -- Name of behaviour
annotations: {a}
""".format(a=annotations, v=vial, exp="{exp}", vol="{vol}")

# <codecell>

str(annotations)

# <codecell>


