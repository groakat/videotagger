#!/bin/bash
echo "Downloading Sources"
conda config --add channels https://conda.binstar.org/groakat
conda install -y videotagger

echo "Installing VideoTagger in Applications.."
ANACONDAPATH=$(dirname $(dirname $(which python)))

cd $ANACONDAPATH/lib/python2.7/site-packages/pyTools*/pyTools/install/osx/

unzip -f Videotagger.zip
python installShortcut.py

echo "Done"