__author__ = 'peter'

import pyTools.legion.clusterFeatureExtractor as CFE
import pyTools.legion.feat.burgos as B

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('baseFolder', metavar='b',
                       help='folder containing the feature files')
    parser.add_argument('cfgFile', metavar='c',
                       help='folder containing the feature files')
    parser.add_argument('noPerBatch', metavar='n', type=int,  default=1440,
                       help='number of files to be processed by each process')


    args = parser.parse_args()
    baseFolder = args.baseFolder
    noPerBatch = args.noPerBatch
    cfgFile = args.cfgFile

    fd1 = CFE.featureDesc('feat/pos', ".pos.npy")
    targetFeat = CFE.featureDesc('feat/traj/borgus/','.borgus.npy')

    cfe = B.BurgosFeatureExtractor(baseFolder, fd1, targetFeat, 0, 0, params={}, overlap=[1,1])
    cfe.generateConfig(cfgFile, noPerBatch=noPerBatch)