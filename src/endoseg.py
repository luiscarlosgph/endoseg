"""
@brief   Module to segment out the black padding that is usually seen around endoscopic images.
@author  Luis Carlos Garcia-Peraza Herrera (luiscarlos.gph@gmail.com).
@date    25 March 2021.
"""

import cv2
import numpy as np


def shell(cmd):
    """
    @brief Runs a shell command and returns the output.
    @param[in] cmd String with the command that will be run.
    @returns the output (stdout and stderr) of the command.
    """
    # Generate the name of the random log file that will store the command
    # output
    tmp_log_file = tempfile.gettempdir() + '/' + gen_rand_str() + '.log'
    cmd += ' > ' + tmp_log_file + ' 2>&1'

    # Run command
    os.system(cmd)

    # Read command output from logfile
    fd = open(tmp_log_file, 'r')
    output = fd.read()
    fd.close()

    # Delete log file
    rm(tmp_log_file)

    return output


def rm(path):
    """
    @brief Remove file. Only files can be removed with this function.
    @param[in] path to the file that will be removed.
    @returns nothing.
    """
    # Assert that the path is a file
    if not file_exists(path):
        raise RuntimeError('[rm] The given path is not a file.')
    os.unlink(path)


class Segmenter(object):
    """@class Segmenter of the visible are of an endoscopic image."""

    def __init__(self, min_hsv_thresh=[0, 0, 0], max_hsv_thresh=[255, 255, 10],
            deinterlace=False, denoise=True):
        """
        @details The min_hsv_thresh and max_hsv_thresh can be a list of lists, in case that you
                 want to capture several colour ranges.
        @param[in]  min_hsv_thresh  List with the lower bounds of the HSV thresholds that captures 
                                    the chroma key, the order is [H, S, V]. The default value is
                                    [35, 70, 15], which works for green screens.
        @param[in]  max_hsv_thresh  Same as above but with the upper bounds of the HSV threshold.
                                    The default value is [95, 255, 255], which works for green
                                    screens.
        """
        self._min_hsv_thresh = min_hsv_thresh
        self._max_hsv_thresh = max_hsv_thresh 
        self.deinterlace = deinterlace
        self.denoise = denoise

    @staticmethod
    def deinterlace(im):
        """
        @brief This method deinterlaces an image using ffmpeg.
        @param[in]  im  Numpy ndarray image. Shape (h, w, 3) or (h, w).
        @returns the deinterlaced image.
        """
        interlaced_path = os.path.join(tempfile.gettempdir(), '.interlaced.png')
        deinterlaced_path = os.path.join(tempfile.gettempdir(), '.deinterlaced.png')
        
        # Save image in a temporary folder
        cv2.imwrite(interlaced_path, im)
        
        # Deinterlace using ffmpeg
        shell('ffmpeg -i ' + interlaced_path + ' -vf yadif ' + deinterlaced_path)

        # Read deinterlaced image
        deinterlaced = cv2.imread(deinterlaced_path, cv2.IMREAD_UNCHANGED)

        # Remove image from temporary folder
        rm(interlaced_path)
        rm(deinterlaced_path)

        return deinterlaced

    @staticmethod
    def denoise(im, ksize=15, sigma_color=75, sigma_space=75):
        """
        @brief Denoise image to make colours more homogeneous.
        @param[in]  im     BGR input image.
        @param[in]  ksize  Kernel size for the filter.
        @returns a new filtered image.
        """
        denoised = cv2.bilateralFilter(im, ksize, sigma_color, sigma_space)
        return denoised
    
    @staticmethod
    def hsv_bg_remove(im, min_hsv_thresh, max_hsv_thresh):
        """
        @param[in]  min_hsv_thresh  List [H, S, V] or list of lists [[H, S, V], [H, S, V]] that
                                    contain the lower bound of the threshold.
        @param[in]  max_hsv_thresh  Same as above, but indicating the upper bound of the threshold.
        @reurns a binary mask with the chroma key labeled as zero, and the rest as 255.
        """
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        mask = np.zeros((im.shape[0], im.shape[1]), dtype=np.uint8)
        
        # If the user specified just a list, we make it a list of lists
        if type(min_hsv_thresh[0]) != list:
            min_hsv_thresh = [min_hsv_thresh]
            max_hsv_thresh = [max_hsv_thresh]
        
        # Perform a union of all the chroma key colour chunks
        assert(len(min_hsv_thresh) == len(max_hsv_thresh))
        for mi, ma in zip(min_hsv_thresh, max_hsv_thresh):
            lower_bound = (mi[0], mi[1], mi[2])
            upper_bound = (ma[0], ma[1], ma[2])
            new_mask = cv2.inRange(hsv, lower_bound, upper_bound)
            mask = cv2.bitwise_or(mask, new_mask)
        mask = 255 - mask

        return mask

    @staticmethod
    def largest_cc_mask(mask, ncc=1):
        """
        @brief Returns a mask with the largest connected components.
        @param[in]  mask Input binary mask with noise.
        @param[in]  ncc  Number of connected components to be retrieved.
        @returns a clean mask with just the connected components of largest area.
        """
        assert(mask.dtype == np.uint8)
    
        # Label connected components
        _, markers = cv2.connectedComponents(mask)
        frequency = np.bincount(markers.flatten()).tolist()

        # Get largest connected components
        largest_cc = [x for _, x in \
            sorted(zip(frequency, range(len(frequency))))][::-1][1:][:ncc]

        # Create the new mask
        new_mask = np.zeros_like(mask)
        for i in largest_cc:
            new_mask[markers == i] = 255 
    
        return new_mask

    def get_rect_crop(self, im, erode_iterations=3):
        """
        @brief Crop the visible part of an endoscopic image. 
        @param[in]  im  Input endoscopic image with circular FoV and black endoscopic 
                        padding.
        @returns a new image containing a rectangular crop that fits inside the circular 
                 endoscopic area.     
        """
        # Segment the endoscopic circle
        mask = self.segment(im, erode_iterations)

        # Compute centroid
        moments = cv2.moments(mask)
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])

        # Expand top-left
        tlx = cx - 1 
        tly = cy - 1
        finished = False
        while not finished and tlx > 0 and tly > 0:
            if 0 in mask[tly:cy, tlx:cx]:
                finished = True
                tlx += 1
                tly += 1
            else:
                tlx -= 1
                tly -= 1

        # Expand bottom-right
        brx = cx + 1
        bry = cy + 1
        finished = False
        while not finished and brx < mask.shape[1] - 1 and bry < mask.shape[0] - 1:
            if 0 in mask[cy:bry, cx:brx]:
                finished = True
                brx -= 1
                bry -= 1
            else:
                brx += 1
                bry += 1

        return im[tly:bry, tlx:brx].copy()
        
    def segment(self, im, erode_iterations=3):
        """
        @brief Binary segmentation of the black padding surrounding the 
               endoscopic image.
        @param[in]  im                BGR image to be segmented.
        @param[in]  erode_iterations  Depending on how blurred is the border of
                                      the endoscopic area, the mask can be a
                                      bit larger than it should, hence we erode
                                      it with a (5, 5) kernel. This parameter
                                      controls the number of erosion iterations.
                                      The default value is three iterations.
        @returns a numpy.ndarray of shape (h, w) and type np.uint8 with a label 
                 of 0 for the chroma key and 255 for the foreground objects.
        """
        # Deinterlace
        if self.deinterlace:
            im = Segmenter.deinterlace(im)

        # Denoise
        denoised_im = Segmenter.denoise(im) if self.denoise else im

        # Get HSV-based segmentation mask
        mask = Segmenter.hsv_bg_remove(denoised_im, self.min_hsv_thresh, 
            self.max_hsv_thresh)
        
        # Detect the largest connected component
        mask = Segmenter.largest_cc_mask(mask)
        
        # If the pixel in the centre is background, we have the segmentation 
        # flipped
        if mask[mask.shape[0] // 2, mask.shape[1] // 2] == 0:
            mask = 255 - mask
        
        # The mask usually comes a bit thicker than it should, so we erode it 
        # a bit
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=erode_iterations)
        
        # Convex hull as a sanity measure
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, 
            cv2.CHAIN_APPROX_SIMPLE)
        hull = cv2.convexHull(contours[0], False)
        cv2.drawContours(mask, [hull], -1, 255, -1)

        return mask

    @property
    def min_hsv_thresh(self):
        return self._min_hsv_thresh
    
    @min_hsv_thresh.setter
    def min_hsv_thresh(self, min_hsv_thresh):
        self._min_hsv_thresh = min_hsv_thresh
    
    @property
    def max_hsv_thresh(self):
        return self._max_hsv_thresh
    
    @max_hsv_thresh.setter
    def max_hsv_thresh(self, max_hsv_thresh):
        self._max_hsv_thresh = max_hsv_thresh


if __name__ == '__main__':
    raise RuntimeError('[ERROR] The endoremoval module is not supposed to be run as a script.')
