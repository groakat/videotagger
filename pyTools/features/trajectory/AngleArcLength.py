import numpy as np
import scipy.signal as signal
from scipy import interpolate
import copy
import matplotlib.pyplot as plt


def computeRawAAL(rawPosVector, cMass=False, groverFormula=False):
    """
    Computation of angle-arc-length signature of a trajectory
    
    """
    
    rpv = rawPosVector
    kernel = np.array([-1, 1])
    if cMass:
        pcMass = np.sum(rpv, axis=0) / np.float(rpv.shape[1])
    else:
        M_ref = np.array([1,0, 0]).transpose()
#     M_ref = np.array([1,0])
    
    dx = signal.convolve(rpv[:, 0], kernel, 'same')
    dy = signal.convolve(rpv[:, 1], kernel, 'same')
    # dirty fix of large values in the first elements
    dx[0] = dx[1]
    dy[0] = dy[1]
    
    M_t = np.array([dx, dy]).transpose()
    
    alpha = []
    sign = 0
    for i in range(M_t.shape[0]):    
        if cMass:
            if i == 0:                
                M_ref = np.append(rpv[i, :] - pcMass, 0)
            else:
                M_ref = np.append(rpv[i-1, :] - pcMass, 0)
            
        m_t = np.append(M_t[i, :], 0)
        if groverFormula:
            inner = np.linalg.norm(np.cross(M_t[i, :], M_ref))
            outer = np.dot(m_t, M_ref)
            alpha += [np.arctan2(inner, outer)]
        else:
            dot = np.dot(m_t, M_ref)
            deNom = np.linalg.norm(m_t) * np.linalg.norm(M_ref)
            sign = 0
            if np.cross(m_t, M_ref)[2] >= 0:
                sign = 1
            else:
                sign = -1
            
            if deNom == 0:
                # no movement
                alpha += [0]
            else:
                alpha += [sign * np.arccos(dot / deNom)]

    M = np.add.accumulate(np.sqrt((M_t[:, 0] - M_t[:, 1])**2))
    
    
    return np.array([alpha, M]).transpose()

    
def normalizeAAL(AALvec, step=0.5):
    """
    Arc length normalization with splines
    """
    tck = interpolate.splrep(AALvec[:,1], AALvec[:,0], s=0, k=1)#,s=0)
    xnew = np.arange(0, AALvec[-1,1], step)
    ynew = interpolate.splev(xnew,tck,der=0)
    
    return np.array([ynew, xnew]).transpose()


def rotateMatrix(mat, theta):
    """
    Simple 2D rotation
    """
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])
        
    return np.dot(R, mat)


def iterativeNormalization(AALvec, k=5):
    """
    Normalizes angles of raw AAL vector
    """
    n = len(AALvec)
    seqNorm = copy.copy(AALvec[:,0])
    
    for i in range(k):
#         if argValue
        # subtract mean value
        avgValue = np.mean(seqNorm)
        seqNorm -= avgValue
        
        # wrap points in range [-pi, pi]
        for j in range(n):
            if seqNorm[j] < -np.pi:
                seqNorm[j] = 2 * np.pi + seqNorm[j]
            if seqNorm[j] > np.pi:
                seqNorm[j] = -2 * np.pi + seqNorm[j]
                
    return np.array([seqNorm, AALvec[:,1]]).transpose()

def findAALfitPython(vecA, vecB, theta, delta, alpha=1):
    """
    Args:
        vecA: normalized AAL vector, shorter sequence (1..n)
        vecB: normalized AAL vector, longer sequence (1..m)
        n << m
        
        theta: threshold in radians for the two vectors to allign
        delta: gap penalty
        alpha: matching score 
    
    Return:
        T: weight matrix 
        trace: alignment vector
        
    Note:
    Implementation of 
    2009 - Grover, Tavare - Finding behavioral motifs in fly trajectories
    """
    

    
    
    n = vecA.shape[0]
    m = vecB.shape[0]
    T = np.zeros((n, m))
            
    for i in range(1, n):
        for j in range(1, m):
            diff = np.abs(vecA[i][0] - vecB[j][0])            
            if diff < theta:
                a = alpha
            else:
                a = -diff
            
    
            T[i,j] = np.max([T[i-1, j-1] + a,
                             T[i-1, j] - delta,
                             T[i, j-1] - delta])
            
            
            
    """ backtrace """
    trace = np.zeros((m,), dtype=np.int)
    trace[-1] = np.argmax(T[:,-1])
    for j in range(m-2, -1, -1):
        trace[j] = np.argmax(T[:, j])
    
    return T, trace


import scipy.weave

