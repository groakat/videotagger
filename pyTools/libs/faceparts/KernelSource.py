"""Kernel_Source.py
  
    Below are 4 GPU kernels for use with an nVidia CUDA enabled device that
    has compute capability 1.1 (i.e. floats are required instead of doubles).
    
    The kernels devine several different versions of the Histogram of Oriented
    Gradient feature extraction algorithm.   
   
   This code is released as-is, with no warranty of any kind, under the GNU Public License.
   
   Author: Ely M. Spears
   Date: DEC-5-2011
   
   http://people.seas.harvard.edu/~ely
"""

#####
# Every-pixel HoG kernel source
#####
def every_pixel_hog_kernel_source_code():
    every_pixel_hog_kernel_source = \
"""
#include <math.h>
#include <stdio.h>

__device__ int idx(int ii, int jj){
    return gridDim.x*blockDim.x*ii+jj;
}

__device__ int bin_number(float angle_val, int total_angles, int num_bins){ 

    float angle1;   
    float min_dist;
    float this_dist;
    int bin_indx;
    
    angle1 = 0.0f;
    min_dist = abs(angle_val - angle1);
    bin_indx = 0;
    
    for(int kk=1; kk < num_bins; kk++){
        angle1 = angle1 + float(total_angles)/float(num_bins);
        this_dist = abs(angle_val - angle1);
        if(this_dist < min_dist){
            min_dist = this_dist;
            bin_indx = kk;
        }
    }
    
    return bin_indx;
}

__device__ int hist_number(int ii, int jj, int window){

    int hist_num = 0;
    
    if(jj >= 0 && jj < window/3){ 
        if(ii >= 0 && ii < window/3){ 
            hist_num = 0;
        }
        else if(ii >= window/3 && ii < 2*window/3){
            hist_num = 3;
        }
        else if(ii >= 2*window/3 && ii < window){
            hist_num = 6;
        }
    }
    else if(jj >= window/3 && jj < 2*window/3){
        if(ii >= 0 && ii < window/3){ 
            hist_num = 1;
        }
        else if(ii >= window/3 && ii < 2*window/3){
            hist_num = 4;
        }
        else if(ii >= 2*window/3 && ii < window){
            hist_num = 7;
        }
    }
    else if(jj >= 2*window/3 && jj < window){
        if(ii >= 0 && ii < window/3){ 
            hist_num = 2;
        }
        else if(ii >= window/3 && ii < 2*window/3){
            hist_num = 5;
        }
        else if(ii >= 2*window/3 && ii < window){
            hist_num = 8;
        }
    }
    
    return hist_num;
}

__global__ void every_pixel_hog_kernel(float* input_image, int im_width, int im_height, float* gaussian_array, 
                                       float* x_gradient, float* y_gradient, float* gradient_mag, float* angles, float* output_array)
{    
    /////
    // Setup the thread indices and linear offset.
    /////
    int i = blockDim.y * blockIdx.y + threadIdx.y;
    int j = blockDim.x * blockIdx.x + threadIdx.x;
    int ang_limit = 180;
    int ang_bins = 9;
    float pi_val = 3.141592653589f; //91
    
    /////
    // Compute a Gaussian smoothing of the current pixel and save it into a new image array
    // Use sync threads to make sure everyone does the Gaussian smoothing before moving on.
    /////
    if( j > 1 && i > 1 && j < im_width-2 && i < im_height-2 ){
    
        // Hard-coded unit standard deviation 5-by-5 Gaussian smoothing filter.
        gaussian_array[idx(i,j)] = float(1.0/273.0) *(
            input_image[idx(i-2,j-2)] + float(4.0)*input_image[idx(i-2,j-1)] + float(7.0)*input_image[idx(i-2,j)] + float(4.0)*input_image[idx(i-2,j+1)] + input_image[idx(i-2,j+2)] + 
            float(4.0)*input_image[idx(i-1,j-2)] + float(16.0)*input_image[idx(i-1,j-1)] + float(26.0)*input_image[idx(i-1,j)] + float(16.0)*input_image[idx(i-1,j+1)] + float(4.0)*input_image[idx(i-1,j+2)] +
            float(7.0)*input_image[idx(i,j-2)] + float(26.0)*input_image[idx(i,j-1)] + float(41.0)*input_image[idx(i,j)] + float(26.0)*input_image[idx(i,j+1)] + float(7.0)*input_image[idx(i,j+2)] +
            float(4.0)*input_image[idx(i+1,j-2)] + float(16.0)*input_image[idx(i+1,j-1)] + float(26.0)*input_image[idx(i+1,j)] + float(16.0)*input_image[idx(i+1,j+1)] + float(4.0)*input_image[idx(i+1,j+2)] +
            input_image[idx(i+2,j-2)] + float(4.0)*input_image[idx(i+2,j-1)] + float(7.0)*input_image[idx(i+2,j)] + float(4.0)*input_image[idx(i+2,j+1)] + input_image[idx(i+2,j+2)]);
    }
    __syncthreads();
    
    /////
    // Compute the simple x and y gradients of the image and store these into new images
    // again using syncthreads before moving on.
    /////
    
    // X-gradient, ensure x is between 1 and width-1
    if( j > 0 && j < im_width){
        x_gradient[idx(i,j)] = float(gaussian_array[idx(i,j)] - gaussian_array[idx(i,j-1)]);
    }
    else if(j == 0){
        x_gradient[idx(i,j)] = float(0.0);
    }
    
    // Y-gradient, ensure y is between 1 and height-1
    if( i > 0 && i < im_height){
        y_gradient[idx(i,j)] = float(gaussian_array[idx(i,j)] - gaussian_array[idx(i-1,j)]);
    }
    else if(i == 0){
        y_gradient[idx(i,j)] = float(0.0);
    }
    __syncthreads();
    
    // Gradient magnitude, so 1 <= x <= width, 1 <= y <= height. 
    if( j < im_width && i < im_height){
        
        gradient_mag[idx(i,j)] = float(sqrt(x_gradient[idx(i,j)]*x_gradient[idx(i,j)] + y_gradient[idx(i,j)]*y_gradient[idx(i,j)]));
    }
    __syncthreads();
    
    /////
    // Compute the orientation angles
    /////
    if( j < im_width && i < im_height){
        if(ang_limit == 360){
            angles[idx(i,j)] = float((atan2(y_gradient[idx(i,j)],x_gradient[idx(i,j)])+pi_val)*float(180.0)/pi_val);
        }
        else{
            angles[idx(i,j)] = float((atan( y_gradient[idx(i,j)]/x_gradient[idx(i,j)] )+(pi_val/float(2.0)))*float(180.0)/pi_val);
        }
    }
    __syncthreads();
    
    // Compute the HoG using the above arrays. Do so in a 3x3 grid, with 9 angle bins for each grid.
    // forming an 81-vector and then write this 81 vector as a row in the large output array.
    
    int top_bound, bot_bound, left_bound, right_bound, offset;
    int window = 30;
     
    if(i-window/2 > 0){
        top_bound = i-window/2;
        bot_bound = top_bound + window;
    }
    else{
        top_bound = 0;
        bot_bound = top_bound + window;
    }
    
    if(j-window/2 > 0){
        left_bound = j-window/2;
        right_bound = left_bound + window;
    }
    else{
        left_bound = 0;
        right_bound = left_bound + window;
    }
    
    if(bot_bound - im_height > 0){
        offset = bot_bound - im_height;
        top_bound = top_bound - offset;
        bot_bound = bot_bound - offset;
    }
    
    if(right_bound - im_width > 0){
        offset = right_bound - im_width;
        right_bound = right_bound - offset;
        left_bound = left_bound - offset;
    }
    
    int counter_i = 0;
    int counter_j = 0;
    int bin_indx, hist_indx, glob_col_indx, glob_row_indx;
    int row_width = 81; 
    
    for(int pix_i = top_bound; pix_i < bot_bound; pix_i++){
        for(int pix_j = left_bound; pix_j < right_bound; pix_j++){
        
            bin_indx = bin_number(angles[idx(pix_i,pix_j)], ang_limit, ang_bins);
            hist_indx = hist_number(counter_i,counter_j, window);
            
            glob_col_indx = ang_bins*hist_indx + bin_indx;
            glob_row_indx = idx(i,j);
            
            output_array[glob_row_indx*row_width + glob_col_indx] = float(output_array[glob_row_indx*row_width + glob_col_indx] + float(gradient_mag[idx(pix_i,pix_j)]));
            
            
            counter_j = counter_j + 1; 
        }
        counter_i = counter_i + 1;
        counter_j = 0;
    }
             
}
"""
    return every_pixel_hog_kernel_source
