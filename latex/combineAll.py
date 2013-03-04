import os
import glob
import re
import copy as cp
import subprocess
import shlex

files = [f for f in os.listdir('.') if os.path.isfile(f)]

files = glob.glob('*.pdf')

symLink = []
fList = []


"""
create latex file
"""
latex = r'''\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[encoding, filenameencoding=utf8]{grffile}
\usepackage{pdfpages}
\begin{document}
'''



"""
create useful list of files for \includepdf
"""
for f in files:
    if f == "combineAll.pdf":
        continue
    
    latex += r"\Large\centering"
    latex += f + "\n"
    latex += r"\newpage"
    latex += "\n"

    if re.search(",", f) or re.search(" ", f):
        forg = cp.copy(f);
        f = re.sub("[, ]", '', f)

        os.symlink(forg, f)
        symLink.append(f)

    fList.append(f)


for f in fList:
    latex += r"\includepdf[pages=-]{\detokenize{"
    latex += f
    latex += "}}\n"

latex += r"\end{document}"

"""
save file and run pdflatex
"""
f = open("combineAll.tex", "w")
f.write(latex)
f.close()

proc = subprocess.Popen(["pdflatex", "-shell-escape", "-interaction=nonstopmode","combineAll.tex"])
proc.communicate()

"""
remove all symbolic links
"""
for f in symLink:
    os.remove(f)

