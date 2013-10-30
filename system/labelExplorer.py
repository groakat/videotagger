import numpy as np
import pylab as plt

import os
import pyTools.videoProc.annotation as annotation
import pyTools.system.videoExplorer as videoExplorer
import pyTools.misc.config as cfg
import pyTools.misc.basic as bsc
import time
import operator

from ffvideo import VideoStream

from collections import deque
import copy
import json
import misvm as ms


def extractAnnotatedFrames(vials=None, annotator="peter", behaviour="struggling", 
                           dataFolder='/run/media/peter/Elements/peter/data/tmp-20130506'):
    
    filt = annotation.AnnotationFilter(vials, [annotator], [behaviour])
#     frames = []
    
    # list of filtered frames (one list for each vial)
    a = [[] for i in range(4)]
    
    for root, dirs, files in os.walk(dataFolder):
        for file in sorted(files):
            if file.endswith(".bhvr"):
                # load annotation and filter it #
                path = os.path.join(root,file)
                anno = annotation.Annotation()
        
                anno.loadFromFile(path)
                filteredAnno = anno.filterFrameList(filt)
                
                if behaviour in anno.behaviours and annotator in anno.annotators:
                    # extract frame numbers corresponding to filter #
                    frameList = [[i, x] for i, x in enumerate(filteredAnno.frameList)  \
                                             if x is not None]
                    
                    # sort frames into the different vials to know what
                    # feature files we will have to load later #
                    if frameList:
                        for f in frameList:
#                             frames += [[path, f[0]]]
                            for v in range(len(a)):
                                if f[1][v] is not None:
                                    a[v] += [[path.split('.bhvr')[0] + '.pos.npy', f[0]]]
                    
    return a

def extractNegativeAnnotatedFrames(vials=None, annotator="peter", behaviours=["struggling"], 
                           dataFolder='/run/media/peter/Elements/peter/data/tmp-20130506',
                           samplesNo=10000):
    """
    Extracts frames that do not contain any of the given behaviours.
    
    The algorithm samples frames randomly from the given `dataFolder` and verifies that they
    are not labelled with the given annotations
    
    TODO: needs refinement in vial selection
    """
#     frames = []
    noVials = 3
    
    # list of filtered frames (one list for each vial)
    a = [[] for i in range(3)]
    
    fileList = []
    for root, dirs, files in os.walk(dataFolder):
        for file in files:
            if file.endswith(".bhvr"):
                fileList += [os.path.join(root,file)]
                
    fileList.sort() 
    
    for i in range(samplesNo):
        # random selection of file (not the first or last one because some features
        # might not be extracted for them)
        fileIdx = int(np.floor(np.random.random() * (len(fileList) - 2))) + 1
        # random selection of vial
        vIdx = int(np.floor(np.random.random() * noVials))
        
        # load annotation and filter it #
        path = os.path.join(fileList[fileIdx])
        anno = annotation.Annotation()
        anno.loadFromFile(path)
        
        # random selection of frame
        negativeFrames = range(len(anno.frameList))
        for behaviour in behaviours:
            annoFrames = anno.getFramesWithBehaviour(behaviour, [vIdx])
            negativeFrames = set(negativeFrames).difference(annoFrames)
            
        if not negativeFrames:
            # if we get here, that means that all frames
            # in the given vial are annotated by the behaviour
            i -= 1
            continue
        else:
            selFrameIdx = np.random.permutation(list(negativeFrames))[0]
            a[vIdx] += [[path.split('.bhvr')[0] + '.pos.npy', selFrameIdx]]
        
        
                    
    return a
                    

       
# cfg.log.info("finished in {0} sec".format(time.time() - t))   

def createFeatureVector(a, ending=['feat.hog3d']):
    """
    Args:
        a (list [[path, int]]):
                    list of paths with corresponding
                    frame numbers
                    see :func:`extractAnnotatedFrames`
    """
    # feature matrix #
    feats = []
    for i in range(len(a)):
        # path to feature vector #
        path = ''
        # numpy array containing features #
        npA = [None for k in range(len(ending))]
        for frame in a[i]:            
            if frame[0] != path:
                # load new feature vector only if it was not used already before #
                path = frame[0]
                for k in range(len(ending)):
                    npA[k] = np.load(path.split('.pos.npy')[0] + \
                                     '.v{0}.{ending}.npy'.format(i, ending=ending[k]))
            f = []
            try:
                for k in range(len(ending)):
                    f += [npA[k][frame[1]].flatten()]
            except:
                print("Problems loading {0}".format(frame))
                
            feats += [np.concatenate(tuple(f))]
            
    return np.asarray(feats)

