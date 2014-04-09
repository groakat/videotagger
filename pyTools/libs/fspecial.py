import scipy


def fspecial(type,**args):
    '''
    Create predefined 2-D filter. I refers to matlab fspecial.
    Now it's just implement gaussian filter-kernel.
    specified type. Possible values for TYPE are:
     'average'   averaging filter
     'disk'      circular averaging filter
     'gaussian'  Gaussian lowpass filter
     'laplacian' filter approximating the 2-D Laplacian operator
     'log'       Laplacian of Gaussian filter
     'motion'    motion filter
     'prewitt'   Prewitt horizontal edge-emphasizing filter
     'sobel'     Sobel horizontal edge-emphasizing filter
     'unsharp'   unsharp contrast enhancement filter


       Depending on TYPE, FSPECIAL may take additional parameters
       which you can supply.  These parameters all have default
       values. 
    
       H = FSPECIAL('average',HSIZE) returns an averaging filter H of size
       HSIZE. HSIZE can be a vector specifying the number of rows and columns in
       H or a scalar, in which case H is a square matrix.
       The default HSIZE is [3 3].
    
       H = FSPECIAL('disk',RADIUS) returns a circular averaging filter
       (pillbox) within the square matrix of side 2*RADIUS+1.
       The default RADIUS is 5.
    
       H = FSPECIAL('gaussian',HSIZE,SIGMA) returns a rotationally
       symmetric Gaussian lowpass filter  of size HSIZE with standard
       deviation SIGMA (positive). HSIZE can be a vector specifying the
       number of rows and columns in H or a scalar, in which case H is a
       square matrix.
       The default HSIZE is [3 3], the default SIGMA is 0.5.
    
       H = FSPECIAL('laplacian',ALPHA) returns a 3-by-3 filter
       approximating the shape of the two-dimensional Laplacian
       operator. The parameter ALPHA controls the shape of the
       Laplacian and must be in the range 0.0 to 1.0.
       The default ALPHA is 0.2.
    
       H = FSPECIAL('log',HSIZE,SIGMA) returns a rotationally symmetric
       Laplacian of Gaussian filter of size HSIZE with standard deviation
       SIGMA (positive). HSIZE can be a vector specifying the number of rows
       and columns in H or a scalar, in which case H is a square matrix.
       The default HSIZE is [5 5], the default SIGMA is 0.5.
    
       H = FSPECIAL('motion',LEN,THETA) returns a filter to approximate, once
       convolved with an image, the linear motion of a camera by LEN pixels,
       with an angle of THETA degrees in a counter-clockwise direction. The
       filter becomes a vector for horizontal and vertical motions.  The
       default LEN is 9, the default THETA is 0, which corresponds to a
       horizontal motion of 9 pixels.
    
       H = FSPECIAL('prewitt') returns 3-by-3 filter that emphasizes
       horizontal edges by approximating a vertical gradient. If you need to
       emphasize vertical edges, transpose the filter H: H'.
    
           [1 1 1;0 0 0;-1 -1 -1].
    
       H = FSPECIAL('sobel') returns 3-by-3 filter that emphasizes
       horizontal edges utilizing the smoothing effect by approximating a
       vertical gradient. If you need to emphasize vertical edges, transpose
       the filter H: H'.
    
           [1 2 1;0 0 0;-1 -2 -1].
    
       H = FSPECIAL('unsharp',ALPHA) returns a 3-by-3 unsharp contrast
       enhancement filter. FSPECIAL creates the unsharp filter from the
       negative of the Laplacian filter with parameter ALPHA. ALPHA controls
       the shape of the Laplacian and must be in the range 0.0 to 1.0.
       The default ALPHA is 0.2.
    
       Class Support
       -------------
       H is of class double.
    
       Example
       -------
          I = imread('cameraman.tif');
          subplot(2,2,1);imshow(I);title('Original Image'); 
          H = fspecial('motion',20,45);
          MotionBlur = imfilter(I,H,'replicate');
          subplot(2,2,2);imshow(MotionBlur);title('Motion Blurred Image');
          H = fspecial('disk',10);
          blurred = imfilter(I,H,'replicate');
          subplot(2,2,3);imshow(blurred);title('Blurred Image');
          H = fspecial('unsharp');
          sharpened = imfilter(I,H,'replicate');
          subplot(2,2,4);imshow(sharpened);title('Sharpened Image');
        @see: matlab fspercial.m
        @copyright: 1993-2005 The MathWorks, Inc. 
        @author: Qiu wenfeng rewrite
    '''
    if type=='gaussian':
        
        siz = [(args['N']-1)/2, (args['N']-1)/2]
        std = args['Sigma']
        
        y, x = scipy.mgrid[-siz[0]:siz[0]+1, -siz[1]:siz[1]+1]
        
        arg = -(x*x+y*y)/(2*std*std)
        h = scipy.exp(arg)
        h[h<scipy.finfo(float).eps*h.max(0)]=0
        sumh = h.sum()
        
        if sumh<>0:
            h=h/sumh
            
        return h
    return []


if __name__=="__main__":
    print fspecial('gaussian', N=15, Sigma=1.5)