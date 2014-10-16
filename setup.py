from __future__ import with_statement
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

## windows install part from http://matthew-brett.github.io/pydagogue/installing_scripts.html
import os
from os.path import join as pjoin, splitext, split as psplit
from distutils.core import setup
from distutils.command.install_scripts import install_scripts
from distutils import log

BAT_TEMPLATE = \
r"""@echo off
set mypath=%~dp0
set pyscript="%mypath%{FNAME}"
set /p line1=<%pyscript%
if "%line1:~0,2%" == "#!" (goto :goodstart)
echo First line of %pyscript% does not start with "#!"
exit /b 1
:goodstart
set py_exe=%line1:~2%
call %py_exe% %pyscript% %*
"""


class my_install_scripts(install_scripts):
    def run(self):
        install_scripts.run(self)
        if not os.name == "nt":
            return
        for filepath in self.get_outputs():
            # If we can find an executable name in the #! top line of the script
            # file, make .bat wrapper for script.
            with open(filepath, 'rt') as fobj:
                first_line = fobj.readline()
            if not (first_line.startswith('#!') and
                    'python' in first_line.lower()):
                log.info("No #!python executable found, skipping .bat "
                            "wrapper")
                continue
            pth, fname = psplit(filepath)
            froot, ext = splitext(fname)
            bat_file = pjoin(pth, froot + '.bat')
            bat_contents = BAT_TEMPLATE.replace('{FNAME}', fname)
            log.info("Making %s wrapper for %s" % (bat_file, filepath))
            if self.dry_run:
                continue
            with open(bat_file, 'wt') as fobj:
                fobj.write(bat_contents)

### end windows install part

setup(
    name = "pyTools",
    version = "0.1.0",
    author = "Peter Rennert",
    author_email = "p.rennert@cs.ucl.ac.uk",
    description = ("Toolbox for handling large video datasets"),
    license = "--",
    keywords = "video",
    url = "https://github.com/groakat/pyTools",
    packages=["pyTools", 'pyTools/batch', 'pyTools/features', "pyTools/gui", "pyTools/imgProc", "pyTools/misc", "pyTools/qtGUI", "pyTools/sandbox", "pyTools/system", "pyTools/videoTagger", "pyTools/videoProc", "pyTools/icon"],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
    ],
    entry_points={
        #'console_scripts': [
            #'videotagger = pyTools.videoTagger.videoTagger:main',
        #],
        'gui_scripts': [
            'videotagger = pyTools.videoTagger.videoTagger:main',
        ]
    },
    package_data = {
        '': ['*.svg']
    }
)
#cmdclass = {'install_scripts': my_install_scripts}