def createFeatureVectorFromAnnotationSections(aS, ending=['feat.hog3d']):
    """
    Args:
        a (list [[path, int]]):
                    list of paths with corresponding
                    frame numbers
                    see :func:`extractAnnotatedFrames`
    """
    # feature matrix #
    feats = []
    aCnt = 0
    for a in aS:
        aCnt += 1
        # path to feature vector #
        path = ''
        vial = -1
        # numpy array containing features #
        npA = [None for k in range(len(ending))]
        featSs = []
        
        sCnt = 0
        for section in a:            
            sCnt += 1
            featFs = []
            for frame in section:
                if frame[0] != path or frame[2] != vial:
                    # load new feature vector only if it was not used already before #
                    path = copy.copy(frame[0])
                    vial = frame[2]
                    for k in range(len(ending)):
                        npA[k] = np.load(path.split('.pos.npy')[0] + \
                                         '.v{0}.{ending}.npy'.format(vial, ending=ending[k]))
                f = []
                try:
                    for k in range(len(ending)):
                        f += [npA[k][frame[1]].flatten()]
                except:
                    print("Problems loading {0}".format(frame))
                
                featFs += [np.concatenate(tuple(f))]
            
            feat = np.asarray(featFs)
            if feat.shape == (0,):
                print frame
                
            featSs += [feat]
        
        feats += [featSs]        
                
            
    return feats
            
def computeConfusionMatrix(predict, label):
    size = np.max(label) + 1
    cmat = np.zeros((size, size), dtype=np.int32)
    
    for i in range(predict.shape[0]):
        cmat[np.int32(label[i]), np.int32(predict[i])] += 1
        
    return cmat

from sklearn.cross_validation import StratifiedKFold
def crossValidateIndependentSamples(data, labels, classifier, Nfolds=2):
    idx = np.unique(labels)
    cmat = np.zeros((idx.shape[0], idx.shape[0]), dtype=np.int32)
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    kf = StratifiedKFold(labels, n_folds=Nfolds, indices=True)
    
    cnt = 1
    
    predict = []
    testLbl = []
    testPos = []
    for train, test in kf:
        testPos.append(test)
        print("processing fold no {0}/{1}".format(cnt, Nfolds))
        
        trainSet = data[train]
        trainLbl = labels[train]
        
        testSet = data[test]
        testLbl.append(labels[test])
        
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        cmat += computeConfusionMatrix(predict[-1], testLbl[-1])
        cnt += 1
    
    return cmat, predict, testLbl, testPos

def crossValidateSampleSets(data, labels, sets, classifier, Nfolds=2):
    """
    Args:
        data (list of np.arrays)
                list of feature matrices, one for each class
        labels (list of np.arrays)
                list of labels corresponding feature matrices in data
        sets (list of [begin (int), end (int)])
                list of indeces of sets of groups of samples in feature
                matrices
                
                
    """
    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    
    pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
    pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    idx = np.max(pseudoLabel) + 1
    cmat = np.zeros((idx, idx), dtype=np.int32)
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    kf = StratifiedKFold(pseudoLabel, n_folds=Nfolds, indices=True)
    
    cnt = 1
    
    predict = []
    testLbl = []
    testPos = []
    trainSets = []
    testSets = []
    
    for train, test in kf:
        testPos.append(test)
        print("processing fold no {0}/{1}".format(cnt, Nfolds))
        
        
        # create balanced training set
        cFeat = []
        for c in range(idx):
            cFeat += [[i for t in train \
                           if pseudoLabel[t] == c \
                               for i in range(*sets[pseudoLabel[t]][pseudoFeat[t]])]]
            
        maxSamples = min([len(a) for a in cFeat])
        
        feats = []
        lbls= []
        selection = []
        for c in range(len(cFeat)):
            idces = np.random.permutation(np.asarray(cFeat[c]))[:maxSamples]
            feats += [data[c][idces]]
            lbls += [[c] * maxSamples]
            selection += [idces]
            
                
        trainSet = np.concatenate(tuple(feats)) #data[train]
        trainSets += [selection]
        trainLbl = np.concatenate(tuple(lbls)) #labels[train]
        
        
        # create test set from all samples in sets choosen for testing
        # (class imbalance does not matter)
        cFeat = []
        for c in range(idx):
            cFeat += [[i for t in test \
                           if pseudoLabel[t] == c \
                               for i in range(*sets[pseudoLabel[t]][pseudoFeat[t]])]]
        
        feats = []
        lbls= []
        for c in range(len(cFeat)):
            feats += [data[c][cFeat[c]]]
            lbls += [[c] * len(cFeat[c])]
            
                
        testSet = np.concatenate(tuple(feats)) #data[train]
        testSets += [cFeat]
        testLbl.append(np.concatenate(tuple(lbls))) #labels[train]
        
        
        # train classifier and test 
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        cmat += computeConfusionMatrix(predict[-1], testLbl[-1])
        cnt += 1
    
    return cmat, predict, trainSets, testSets


def getPseudoIndeces(sets):    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
    pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    return pseudoFeat, pseudoLabel

def crossValidateSectionSets(sets, classifier, Nfolds=2):
    """
    Args:
        data (list of np.arrays)
                list of feature matrices, one for each class
        labels (list of np.arrays)
                list of labels corresponding feature matrices in data
        sets (list of [begin (int), end (int)])
                list of indeces of sets of groups of samples in feature
                matrices
                
                
    """
    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    
