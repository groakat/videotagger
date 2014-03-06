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

vol = "00"

# <codecell>

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
vial = 3

# <codecell>

exp = "00"
with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
    bhvrList = json.load(f)
    
fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv00.importAnnotations(bhvrList, annotations, [vial])
fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

exp = "01"
with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
    bhvrList = json.load(f)
    
fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv00.importAnnotations(bhvrList, annotations, [vial])
fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

exp = "02"
with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
    bhvrList = json.load(f)
    
fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv00.importAnnotations(bhvrList, annotations, [vial])
fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

exp = "03"
with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp{0}.json".format(exp), "r") as f:
    bhvrList = json.load(f)
    
fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv00.importAnnotations(bhvrList, annotations, [vial])
fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp{0}_vol{1}.npy".format(exp, vol))

# <codecell>

fdtv00.tree['meta']

# <codecell>


