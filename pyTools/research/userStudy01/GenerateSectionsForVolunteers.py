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

with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3.json", "r") as f:
    bhvrList = json.load(f)

# <codecell>

bhvrList[1990]

# <codecell>

bhvrList[2700]

# <codecell>

experimentLength = 60 * 3

# <codecell>

bhvrList[1980 + experimentLength]

# <codecell>

exp00 = bhvrList[1980: 1980 + experimentLength]

# <codecell>

exp00[-1]

# <codecell>

with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp00.json", "w") as f:
    json.dump(exp00, f)

# <codecell>

start = 1980 + experimentLength
end = start + experimentLength
exp01 = bhvrList[start:end]

# <codecell>

exp01[-1]

# <codecell>

with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp01.json", "w") as f:
    json.dump(exp01, f)

# <codecell>

start = 1980 + experimentLength * 2
end = start + experimentLength
exp02 = bhvrList[start:end]

# <codecell>

exp02[-1]

# <codecell>

with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp02.json", "w") as f:
    json.dump(exp02, f)

# <codecell>

start = 1980 + experimentLength * 3
end = start + experimentLength
exp03 = bhvrList[start:end]

# <codecell>

with open("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrList_v3_exp03.json", "w") as f:
    json.dump(exp03, f)

# <codecell>

annotations = [
        {
            "annot": "peter",
            "behav": "falling",
            "color": "#ff0000"
        },
        {
            "annot": "peter",
            "behav": "dropping",
            "color": "#00ff00"
        },
        {
            "annot": "peter",
            "behav": "struggling",
            "color": "#0000ff"
        },
        {
            "annot": "peter",
            "behav": "struggling II",
            "color": "#00aaaa"
        }
    ]
vial = 3

# <codecell>

fdtv00 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv00.importAnnotations(exp00, annotations, [vial])
fdtv00.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp00.npy")

# <codecell>

fdtv01 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv01.importAnnotations(exp01, annotations, [vial])
fdtv01.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp01.npy")

# <codecell>

fdtv02 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv02.importAnnotations(exp02, annotations, [vial])
fdtv02.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp02.npy")

# <codecell>

fdtv03 = FDV.FrameDataVisualizationTreeBehaviour()
fdtv03.importAnnotations(exp03, annotations, [vial])
fdtv03.save("/home/peter/phd/code/pyTools/pyTools/pyTools/videoPlayer/bhvrTree_v3_exp03.npy")

# <codecell>


