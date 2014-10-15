import pyTools.system.misc as systemMisc
import pyTools.videoTagger.cacheFilelist as CF
import os
import shutil
import subprocess


def scanForVideoFiles(folder):
    fileList = []

    for ending in ['.mp4', '.avi', 'mpeg']:
        fileList += systemMisc.providePosList(folder, ending=ending)

    return fileList

def checkForCleanFolder(folder):
    fileList = scanForVideoFiles(folder)
    if len(fileList) != 1:
        raise ValueError("The directory you have chosen is not 'clean'. I.e. you need to select a folder that contains only a single video file you want to work on")
    else:
        return fileList[0]

def generateSmallVideo(videoPath, ext='avi'):
    basename = os.path.basename(videoPath)
    # ext = basename.split(os.path.extsep)[-1]
    basename_wo_ext = os.path.extsep.join(basename.split(os.path.extsep)[:-1])
    folder = os.path.dirname(videoPath)

    targetBasename = basename_wo_ext + "_small" + os.path.extsep + ext
    targetPath = os.path.join(folder, targetBasename)

    ffmpegStr = ('ffmpeg -i "{orgPath}" -vf scale=320:-1 ' + \
                '-strict -2 "{targetPath}"').format(orgPath=videoPath,
                                                 targetPath=targetPath)

    print ffmpegStr

    p = subprocess.Popen(ffmpegStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0]

    print(output)

    targetFullBasename = basename_wo_ext + "_full" + os.path.extsep + ext
    targetFullPath = os.path.join(folder, targetFullBasename)

    ffmpegStr = ('ffmpeg -i "{orgPath}" -an ' +\
                '-b 10000k -c:v mpeg4 "{targetPath}"').format(orgPath=videoPath,
                                                      targetPath=targetFullPath)

    p = subprocess.Popen(ffmpegStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0]

    print(output)
    # shutil.move(videoPath, targetFullPath)

    return folder, targetPath, ext

def generateStandardYaml(rootFolder, videoPath, videoExtension, backgroundImg=None):
    with open('config-template.yaml', 'r') as f:
        templateStr = f.readlines()

    config = ''.join(templateStr).format(rootFolder=rootFolder,
                                videoPath=videoPath,
                                backgroundImg=backgroundImg,
                                videoExt=videoExtension)

    yamlPath = os.path.join(rootFolder, 'config.yaml')
    with open(yamlPath, 'w') as f:
        f.writelines(config)

    return yamlPath

def checkForConfig(folder):
    if os.path.exists(os.path.join(folder, 'config.yaml')):
        return os.path.join(folder, 'config.yaml')
    else:
        return False

def prepareFolder(folder):
    yamlPath = checkForConfig(folder)
    if not yamlPath:
        filename = checkForCleanFolder(folder)
        folder, videoPath, videoExtension = generateSmallVideo(filename)
        yamlPath = generateStandardYaml(folder, videoPath,videoExtension)

        CF.cacheFilelist(yamlPath)

    return yamlPath


if __name__ == "__main__":
    prepareFolder('/media/peter/Seagate Backup Plus Drive/test3')