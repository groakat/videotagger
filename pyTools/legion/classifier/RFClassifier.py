__author__ = 'peter'

import pyTools.legion.clusterFeatureExtractor as CFE
from collections import OrderedDict
import numpy as np
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.externals import joblib

class RFClassifier(CFE.ClusterFeatureExtratorBase):
    def __init__(self, baseFolder, featureLst, targetFeat, batchIdx, startIdx, stopIdx, clfPath):
        self.cfr = joblib.load(clfPath)
        super(RFClassifier, self).__init__(baseFolder, featureLst, targetFeat, batchIdx, startIdx, stopIdx, params=None, overlap=[0,0])


    def classify(self, paths):
        feats = []
        for p in paths:
            feats += [np.load(p[0])]

        feat = np.concatenate(feats, axis=1)
        return self.cfr.predict(feat)

    def calculateFeatures(self, paths, loc, v, **params):
        pred = self.classify(paths)
        return pred



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
    parser.add_argument('clfPath', metavar='c',
                       help='path to classifer')


    args = parser.parse_args()
    baseFolder = args.baseFolder
    start = args.start
    stop = args.stop
    batchIdx = args.batchIdx
    clfPath = args.clfPath


    fd2 = CFE.featureDesc('feat/traj/borgus','.borgus.npy')
    targetFeat = CFE.featureDesc('clf/borgusRF','.cls.npy')

    cfe = RFClassifier(baseFolder, fd2, targetFeat, batchIdx, start, stop, clfPath)
    cfe.extractFeatures()