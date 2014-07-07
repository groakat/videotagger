__author__ = 'peter'

import pyTools.legion.clusterFeatureExtractor as CFE
import pyTools.legion.classifier.RFClassifier as RFC

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('baseFolder', metavar='b',
                       help='folder containing the feature files')
    parser.add_argument('cfgFile', metavar='c',
                       help='folder containing the feature files')
    parser.add_argument('noPerBatch', metavar='n', type=int,  default=1440,
                       help='number of files to be processed by each process')
    parser.add_argument('clfPath', metavar='c',
                       help='path to classifer')


    args = parser.parse_args()
    baseFolder = args.baseFolder
    noPerBatch = args.noPerBatch
    cfgFile = args.cfgFile
    clfPath = args.clfPath

    fd2 = CFE.featureDesc('feat/traj/borgus','.borgus.npy')
    targetFeat = CFE.featureDesc('clf/borgusRF/','.cls.npy')

    cfe = RFC.RFClassifier(baseFolder, fd2, targetFeat, 0, 0, 0, clfPath)
    cfe.generateConfig(cfgFile, noPerBatch=noPerBatch, additionalParams=clfPath)