#     pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
#     pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    pseudoFeat, pseudoLabel = getPseudoIndeces(sets)
    
    idx = np.max(pseudoLabel) + 1
    cmat = np.zeros((idx, idx), dtype=np.int32)
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    kf = StratifiedKFold(pseudoLabel, n_folds=Nfolds, indices=True)
    
    cnt = 1
    
    predict = []
    testLbl = []
    testPos = []
    trainSets = []
    testSets = []
    selectionSet = []
    
    for train, test in kf:
        trainSets += [train]
        testSets += [test]
        print("processing fold no {0}/{1}".format(cnt, Nfolds))
        
        
        # create balanced training set
        cFeat = []
        for c in range(idx):
            abc = [sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in train \
                                                   if pseudoLabel[t] == c ]
#             for a in abc:
#                 print a.shape
            cFeat += [np.concatenate(abc)]
        
        
        maxSamples = min([a.shape[0] for a in cFeat])
        
        feats = []
        lbls= []
        selection = []
        for c in range(len(cFeat)):
            idces = np.random.permutation(np.arange(cFeat[c].shape[0]))[:maxSamples]
            feats += [cFeat[c][idces]]
            lbls += [[c] * maxSamples]
            selection += [idces]
            
                
        trainSet = np.concatenate(tuple(feats)) #data[train]
        selectionSet += [selection]
        trainLbl = np.concatenate(tuple(lbls)) #labels[train]
        
        
        # create test set from all samples in sets choosen for testing
        # (class imbalance does not matter)
        cFeat = []
        for c in range(idx):
            cFeat += [np.concatenate(tuple([sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in test \
                                                   if pseudoLabel[t] == c ]))]
        
        feats = []
        lbls= []
        for c in range(len(cFeat)):
            feats += [cFeat[c]]
            lbls += [[c] * cFeat[c].shape[0]]
            
                
        testSet = np.concatenate(tuple(feats)) #data[train]
        testLbl.append(np.concatenate(tuple(lbls))) #labels[train]
        
        
        # train classifier and test 
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        cmat += computeConfusionMatrix(predict[-1], testLbl[-1])
        cnt += 1
    
    return cmat, predict, trainSets, testSets, selectionSet

def crossValidateSectionSetsMIL(sets, classifier, additionalFrames=100, negativeSet=1, Nfolds=2, verbose=True):
    """
    
    Takes only one-vs-all type of multi-class
    
    Args:
        negativeSets (int):
                set with only negative examples
        data (list of np.arrays)
                list of feature matrices, one for each class
        labels (list of np.arrays)
                list of labels corresponding feature matrices in data
        sets (list of [begin (int), end (int)])
                list of indeces of sets of groups of samples in feature
                matrices
                
                
    """
    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    
#     pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
#     pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    pseudoFeat, pseudoLabel = getPseudoIndeces(sets)
    
    idx = np.max(pseudoLabel) + 1
    cmat = np.zeros((idx, idx))
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    kf = StratifiedKFold(pseudoLabel, n_folds=Nfolds, indices=True)
    
    cnt = 1
    
    predict = []
    testLbl = []
    testPos = []
    trainSets = []
    testSets = []
    selectionSet = []
    
    for train, test in kf:
        trainSets += [train]
        testSets += [test]
        if verbose:
            print("processing fold no {0}/{1}".format(cnt, Nfolds))
        
        
        # create balanced training set
        cFeat = []
        for c in range(idx):
            abc = [sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in train \
                                                   if pseudoLabel[t] == c ]
#             for a in abc:
#                 print a.shape
            cFeat += [np.concatenate(abc)]
        
        
        maxSamples = min([a.shape[0] for a in cFeat])
        
        feats = []
        lbls= []
        selection = []
        for c in range(len(cFeat)):
            idces = np.random.permutation(np.arange(cFeat[c].shape[0]))[:maxSamples]
            feats += [cFeat[c][idces]]
            lbls += [[c] * maxSamples]
            selection += [idces]
            
                
        trainSet = np.concatenate(tuple(feats)) #data[train]
        selectionSet += [selection]
        trainLbl = np.concatenate(tuple(lbls)) #labels[train]
        
        
        # create test set from all samples in sets choosen for testing
        # (class imbalance does not matter)
        cFeat = []
        for c in range(idx):
            if c == negativeSet:
                cFeat += [np.concatenate(tuple([sets[pseudoLabel[t]][pseudoFeat[t]] \
                                                   for t in test \
                                                       if pseudoLabel[t] == c ]))]
            else:
                pI = lambda bag: extractPositiveInstances(bag, additionalFrames)
                cFeat += [np.concatenate(tuple([pI(sets[pseudoLabel[t]][pseudoFeat[t]]) \
                                                   for t in test \
                                                       if pseudoLabel[t] == c ]))]
                
        
        feats = []
        lbls= []
        for c in range(len(cFeat)):
            feats += [cFeat[c]]
            lbls += [[c] * cFeat[c].shape[0]]
            
                
        testSet = np.concatenate(tuple(feats)) #data[train]
        testLbl.append(np.concatenate(tuple(lbls))) #labels[train]
        
        
        # train classifier and test 
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        curCMAT = computeConfusionMatrix(np.int32(predict[-1] > 0), testLbl[-1])
        cmat += curCMAT
        if verbose:
            print curCMAT
        cnt += 1
    
    return cmat, predict, trainSets, testSets, selectionSet