def findAALfit(vecA, vecB, theta, delta, alpha=1):
    """
    Args:
        vecA: normalized AAL vector, shorter sequence (1..n)
        vecB: normalized AAL vector, longer sequence (1..m)
        n << m
        
        theta: threshold in radians for the two vectors to allign
        delta: gap penalty
        alpha: matching score 
    
    Return:
        T: weight matrix 
        trace: alignment vector
        
    Note:
    Implementation of 
    2009 - Grover, Tavare - Finding behavioral motifs in fly trajectories
    """
    
    n = vecA.shape[0]
    m = vecB.shape[0]
    T = np.zeros((n, m))
    
    a = np.zeros((1, vecA.shape[0])) + vecA[:,0]

    diff = -np.abs(a.T - vecB[:,0])
    diff[diff > -theta] = alpha
        
    code = """
    float v0;
    float v1;
    float v2;
    float v3;
    float res;
    
    for (int i = 1; i < n; ++i){
        for (int j = 1; j < m; ++j){
            v0 = diff[i * m  + j];
            v1 = T[(i-1) * m + j-1] + v0;
            v2 = T[(i-1) * m + j] - delta;
            v3 = T[i * m     + j-1] - delta;
            
            res = v1;
            
            if (res < v2){
                res = v2;
            }
                
            if (res < v3){
                res = v3;
            }
            
            T[i * m + j] = res;
        }
    }
    """
            
    scipy.weave.inline(code, ['diff', 'T', 'delta', 'n', 'm'], 
                 extra_compile_args=['-O3'], compiler='gcc')
    
    """ backtrace """
    trace = np.zeros((m,), dtype=np.int)
    trace[-1] = np.argmax(T[:,-1])
    for j in range(m-2, -1, -1):
        trace[j] = np.argmax(T[:, j])
    
    return T, trace


def computeAAL(longVector, interpolationStep=0.2, cMass=True, 
               groverFormula=False):    
    AALvec = computeRawAAL(longVector, cMass=cMass, groverFormula=groverFormula)    
    itNormAAL = iterativeNormalization(AALvec)    
    normAALvec = normalizeAAL(itNormAAL, step=interpolationStep)    
    
    return AALvec, itNormAAL, normAALvec




if __name__ == "__main__":
    """ generate long sequence """
    rng = np.arange(0, 2 * np.pi, 0.1)
    longVector = np.concatenate(\
                            (np.array([rng, np.zeros(len(rng))]).T,
                            np.array([rng + rng[-1], np.sin(rng)]).T,
                            np.array([rng + rng[-1] * 2, np.zeros(len(rng))]).T),
                            axis=0)
    
    longVector += np.random.normal(scale=0.001, size=longVector.shape)

    AALvec, itNormAAL, normAALvec = computeAAL(longVector,
                                               cMass=True, 
                                               groverFormula=False)
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(AALvec[:,1], AALvec[:,0])
    plt.title("un-normalized AAL vector")
    plt.xlim(AALvec[0,1], AALvec[-1,1])
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(itNormAAL[:,1], itNormAAL[:,0])
    plt.title("iterative normalization AAL vector")
    plt.xlim(itNormAAL[0,1], itNormAAL[-1,1])
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(normAALvec[:,1], normAALvec[:,0])
    plt.title("normalized AAL vector")
    plt.xlim(normAALvec[0,1], normAALvec[-1,1])
    
    
    """ generate short sequence """
    rng = np.arange(0, 2 * np.pi, 0.2)
    shortVector = np.concatenate((np.array([rng, np.sin(rng)]).T,), axis=0)
    shortVector += np.random.normal(scale=0.001, size=shortVector.shape)

    AALvec2, itNormAAL2, normAALvec2 = computeAAL(shortVector, cMass=True, 
                                                  groverFormula=False)
    
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(AALvec2[:,1], AALvec2[:,0])
    plt.title("un-normalized AAL vector")
    plt.xlim(AALvec2[0,1], AALvec2[-1,1])
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(itNormAAL2[:,1], itNormAAL2[:,0])
    plt.title("iterative normalization AAL vector")
    plt.xlim(itNormAAL2[0,1], itNormAAL2[-1,1])
    
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    plt.plot(normAALvec2[:,1], normAALvec2[:,0])
    plt.title("normalized AAL vector")
    plt.xlim(normAALvec2[0,1], normAALvec2[-1,1])
    
    
    """ fit sequences """
    T, trace = findAALfit(normAALvec2, normAALvec, theta=0.25, delta=2.0, 
                          alpha=1)
    
    fig = plt.figure()
    plt.plot(normAALvec[:,1], trace)
    plt.title("sequence fit")
    plt.show()
    
    
    
    
    
    
    
    
    
    
    