#####
#END Every-pixel HoG kernel source
#####

##########

#####
# Keypoint HoG kernel source
#####
def keypoint_hog_kernel_source_code():
    keypoint_hog_kernel_source = \
"""
#include <math.h>
#include <stdio.h>

__device__ int idx(int ii, int jj){
    return gridDim.x*blockDim.x*ii+jj;
}

__device__ int bin_number(float angle_val, int total_angles, int num_bins){ 

    float angle1;   
    float min_dist;
    float this_dist;
    int bin_indx;
    
    angle1 = 0.0;
    min_dist = abs(angle_val - angle1);
    bin_indx = 0;
    
    for(int kk=1; kk < num_bins; kk++){
        angle1 = angle1 + float(total_angles)/float(num_bins);
        this_dist = abs(angle_val - angle1);
        if(this_dist < min_dist){
            min_dist = this_dist;
            bin_indx = kk;
        }
    }
    
    return bin_indx;
}

__device__ int hist_number(int ii, int jj, int win_size){

    int hist_num = 0;
    
    if(jj >= 0 && jj < win_size/3){ 
        if(ii >= 0 && ii < win_size/3){ 
            hist_num = 0;
        }
        else if(ii >= win_size/3 && ii < 2*win_size/3){
            hist_num = 3;
        }
        else if(ii >= 2*win_size/3 && ii < win_size){
            hist_num = 6;
        }
    }
    else if(jj >= win_size/3 && jj < 2*win_size/3){
        if(ii >= 0 && ii < win_size){ 
            hist_num = 1;
        }
        else if(ii >= win_size/3 && ii < 2*win_size/3){
            hist_num = 4;
        }
        else if(ii >= 2*win_size/3 && ii < win_size){
            hist_num = 7;
        }
    }
    else if(jj >= 2*win_size/3 && jj < win_size){
        if(ii >= 0 && ii < win_size){ 
            hist_num = 2;
        }
        else if(ii >= win_size/3 && ii < 2*win_size/3){
            hist_num = 5;
        }
        else if(ii >= 2*win_size/3 && ii < win_size){
            hist_num = 8;
        }
    }
    
    return hist_num;
}

__global__ void keypoint_hog_kernel(float* input_image, int im_width, int im_height, float* keypoint_xs, float* keypoint_ys, int num_keypoints, int win_size,
                                    float* x_gradient, float* y_gradient, float* gradient_mag, float* angles, float* output_array)
{    
    /////
    // Setup the thread indices and linear offset.
    /////
    int i = blockDim.y * blockIdx.y + threadIdx.y;
    int j = blockDim.x * blockIdx.x + threadIdx.x;
    int ang_limit = 180;
    int ang_bins = 9;
    float pi_val = 3.141592653589f;
    
    
    /////
    // Compute the simple x and y gradients of the image and store these into new images
    // again using syncthreads before moving on.
    /////
    
    // X-gradient, ensure x is between 1 and width-1
    if( j > 0 && j < im_width){
        x_gradient[idx(i,j)] = input_image[idx(i,j)] - input_image[idx(i,j-1)];
    }
    else if(j == 0){
        x_gradient[idx(i,j)] = 0.0f;
    }
    
    // Y-gradient, ensure y is between 1 and height-1
    if( i > 0 && i < im_height){
        y_gradient[idx(i,j)] = input_image[idx(i,j)] - input_image[idx(i-1,j)];
    }
    else if(i == 0){
        y_gradient[idx(i,j)] = 0.0f;
    }
    __syncthreads();
    
    // Gradient magnitude, so 1 <= x <= width, 1 <= y <= height. 
    if( j < im_width && i < im_height){
        
        gradient_mag[idx(i,j)] = sqrt(x_gradient[idx(i,j)]*x_gradient[idx(i,j)] + y_gradient[idx(i,j)]*y_gradient[idx(i,j)]);
    }
    __syncthreads();
    
    /////
    // Compute the orientation angles
    /////
    if( j < im_width && i < im_height){
        if(ang_limit == 360){
            angles[idx(i,j)] = (atan2(y_gradient[idx(i,j)],x_gradient[idx(i,j)])+pi_val)*180.0f/pi_val;
        }
        else{
            angles[idx(i,j)] = (atan( y_gradient[idx(i,j)]/x_gradient[idx(i,j)] )+(pi_val/2.0f))*180.0f/pi_val;
        }
    }
    __syncthreads();
    
    // Compute the HoG using the above arrays. Do so in a 3x3 grid, with 9 angle bins for each grid.
    // forming an 81-vector and then write this 81 vector as a row in the large output array.
    // Note that in this program, only pixels located at the keypoint locations do any work here.
    
    int key_x_idx;
    int found_x = 0;
    int found_y = 0;
    
    for(int key_x = 0; key_x < num_keypoints; key_x++){
        if(j == keypoint_xs[key_x]){
            found_x = 1;
            key_x_idx = key_x;
            if(i == keypoint_ys[key_x]){
                found_y = 1;
                break;
            }
        }    
    }
    
    if(found_x == 1 && found_y == 1){
    
        int top_bound, bot_bound, left_bound, right_bound, offset;
        int window = win_size;
     
        if(i-window/2 > 0){
            top_bound = i-window/2;
            bot_bound = top_bound + window;
        }
        else{
            top_bound = 0;
            bot_bound = top_bound + window;
        }
    
        if(j-window/2 > 0){
            left_bound = j-window/2;
            right_bound = left_bound + window;
        }
        else{
            left_bound = 0;
            right_bound = left_bound + window;
        }
    
        if(bot_bound - im_height > 0){
            offset = bot_bound - im_height;
            top_bound = top_bound - offset;
            bot_bound = bot_bound - offset;
        }
    
        if(right_bound - im_width > 0){
            offset = right_bound - im_width;
            right_bound = right_bound - offset;
            left_bound = left_bound - offset;
        }
    
        int counter_i = 0;
        int counter_j = 0;
        int bin_indx, hist_indx, glob_col_indx, glob_row_indx;
        int row_width = 81; 
    
        for(int pix_i = top_bound; pix_i < bot_bound; pix_i++){
            for(int pix_j = left_bound; pix_j < right_bound; pix_j++){
        
                bin_indx = bin_number(angles[idx(pix_i,pix_j)], ang_limit, ang_bins);
                hist_indx = hist_number(counter_i,counter_j,win_size);
            
                glob_col_indx = ang_bins*hist_indx + bin_indx;
                glob_row_indx = key_x_idx;
            
                output_array[glob_row_indx*row_width + glob_col_indx] = float(output_array[glob_row_indx*row_width + glob_col_indx] + float(gradient_mag[idx(pix_i,pix_j)]));
            
            
                counter_j = counter_j + 1; 
            }
            counter_i = counter_i + 1;
            counter_j = 0;
        }
    }     
}
"""
    return keypoint_hog_kernel_source