def timeBiasedFold(pseudoLabel, aS, idx, behaviour):
    train = []
    test = []
    for i in range(max(pseudoLabel) + 1):
        vIndeces = np.where(pseudoLabel == i)[0]
        if i == behaviour:
            train += list(vIndeces[:idx])
            test += list(vIndeces[idx:])
        else:
            inces = np.random.permutation(vIndeces)
            train += list(inces[:len(inces)/2])
            test += list(inces[len(inces)/2:])
                    
    return [[train, test]]

def validateSectionSetsIncremental(sets, classifier, aS, timePos, behaviour=0):
    """
    Args:
        data (list of np.arrays)
                list of feature matrices, one for each class
        labels (list of np.arrays)
                list of labels corresponding feature matrices in data
        sets (list of [begin (int), end (int)])
                list of indeces of sets of groups of samples in feature
                matrices
                
                
    """
    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    
#     pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
#     pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    pseudoFeat, pseudoLabel = lE.getPseudoIndeces(sets)
    
    idx = np.max(pseudoLabel) + 1
    cmat = np.zeros((idx, idx), dtype=np.int32)
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    kf = timeBiasedFold(pseudoLabel, aS, timePos, behaviour)
    
    cnt = 1
    
    predict = []
    testLbl = []
    testPos = []
    trainSets = []
    testSets = []
    selectionSet = []
    
    for train, test in kf:
        trainSets += [train]
        testSets += [test]
        
        
        # create balanced training set
        cFeat = []
        for c in range(idx):
            abc = [sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in train \
                                                   if pseudoLabel[t] == c ]
#             for a in abc:
#                 print a.shape
            if abc:
                cFeat += [np.concatenate(abc)]
        
        
        maxSamples = min([a.shape[0] for a in cFeat])
        
        feats = []
        lbls= []
        selection = []
        for c in range(len(cFeat)):
            idces = np.random.permutation(np.arange(cFeat[c].shape[0]))[:maxSamples]
            feats += [cFeat[c][idces]]
            lbls += [[c] * maxSamples]
            selection += [idces]
            
                
        trainSet = np.concatenate(tuple(feats)) #data[train]
        selectionSet += [selection]
        trainLbl = np.concatenate(tuple(lbls)) #labels[train]
        
        
        # create test set from all samples in sets choosen for testing
        # (class imbalance does not matter)
        cFeat = []
        for c in range(idx):
            cFeat += [np.concatenate(tuple([sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in test \
                                                   if pseudoLabel[t] == c ]))]
        
        feats = []
        lbls= []
        for c in range(len(cFeat)):
            feats += [cFeat[c]]
            lbls += [[c] * cFeat[c].shape[0]]
            
                
        testSet = np.concatenate(tuple(feats)) #data[train]
        testLbl.append(np.concatenate(tuple(lbls))) #labels[train]
        
        
        # train classifier and test 
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        cmat += computeConfusionMatrix(predict[-1], testLbl[-1])
        cnt += 1
    
    return cmat, predict, trainSets, testSets, selectionSet


def timeBiasedSplit(pseudoLabel, aS, idx, behaviour):
    normalSet = []
    testOnlySet = []
    for i in range(max(pseudoLabel) + 1):
        vIndeces = np.where(pseudoLabel == i)[0]
        if i == behaviour:
            normalSet += list(vIndeces[:idx])
            testOnlySet += list(vIndeces[idx:])
        else:
            normalSet += list(vIndeces)
                    
    return normalSet, testOnlySet


def crossValidateSectionSetsIncremental(sets, classifier, aS, timePos, behaviour=0, nFolds=10):
    """
    Args:
        data (list of np.arrays)
                list of feature matrices, one for each class
        labels (list of np.arrays)
                list of labels corresponding feature matrices in data
        sets (list of [begin (int), end (int)])
                list of indeces of sets of groups of samples in feature
                matrices
                
                
    """
    
    # construct pseudo feature matrix that in reality contains 
    # indices to sections in the sets, which will then be used
    # to sample from the samples within the choosen sections
    # to create unbiased training and test set
    
#     pseudoFeat = np.asarray([f for s in sets for f in range(len(s))])
#     pseudoLabel = np.asarray([i for i in range(len(sets)) for f in range(len(sets[i]))])
    
    pseudoFeat, pseudoLabel = lE.getPseudoIndeces(sets)
    
    idx = np.max(pseudoLabel) + 1
    cmat = np.zeros((idx, idx), dtype=np.int32)
    
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    normalSet, testOnlySet = timeBiasedSplit(pseudoLabel, aS, timePos, behaviour)
    print len(testOnlySet)
    
    testParts = []
    kf = None
    #kf = KFold(len(labels), n_folds=Nfolds, indices=True)
    if timePos > nFolds:
        kf = StratifiedKFold(pseudoLabel[normalSet], n_folds=nFolds, indices=True)
        # distribute test only part into test sets of folds
        testParts = list(partition(np.random.permutation(testOnlySet), nFolds))
    else:
        kf = StratifiedKFold(pseudoLabel[normalSet], n_folds=timePos, indices=True)        
        # distribute test only part into test sets of folds
        testParts = list(partition(np.random.permutation(testOnlySet), timePos))
    
    
        
    # rest is business as usual
    
    cnt = 0
    
    predict = []
    testLbl = []
    testPos = []
    trainSets = []
    testSets = []
    selectionSet = []
    
    for train, test in kf:
        test = np.asarray(normalSet)[np.asarray(test)]
        train = np.asarray(normalSet)[np.asarray(train)]
        if len(testParts) > cnt:
            test = np.append(test,  testParts[cnt])
            
        trainSets += [train]
        testSets += [test]
        cnt += 1
        
        
        # create balanced training set
        cFeat = []
        for c in range(idx):
            abc = [sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in train \
                                                   if pseudoLabel[t] == c ]
