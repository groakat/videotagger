__author__ = 'peter'


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate configuration file for precomputeBackgroundFromFiles')
    parser.add_argument('--configPath', '-c',
                       help='filename where to write config')
    parser.add_argument('--flyClassifierPath', '-f',
                       help='path to fly classifier')
    parser.add_argument('--noveltyClassfyPath', '-n',
                       help='path to novelty classifier')
    parser.add_argument('--sourceFolder', '-s',
                       help='path to folder containing video files')
    parser.add_argument('--targetFolder', '-t',
                       help='path to target folder where background images are going to be saved in')

    args = parser.parse_args()

    import pyTools.legion.precomputeBackgroundFromFiles as precompBG

    configPath = args.configPath

    flyClassifierPath = args.flyClassifierPath
    noveltyClassfyPath = args.noveltyClassfyPath

    folder = args.sourceFolder
    targetFolder = args.targetFolder

    precompBG.generateConfigFile(configPath, flyClassifierPath,
                                 noveltyClassfyPath, folder, targetFolder)