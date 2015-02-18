#!/bin/bash

cd ~ 

eval "$(cat .bash_profile)"

# export PATH="/Users/peter/anaconda/bin:$PATH"

echo "Downloading Sources"
conda config --add channels https://conda.binstar.org/groakat
conda install --yes videotagger

echo "Installing VideoTagger in Applications.."
ANACONDAPATH=$(dirname $(dirname $(which python)))

cd $ANACONDAPATH/lib/python2.7/site-packages/pyTools/install/osx/

echo $(pwd)

echo $(ls)

unzip -o Videotagger.zip
# python installShortcut.py

cp -fR Videotagger.app /Applications/

echo "Done"