#             for a in abc:
#                 print a.shape
            if abc:
                cFeat += [np.concatenate(abc)]
        
        
        maxSamples = min([a.shape[0] for a in cFeat])
        
        feats = []
        lbls= []
        selection = []
        for c in range(len(cFeat)):
            idces = np.random.permutation(np.arange(cFeat[c].shape[0]))[:maxSamples]
            feats += [cFeat[c][idces]]
            lbls += [[c] * maxSamples]
            selection += [idces]
            
                
        trainSet = np.concatenate(tuple(feats)) #data[train]
        selectionSet += [selection]
        trainLbl = np.concatenate(tuple(lbls)) #labels[train]
        
        
        # create test set from all samples in sets choosen for testing
        # (class imbalance does not matter)
        cFeat = []
        for c in range(idx):
            normalFeatSet = [sets[pseudoLabel[t]][pseudoFeat[t]] \
                                               for t in test \
                                                   if pseudoLabel[t] == c ]
#             testOnlyFeatSet = [sets[pseudoLabel[t]][pseudoFeat[t]] \
#                                                for t in testOnlySet \
#                                                    if pseudoLabel[t] == c ]
#             cFeat += [np.concatenate(tuple(normalFeatSet + testOnlyFeatSet))]
            cFeat += [np.concatenate(tuple(normalFeatSet))]
        
        feats = []
        lbls= []
        for c in range(len(cFeat)):
            feats += [cFeat[c]]
            lbls += [[c] * cFeat[c].shape[0]]
            
                
        testSet = np.concatenate(tuple(feats)) #data[train]
        testLbl.append(np.concatenate(tuple(lbls))) #labels[train]
        
        
        # train classifier and test 
        wclf = classifier
        wclf.fit(trainSet, trainLbl)
        
        predict.append(wclf.predict(testSet))
        
        cmat += computeConfusionMatrix(predict[-1], testLbl[-1])
    
    return cmat, predict, trainSets, testSets, selectionSet

def reduceMulticlassCMat(cmat, c):
    """
    Args:
        cmat (numpy array):
                multi-class confision matrix
        c (int):
                active class 
    """
    redCMat = np.zeros((2,2))
    redCMat[0,0] = cmat[c,c]
    redCMat[0,1] = np.sum(cmat[c,:]) - cmat[c,c]
    redCMat[1,1] = np.sum(cmat.diagonal()) - cmat[c,c]
    redCMat[1,0] = np.sum(cmat.flatten()) - np.sum(redCMat.flatten())
    
    return redCMat


def calcBaseStatsFromCMat(cmat):
    """
    
    Returns:
        accuracy, presicion, recall, f1Score
        of confusion matrix cmat
    """
    accuracy = np.sum(cmat.diagonal()) / np.sum(cmat.flatten() + 0.0)
    precision = cmat[0,0] / (cmat[0,0] + cmat[0,1] + 0.0)
    recall = cmat[0,0] / (cmat[0,0] + cmat[1,0] + 0.0)
    f1Score = 2 * ((precision * recall) / (precision + recall + 0.0))
    
    return accuracy, precision, recall, f1Score

def plotCmatsPerformance(cmats):    
    stats = []
    for i in range(len(cmats)):
        stats += [[]]
        for cmat in cmats[i]:
            stats[-1] += [calcBaseStatsFromCMat(reduceMulticlassCMat(cmat,i))]
            
    for i in range(len(stats)):
        fig = plt.figure(figsize=(20,10))
        axes = fig.add_subplot(111)
        plt.plot(np.arange(len(stats[i])), [s[0] for s in stats[i]], 
                                                            color='red', 
                                                            label='accuracy')
        plt.plot(np.arange(len(stats[i])), [s[3] for s in stats[i]], 
                                                            color='blue', 
                                                            label='F1 score')
        axes.set_ylim([0,1])
        plt.title("class {i}".format(i=i))
        plt.legend()
    
def saveCMatsToJson(cmats, fn):
    cmatLst = [[a.tolist() for a in b] for b in cmats]
    with open(fn, 'w') as f:
        json.dump(cmatLst,f, indent=4)
    
def loadJsonToCMats(fn):
    with open(fn, 'r') as f:
        cmatLst = json.load(f)
    cmats = [[np.asarray(a) for a in b] for b in cmatLst]
    return cmats    


def getMissClassified(predict, labels, pathList, cl):
    out = []
    
    for i in range(len(pathList)):
        if predict[i] != labels[i] and labels[i] == cl:
            out.append(pathList[i])
            
    return out


