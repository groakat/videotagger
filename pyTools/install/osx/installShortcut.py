__author__ = 'peter'
import os
import shutil
import plistlib as pll

def getPythonPath():
    bashCommand = "which python"
    import subprocess
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]

    return output[:-1]

def convertPListToXML(path):
    bashCommand = 'plutil -convert xml1 {0}'.format(path)
    import subprocess
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]

    return output[:-1]

def updatePythonInPList(path):
    tree = pll.readPlist(path)
    tree['ScriptInterpreter'] = getPythonPath()
    pll.writePlist(tree, path)

def getFolderOfThisScript():
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    folder = getFolderOfThisScript()
    path = os.path.join(folder,
                        'Videotagger.app/Contents/Resources/AppSettings.plist')
    convertPListToXML(path)
    updatePythonInPList(path)

    try:
        shutil.rmtree('/Applications/Videotagger.app')
    except OSError:
        pass

    shutil.copytree(os.path.join(folder,
                        'Videotagger.app'),
                '/Applications/Videotagger.app')