#####
# END Keypoint HoG kernel source
#####

##########

#####
# Patch HoG kernel source
#####
def patch_hog_kernel_source_code():
    patch_hog_kernel_source = \
"""
#include <math.h>
#include <stdio.h>

__device__ int idx(int ii, int jj){
    return gridDim.x*blockDim.x*ii+jj;
}

__device__ int bin_number(float angle_val, int total_angles, int num_bins){ 

    float angle1;   
    float min_dist;
    float this_dist;
    int bin_indx;
    
    angle1 = 0.0;
    min_dist = abs(angle_val - angle1);
    bin_indx = 0;
    
    for(int kk=1; kk < num_bins; kk++){
        angle1 = angle1 + float(total_angles)/float(num_bins);
        this_dist = abs(angle_val - angle1);
        if(this_dist < min_dist){
            min_dist = this_dist;
            bin_indx = kk;
        }
    }
    
    return bin_indx;
}

__device__ int hist_number(int ii, int jj, int x0, int x1, int x2, int x3, int y0, int y1, int y2, int y3){

    int hist_num = 0;
    
    if(jj >= x0 && jj < x1){ 
        if(ii >= y0 && ii < y1){ 
            hist_num = 0;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 3;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 6;
        }
    }
    else if(jj >= x1 && jj < x2){
        if(ii >= y0 && ii < y1){ 
            hist_num = 1;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 4;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 7;
        }
    }
    else if(jj >= x2 && jj < x3){
        if(ii >= y0 && ii < y1){ 
            hist_num = 2;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 5;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 8;
        }
    }
    
    return hist_num;
}

__global__ void patch_hog_kernel(float* input_image, int im_width, int im_height, int patch_top, int patch_bot, int patch_left, int patch_right, 
                                 float* x_gradient, float* y_gradient, float* gradient_mag, float* angles, float* output_array)
{    
    /////
    // Setup the thread indices and linear offset.
    /////
    int i = blockDim.y * blockIdx.y + threadIdx.y;
    int j = blockDim.x * blockIdx.x + threadIdx.x;
    int ang_limit = 180;
    int ang_bins = 9;
    float pi_val = 3.141592653589f; //91
    
    /////
    // Compute the simple x and y gradients of the image and store these into new images
    // again using syncthreads before moving on.
    /////
    
    // X-gradient, ensure x is between 1 and width-1
    if( j > 0 && j < im_width){
        x_gradient[idx(i,j)] = input_image[idx(i,j)] - input_image[idx(i,j-1)];
    }
    else if(j == 0){
        x_gradient[idx(i,j)] = float(0.0);
    }
    
    // Y-gradient, ensure y is between 1 and height-1
    if( i > 0 && i < im_height){
        y_gradient[idx(i,j)] = input_image[idx(i,j)] - input_image[idx(i-1,j)];
    }
    else if(i == 0){
        y_gradient[idx(i,j)] = float(0.0);
    }
    __syncthreads();
    
    // Gradient magnitude, so 1 <= x <= width, 1 <= y <= height. 
    if( j < im_width && i < im_height){
        
        gradient_mag[idx(i,j)] = float(sqrt(x_gradient[idx(i,j)]*x_gradient[idx(i,j)] + y_gradient[idx(i,j)]*y_gradient[idx(i,j)]));
    }
    __syncthreads();
    
    /////
    // Compute the orientation angles
    /////
    if( j < im_width && i < im_height){
        if(ang_limit == 360){
            angles[idx(i,j)] = float((atan2(y_gradient[idx(i,j)],x_gradient[idx(i,j)])+pi_val)*float(180.0)/pi_val);
        }
        else{
            angles[idx(i,j)] = float((atan( y_gradient[idx(i,j)]/x_gradient[idx(i,j)] )+(pi_val/float(2.0)))*float(180.0)/pi_val);
        }
    }
    __syncthreads();
    
    // Compute the HoG using the above arrays. Do so in a 3x3 grid, with 9 angle bins for each grid.
    // forming an 81-vector and then write this 81 vector as a row in the large output array.
    // Note that in this program, only the patch region specified in the input is used.
    
    
    int xbound1, xbound2, xbound3;
    int ybound1, ybound2, ybound3;
    
    xbound1 = patch_left + (patch_right-patch_left)/3;
    xbound2 = patch_left + 2*(patch_right-patch_left)/3;
    xbound3 = patch_right;
    
    ybound1 = patch_top + (patch_bot-patch_top)/3;
    ybound2 = patch_top + 2*(patch_bot-patch_top)/3;
    ybound3 = patch_bot;
    
    int bin_indx, hist_indx, glob_col_indx;
    
    if(i >= patch_top && i <= patch_bot && j >= patch_left && j <= patch_right){
    
        bin_indx = bin_number(angles[idx(i,j)], ang_limit, ang_bins);
        hist_indx = hist_number(i,j, patch_left, xbound1, xbound2, xbound3, patch_top, ybound1, ybound2, ybound3);
        glob_col_indx = ang_bins*hist_indx + bin_indx;
        output_array[glob_col_indx] = float(output_array[glob_col_indx] + float(gradient_mag[idx(i,j)]));
    } 
         
}
"""
    return patch_hog_kernel_source