def extractContinuousAnnotationSections(aF, fileList):
    """
    Args:
    
    
    Returns:
        list of list with [begin, end] of sections of continuous appearances
        of a label.
        `begin` and `end` are as it is required to generate a valid slice
        with range(begin, end)

    """
    sect = []#[] for i in range(len(aF))]
    for b in range(len(aF)):
        sect += [[]]
        for v in range(len(aF[b])):
            vSec = []
            if not aF[b][v]:
                sect[b] += [vSec]
                continue
            start = 0
            end = None
            for a in range(1, len(aF[b][v])):
                if aF[b][v][a-1][0] ==  aF[b][v][a][0]:
                    if aF[b][v][a-1][1] ==  aF[b][v][a][1] - 1:
                        continue                        
                    else:
                        end = a                        
                elif aF[b][v][a][1] == 0:
                    
                    if fileList.index(aF[b][v][a][0]) \
                    == fileList.index(aF[b][v][a - 1][0]) + 1:
                        pos = np.load(aF[b][v][a - 1][0])
                        if pos.shape[0] == aF[b][v][a - 1][1] + 1:
                            print aF[b][v][a - 1]
                            continue
                        else:
                            end = a
                    else:
                        end = a
                else:
                    end = a
                    
                if end is not None:
                    vSec += [[start, end]]
                    start = a
                    end = None                    
                    
            vSec += [[start, a + 1]]        
            sect[b] += [vSec]
            
    return sect


def extendAnnotationSections(aF, sections, fileList, additionalFrames=0):
    """
    Args:
    
    
    Returns:
        list of list with [begin, end] of sections of continuous appearances
        of a label.
        `begin` and `end` are as it is required to generate a valid slice
        with range(begin, end)

    """
    aS = []
    
    for a in range(len(sections)):
        classSects = []
        for v in range(len(sections[a])):
            for s in range(len(sections[a][v])):
                frameList = deque()
                start = copy.copy(aF[a][v][sections[a][v][s][0]])
                end = copy.copy(aF[a][v][sections[a][v][s][1] - 1])
                
                remainingFrames = additionalFrames
                
                while remainingFrames > 0:                 
                    remainingFrames -= 1
                    start[1] -= 1                    
                    if start[1] < 0:
                        filePos = fileList.index(start[0])
                        if filePos < 1:
                            cfg.log.warning(\
                            'tried to include frames previous to the first frame {0} {1} {2}'.format(a,v,s))
                            break
                        start[0] = fileList[filePos - 1]
                        start[1] = np.load(start[0]).shape[0] - 1
                        
                    frameList.appendleft(copy.copy(start) + [v])   

                
                for i in range(*sections[a][v][s]):
                    frameList.append(copy.copy(aF[a][v][i]) + [v])
                
                curLength = np.load(end[0]).shape[0]
                remainingFrames = additionalFrames
                
                
                while remainingFrames > 0:               
                    remainingFrames -= 1
                    end[1] += 1
                    
                    if end[1] >= curLength:
                        filePos = fileList.index(end[0])
                        if filePos >= len(fileList) - 1:
                            cfg.log.warning(\
                            'tried to include frames after to the last frame {0} {1} {2}'.format(a,v,s))
                            break
                        end[0] = fileList[filePos + 1]
                        curLength = np.load(end[0]).shape[0]
                        end[1] = 0
                        
                    frameList.append(copy.copy(end) + [v])     
                        
                if len(frameList) == 0:
                    print a,v,sections[a][v]
                    
                classSects += [frameList]
                
        aS += [classSects]
                            
    return aS


def flattenAnnotationSections(sect):
    out = []
    
    for a in range(len(sect)):
        aSec = []
        offSet = 0
        for v in range(len(sect[a])):
            for i in range(len(sect[a][v])):
                aSec += [[sect[a][v][i][0] + offSet, sect[a][v][i][1] + offSet]]
            
            offSet = aSec[-1][1]
            
        out += [aSec]
        
    return out

def providePosList(path):
    fileList  = []
    posList = []
    print("scaning files...")
    for root,  dirs,  files in os.walk(path):
        for f in files:
            if f.endswith('pos.npy'):
                path = root + '/' + f
                fileList.append(path)
                
    fileList = sorted(fileList)
    print("scaning files done")
    return fileList

def flattenAnnotatedFrames(aF):
    flattenedAF = []
    for a in aF:     
        aList = []
        for v in range(len(a)):
            aList += [i + [v] for i in a[v]]
        flattenedAF += [aList]
        
    return flattenedAF

def sortKey(x):
    op = operator.itemgetter(0,2)
    return op(x[0])

