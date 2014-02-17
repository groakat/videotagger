import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pyTools",
    version = "0.1.0",
    author = "Peter Rennert",
    author_email = "p.rennert@cs.ucl.ac.uk",
    description = ("Toolbox for handling large video datasets"),
    license = "--",
    keywords = "video",
    url = "https://github.com/groakat/pyTools",
    packages=["pyTools", 'pyTools/batch', 'pyTools/features', "pyTools/gui", "pyTools/imgProc", "pyTools/misc", "pyTools/qtGUI", "pyTools/sandbox", "pyTools/system", "pyTools/videoPlayer", "pyTools/videoProc"],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
    ],
)