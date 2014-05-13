__author__ = 'peter'

import pyTools.legion.clusterFeatureExtractor as CFE
import pyTools.features.trajectory.Burgos as B
from collections import OrderedDict
import numpy as np

class BurgosFeatureExtractor(CFE.ClusterFeatureExtratorBase):
    def generatePosMatrix(self, paths, loc):
        posMats = []
        cnt = 0

        if loc.start == -1:
            posMats += [np.load(paths[cnt])[-1:, ...]]
            cnt += 1

        posMats += [np.load(paths[cnt])]
        slc = slice(0, posMats[-1].shape[0])
        cnt += 1

        if loc.stop == 2:
            posMats += [np.load(paths[cnt])[:1, ...]]
            cnt += 1

        return np.concatenate(posMats, axis=0), slc

    def correctTraj(self, traj, v, rois):
        yOffset = rois[v][0]
        traj[:,1] = traj[:,1] - yOffset
        return traj


    def extractTrajFeatures(self, paths, loc, v, rois):
        traj, slc = self.generatePosMatrix(paths[0], loc)
        traj = self.correctTraj(traj, v, rois)
        dt = 60.0 / (slc.stop - slc.start)
        feat = B.generateTrajFeatures(traj, dt)
        return feat[slc]

    def calculateFeatures(self, paths, loc, v, **params):
        rois = params["rois"]
        feat = self.extractTrajFeatures(paths, loc, v, rois)
        return feat

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('batchIdx', metavar='i', type=int,
                       help='index of batch')
    parser.add_argument('start', metavar='s', type=int,
                       help='index where this processing starts')
    parser.add_argument('stop', metavar='e', type=int,
                       help='index where this processing stops')
    parser.add_argument('baseFolder', metavar='b',
                       help='folder containing the feature files')


    args = parser.parse_args()
    baseFolder = args.baseFolder
    start = args.start
    stop = args.stop
    batchIdx = args.batchIdx

    params = {"rois":[[350, 660], [661, 960], [971, 1260], [1270, 1600]]}

    fd1 = CFE.featureDesc('feat/pos', ".pos.npy")
    targetFeat = CFE.featureDesc('feat/traj/borgus/','.borgus.npy')

    cfe = BurgosFeatureExtractor(baseFolder, fd1, targetFeat, batchIdx, start, stop, params=params, overlap=[1,1])
    cfe.extractFeatures()