def saveMILData(data, additionalFrames=100, negBags=50):
    """
    data[0] is the positive class
    data[1] is the negative class    
    
    output format will be
    
    instance name (just a running integer), bag name (ID), instance label (0/1), features
    """
    aF = additionalFrames
    
    id = 0
    bagList = []
    # process posivite bags
    for bP in range(len(data[0])):
        negIID1 = np.arange(id, id+aF).reshape(aF,1)
        id += aF
        bagID1 = np.zeros((aF,1)) + bP   
        lbl = np.zeros((aF,1))
        negFeat1 = data[0][bP][:aF]    
        negPt1 = np.hstack((negIID1, bagID1, lbl, negFeat1))
    
        noPos = data[0][bP].shape[0] - 2 * aF
        posID = np.arange(id, id + noPos).reshape(noPos,1)
        id += noPos
        bagID2 = np.zeros((noPos,1)) + bP    
        lbl = np.ones((noPos,1))
        posFeat1 = data[0][bP][aF:-aF]
        posPt = np.hstack((posID, bagID2, lbl, posFeat1))
        
        negIID2 = np.arange(id, id+aF).reshape(aF,1)
        id += aF
        bagID3 = np.zeros((aF,1)) + bP
        lbl =  np.zeros((aF,1))
        negFeat2 = data[0][bP][-aF:] 
        negPt2 = np.hstack((negIID2,bagID3, lbl, negFeat2))
        
        bagList += [np.vstack((negPt1, posPt, negPt2))]
        
        
    bagID = bP
    for bag in partition(data[1], negBags):
        noInst = len(bag)
        
        ids = np.arange(id, id+noInst).reshape(noInst,1)
        id += noInst
        
        bagIDs = np.zeros((noInst,1)) + bagID
        bagID += 1
         
        lbl =  np.zeros((noInst,1))
        
        feats = np.vstack(bag)
        
        bagList += [np.hstack((ids, bagIDs, lbl, feats))]
        
        
    return np.vstack(bagList)

def extractPositiveInstances(bag, additionalFrames=100):
    return bag[additionalFrames:-additionalFrames]
        
        
def partition ( lst, n ):
    base = np.floor(len(lst) / n)
    add = np.mod(len(lst), n)
    cnt = 0
    for i in range(0, len(lst)):
        oldCnt = cnt
        if i < add:
            cnt += base + 1
        else:
            cnt += base
        
        yield lst[oldCnt:cnt]
    
    
def saveConfusionMatrix(predict, testSet, aS, baseDir='/tmp/cmat'):
    folder = lambda l,p: os.path.join(baseDir, '{0}-{1}'.format(l,p))    
    vE = videoExplorer.videoExplorer()
    
    pseudoFeat, pseudoLabel = getPseudoIndeces(aS)
    
    size = max(pseudoLabel) + 1
    cmat = np.zeros((size, size))
    
    for i in range(size):
        for k in range(size):
            if not os.path.exists(folder(i,k)):
                os.makedirs(folder(i,k))        
             
    
    for test in range(len(testSet)):
        k = 0
        for t in testSet[test]:
            l = pseudoLabel[t]
            section = aS[l][pseudoFeat[t]]
            for f in section:
                basePath = f[0].split('.pos.npy')[0]
                frameNo = f[1]
                vialNo = f[2]
                p = predict[test][k]
             
                fn = '{base}-v{vial}-f{frame}.png'.format(\
                        base=os.path.split(basePath)[-1],
                        vial=vialNo,
                        frame=frameNo)
                savePath = os.path.join(folder(l,p), fn)
                
                videoPath = '{base}.v{vial}.avi'.format(\
                        base=basePath,
                        vial=vialNo)
                
                saveFrameTo(vE, videoPath, frameNo, savePath, 'RGB')
                
                
                cmat[l, p] += 1
                
                k += 1
        
    return cmat

def saveFrameTo(self, videoPath, frameNo, filePath, frameMode='L'):
    import scipy
    frames = []
    self.vs = VideoStream(videoPath, frame_mode=frameMode)      
    for i in range(-1,2):
        try:
            frames += [np.rot90(self.vs.get_frame_no(frameNo + i).ndarray())]
        except:
            pass
        
    frame = np.concatenate(tuple(frames), axis=1)    
    scipy.misc.imsave(filePath, frame)       
    
def gridSearch(feat, cfr, classSets, nFolds, noAddFeat, additionalFrames=1000): 
    aF = additionalFrames
    for addFeat in noAddFeat:
        for cfr in classifiers:
            for k in cfr['kernel']:
                for gamma in cfr['gamma']:
                    for c in cfr['C']:
                        print("computing {0} with {1} kernel and C={2} and gamma={3} using {4} additional negative instances".format(cfr['classifier'], k, c, gamma, addFeat))                
                        classifier = cfr['classifier'](kernel=k, C=c, gamma=gamma, 
                                                       verbose=False)
                        for cs in classSets:
                            print("training for class {0}").format(cs)
                            milFeat = [[extractPositiveInstances(f, aF - addFeat)\
                                             for f in feat[cs[0]]], feat[cs[1]]]
                            t = time.time()
                            cmat, predict, trainSet, testSet, selectionSet = \
                                    crossValidateSectionSetsMIL(milFeat, 
                                                                classifier, 
                                                        additionalFrames=addFeat, 
                                                                Nfolds=nFolds, 
                                                                verbose=False)
                            runningTime = time.time() - t
                            result = {'cmat':cmat.tolist(), 
                                      'predict': [p.tolist() for p in predict],
                                      'trainSet': [t.tolist() for t in trainSet],
                                      'testSet': [t.tolist() for t in testSet],
                                      'selectionSet': [[[a.tolist()] for a in s] \
                                                            for s in selectionSet],
                                      'runningTime': runningTime,
                                      'kernel':k, 
                                      'C':c, 
                                      'gamma':gamma, 
                                      'classifier':str(cfr['classifier'])}
                            
                            acc = float(np.sum(cmat.diagonal()) / 
                                        np.sum(cmat.flatten()))
                            fn = 'results/{classifier} - {kernel} - C{C} - g{g} - {classes}[{add}] - acc {acc} - time {time} - folds {nFolds}.json'.format(\
                                    classifier=str(cfr['classifier']), 
                                    kernel=k, 
                                    C=c, 
                                    g=gamma, 
                                    acc=acc, 
                                    time=runningTime, 
                                    classes=cs, 
                                    add=addFeat, 
                                    nFolds=nFolds)
                            with open(fn, 'w') as f:
                                json.dump(result, f)
                            

