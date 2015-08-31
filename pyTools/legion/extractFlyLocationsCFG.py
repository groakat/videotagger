__author__ = 'peter'

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('videoFolder', metavar='v',
                       help='folder containing the video files')
    parser.add_argument('backgroundFolder', metavar='b',
                       help='folder contain the background files')
    parser.add_argument('patchFolder', metavar='n',
                       help='folder where patches are going to be saved to')
    parser.add_argument('flyClassifierPath', metavar='f',
                       help='path to fly classifier')
    parser.add_argument('noveltyClassfyPath', metavar='o',
                       help='path to novelty classifier')
    parser.add_argument('minPerRun', metavar='m', type=int,
                       help='coverage of each run')
    parser.add_argument('cfgSavePath', metavar='c',
                       help='path where the config file is saved')


    args = parser.parse_args()

    videoFolder = args.videoFolder
    backgroundFolder = args.backgroundFolder
    patchFolder = args.patchFolder
    flyClassifierPath = args.flyClassifierPath
    noveltyClassfyPath = args.noveltyClassfyPath
    minPerRun = args.minPerRun
    cfgSavePath = args.cfgSavePath


    import pyTools.legion.extractFlyLocations as FL

    fe = FL.FlyExtractor(videoFolder, backgroundFolder, patchFolder, flyClassifierPath, noveltyClassfyPath,
                         recIdx=0, runIdx=0, minPerRun=minPerRun)

    fe.generateConfig(cfgSavePath)