#####
# END Patch HoG kernel source code
#####

##########

#####
# Patch/SVM kernel source -- Same as Patch HoG but without gradient computations on GPU device.
#####
def patch_svm_kernel_source_code():
    patch_svm_kernel_source = \
"""
#include <math.h>
#include <stdio.h>

__device__ int idx(int ii, int jj){
    return gridDim.x*blockDim.x*ii+jj;
}

__device__ int bin_number(float angle_val, int total_angles, int num_bins){ 

    float angle1;   
    float min_dist;
    float this_dist;
    int bin_indx;
    
    angle1 = 0.0;
    min_dist = abs(angle_val - angle1);
    bin_indx = 0;
    
    for(int kk=1; kk < num_bins; kk++){
        angle1 = angle1 + float(total_angles)/float(num_bins);
        this_dist = abs(angle_val - angle1);
        if(this_dist < min_dist){
            min_dist = this_dist;
            bin_indx = kk;
        }
    }
    
    return bin_indx;
}

__device__ int hist_number(int ii, int jj, int x0, int x1, int x2, int x3, int y0, int y1, int y2, int y3){

    int hist_num = 0;
    
    if(jj >= x0 && jj < x1){ 
        if(ii >= y0 && ii < y1){ 
            hist_num = 0;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 3;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 6;
        }
    }
    else if(jj >= x1 && jj < x2){
        if(ii >= y0 && ii < y1){ 
            hist_num = 1;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 4;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 7;
        }
    }
    else if(jj >= x2 && jj < x3){
        if(ii >= y0 && ii < y1){ 
            hist_num = 2;
        }
        else if(ii >= y1 && ii < y2){
            hist_num = 5;
        }
        else if(ii >= y2 && ii < y3){
            hist_num = 8;
        }
    }
    
    return hist_num;
}

__global__ void patch_svm_kernel(float* angles, float* gradient_mag, int y_top, int y_bot, int x_left, int x_right, float* output_array)
{    
    /////
    // Setup the thread indices and linear offset.
    /////
    int i = blockDim.y * blockIdx.y + threadIdx.y;
    int j = blockDim.x * blockIdx.x + threadIdx.x;
    int ang_limit = 180;
    int ang_bins = 9;
    
        
    // Compute the HoG using the above arrays. Do so in a 3x3 grid, with 9 angle bins for each grid.
    // forming an 81-vector and then write this 81 vector as a row in the large output array.
    // Note that in this program, only the patch region specified in the input is used.
    
    
    int xbound1, xbound2, xbound3;
    int ybound1, ybound2, ybound3;
    
    xbound1 = x_left + (x_right - x_left)/3;
    xbound2 = x_left + 2*(x_right - x_left)/3;
    xbound3 = x_right;
    
    ybound1 = y_top + (y_bot-y_top)/3;
    ybound2 = y_top + 2*(y_bot-y_top)/3;
    ybound3 = y_bot;
    
    int bin_indx, hist_indx, glob_col_indx;
    
    if(i >= y_top && i < y_bot && j >= x_left && j < x_right){
    
        bin_indx = bin_number(angles[idx(i,j)], ang_limit, ang_bins);
        hist_indx = hist_number(i,j, x_left, xbound1, xbound2, xbound3, y_top, ybound1, ybound2, ybound3);
        glob_col_indx = ang_bins*hist_indx + bin_indx;
        output_array[glob_col_indx] = output_array[glob_col_indx] + gradient_mag[idx(i,j)];
    }
}
"""
    return patch_svm_kernel_source
#####
# END Patch/SVM kernel source code
#####