if __name__ == "__main__":
    dataFolder = '/run/media/peter/Elements/peter/data/tmp-20130506'
    behaviour = "struggling"
    annotator = "peter"
    
    t = time.time()
    aF = []
    aF += [extractAnnotatedFrames(behaviour="falling")]
    aF += [extractAnnotatedFrames(behaviour="dropping")]
    aF += [extractAnnotatedFrames(behaviour="struggling")]
    aF += [extractNegativeAnnotatedFrames(behaviours=["falling", 
                                                      "dropping",
                                                      "struggling"])]
    cfg.log.info("finished in {0} sec".format(time.time() - t)) 
    
    fileList = providePosList(dataFolder)
    
    sect = extractContinuousAnnotationSections(aF, fileList)
    
    aS = []
    additionalFrames = 1000
    s = sect[0:3]
    aS += extendAnnotationSections(aF[0:3], s, fileList, additionalFrames)
    aS += extendAnnotationSections([aF[3]], [sect[3]], fileList, 0)
    aS[3] = sorted(aS[3], key=sortKey)
    
    t = time.time()
    # ending = ['feat.hog3d', 'feat.hog3d-xy2-t0.5', 'feat.hog3d-xy1-t0.25', 'feat.hog3d-xy2-t0.25', 'feat.hog-8', 'feat.position']
    ending = ['feat.hog3d', 'feat.position']
    # ending = ['feat.hog3d-xy2-t0.5']
    feat = createFeatureVectorFromAnnotationSections(aS, ending=ending)
    cfg.log.info("finished in {0} sec".format(time.time() - t)) 
    
    milData = saveMILData([feat[0], feat[3]], additionalFrames=additionalFrames)
    
    # train standard classifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn import grid_search
    
    c = RandomForestClassifier(n_jobs=6, n_estimators=160, max_depth=60)
    
    nonMilFeat =  [[i[additionalFrames:-additionalFrames] for i in feat[0]], feat[3]]    
    cmat, predict, trainSet, testSet, selectionSet = crossValidateSectionSets(nonMilFeat, c,  Nfolds=10)
    print cmat
    
    # train standard SVM
    from sklearn import svm
    c = svm.SVC(kernel='r', C=30.0)#, max_iter=100)
    
    nonMilFeat =  [[i[10:-10] for i in feat[0]], feat[3]]
    
    cmat, predict, trainSet, testSet, selectionSet = crossValidateSectionSets(nonMilFeat, c,  Nfolds=10)
    print cmat
    
    # MISVM
    import misvm

    c = misvm.MISVM(kernel='linear', C=1, max_iters=50)
    # c = misvm.MISVM(kernel='linear', C=1.0, max_iters=50)
    # c = misvm.sMIL(kernel='linear', C=1.0), max_iters=50)
    
    noAddFeat = 10
    selClass = 0
    milFeat = [[extractPositiveInstances(f, 1000 - noAddFeat) for f in feat[selClass]], feat[3]]
    cmat, predict, trainSet, testSet, selectionSet = crossValidateSectionSetsMIL(milFeat, c, additionalFrames=noAddFeat, Nfolds=10)
    print cmat
    
    # Prepare gridsearch
    # make deque to list
    aSList = [[list(b) for b in a] for a in aS]
    
    # ensure int everywhere
    aSList = [[[[c[0], int(c[1]), c[2]] for c in b] for b in a] for a in aSList]
    
    with open('aS.json', 'w') as f:
        json.dump(aSList, f)
        
    MISVM = {'classifier':ms.MISVM, 'kernel':['linear'], 
             'C':[10**(-3), 10**(-2),10**(-1), 10**0, 10**2, 10**3], 
             'gamma':[0]}
    sMIL = {'classifier':ms.sMIL, 
            'kernel':['linear'], 
             'C':[10**(-3), 10**(-2),10**(-1), 10**0, 10**2, 10**3], 
             'gamma':[0]}
    sbMIL = {'classifier':ms.sbMIL, 
             'kernel':['linear'], 
             'C':[10**(-3), 10**(-2),10**(-1), 10**0, 10**2, 10**3], 
             'gamma':[0]}
    stMIL = {'classifier':ms.stMIL, 
             'kernel':['linear'], 
             'C':[10**(-3), 10**(-2),10**(-1), 10**0, 10**2, 10**3], 
             'gamma':[0]}
    
    classifiers = [MISVM, sMIL, sbMIL, stMIL]
    classSets = [[0,3],
                 [1,3],
                 [2,3]]
    
    
    noAddFeat = [10, 100, 500, 1000]
    nFolds = 2
    
    gridSearch(feat, classifiers, classSets, nFolds, noAddFeat, additionalFrames)
    
    
    
