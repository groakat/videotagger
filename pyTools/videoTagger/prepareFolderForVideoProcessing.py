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
    if len(fileList) == 1:
        return fileList[0]
    elif len(fileList) == 3:
        core = os.path.commonprefix(fileList)
        videoExtension = fileList[0].split('.')[-1]
        if core + '_full.' + videoExtension in fileList \
        and core + '_small.' + videoExtension in fileList \
        and core + '.' + videoExtension in fileList:
            fileList = [core + '.' + videoExtension]
            return fileList[0]
    else:
        raise ValueError("The directory you have chosen is not 'clean'. I.e. you need to select a folder that contains only a single video file you want to work on")

def generateSmallVideo(videoPath, ext='avi'):
    basename = os.path.basename(videoPath)
    # ext = basename.split(os.path.extsep)[-1]
    basename_wo_ext = os.path.extsep.join(basename.split(os.path.extsep)[:-1])
    folder = os.path.dirname(videoPath)

    targetBasename = basename_wo_ext + "_small" + os.path.extsep + ext
    targetPath = os.path.join(folder, targetBasename)

    ffmpegStr = ('ffmpeg -i "{orgPath}" -y -c:v ffv1 -vf scale=320:-1 ' + \
                '-qscale 0 -r 30 "{targetPath}"').format(orgPath=videoPath,
                                                 targetPath=targetPath)

    print ffmpegStr

    p = subprocess.Popen(ffmpegStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0]

    print(output)

    targetFullBasename = basename_wo_ext + "_full" + os.path.extsep + ext
    targetFullPath = os.path.join(folder, targetFullBasename)

    ffmpegStr = ('ffmpeg -i "{orgPath}" -y -an ' +\
                '-qscale 0 -c:v ffv1 -r 30 "{targetPath}"').format(orgPath=videoPath,
                                                      targetPath=targetFullPath)

    p = subprocess.Popen(ffmpegStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0]

    print(output)
    # shutil.move(videoPath, targetFullPath)

    return folder, targetPath, ext

def generateStandardYaml(rootFolder, videoPath, videoExtension, backgroundImg=None):
    templateFolder = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(templateFolder,
                           'config-template.yaml'), 'r') as f:
        templateStr = f.readlines()

    config = ''.join(templateStr).format(videoPath=videoPath,
                                         backgroundImg=backgroundImg,
                                         videoExt=videoExtension,
                                         patches='""',
                                         positions='""')

    yamlPath = os.path.join(rootFolder, 'videoTaggerConfig.yaml')
    with open(yamlPath, 'w') as f:
        f.writelines(config)

    return yamlPath

def checkForConfig(folder):
    if os.path.exists(os.path.join(folder, 'videoTaggerConfig.yaml')):
        return os.path.join(folder, 'videoTaggerConfig.yaml')
    else:
        return False

def prepareFolder(folder, alwaysGenerateSmallVideo=False):
    yamlPath = checkForConfig(folder)
    if not yamlPath or alwaysGenerateSmallVideo:
        filename = checkForCleanFolder(folder)
        folder, videoPath, videoExtension = generateSmallVideo(filename)
        yamlPath = generateStandardYaml(folder, videoPath,videoExtension)

        CF.cacheFilelistFromConfig(yamlPath)

    return yamlPath


if __name__ == "__main__":
    prepareFolder('/media/peter/Seagate Backup Plus Drive/gabe_mouse_run_test/')