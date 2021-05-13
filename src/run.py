"""
@brief   Module to segment the circular visible area of endoscopic images.
@author  Luis Carlos Garcia-Peraza Herrera (luiscarlos.gph@gmail.com).
@date    25 March 2021.
"""

import argparse
import cv2
import os

# My imports
import endoseg


def parse_command_line_parameters(parser):      
    """
    @brief  Parses the command line parameters provided by the user and makes sure that 
            mandatory parameters are present.
    @param[in]  parser  argparse.ArgumentParser
    @returns an object with the parsed arguments. 
    """
    msg = {
        '--input':          'Path to the input image.',
        '--output-seg':     'Path of the file where the segmentation will be saved.',
        '--output-crop':    'Path of the file where the rectangular crop will be saved.',
        '--min-hsv-thresh': """Tuple with minimum bound for HSV threshold. 
                               Syntax: (H, S, V).
                               Hue range is [0, 179], saturation range is [0, 255], 
                               and value range is [0, 255].""",
        '--max-hsv-thresh': """Tuple with maximum bound for HSV threshold. 
                               Syntax: (H, S, V). 
                               Hue range is [0, 179], saturation range is [0, 255], and 
                               value range is [0, 255].""",
        '--deinterlace':    'Deinterlace the images as a preprocessing step.',
        '--denoise':        """Set it to one to denoise the image before the HSV 
                               segmentation.""",
    }

    # Mandatory parameters
    parser.add_argument('--input', required=True, help=msg['--input'])
    parser.add_argument('--output-seg', required=True, help=msg['--output-seg'])
    parser.add_argument('--output-crop', required=True, help=msg['--output-crop'])
    
    # Optional parameters 
    parser.add_argument('--min-hsv-thresh', required=False, default='(0, 0, 0)', 
        help=msg['--min-hsv-thresh'])
    parser.add_argument('--max-hsv-thresh', required=False, default='(255, 255, 10)', 
        help=msg['--max-hsv-thresh'])
    parser.add_argument('--deinterlace', required=False, default=False, 
        help=msg['--deinterlace'])
    parser.add_argument('--denoise', required=False, default=True, help=msg['--denoise'])
    
    # Parse command line
    args = parser.parse_args()

    return args


def validate_cmd_param(args):
    """
    @brief  The purpose of this function is to assert that the parameters passed in the 
            command line are ok.
    @param[in]  args  Parsed command line parameters.
    @returns nothing.
    """
    if not os.path.isfile(args.input):
        raise ValueError('[validate_cmd_param] Error, the input file does not exist.')
    if os.path.isfile(args.output_seg):
        raise ValueError('[validate_cmd_param] Error, the output file already exists.')
    if os.path.isfile(args.output_crop):
        raise ValueError('[validate_cmd_param] Error, the output file already exists.')
    assert(type(eval(args.min_hsv_thresh) == tuple))
    assert(type(eval(args.max_hsv_thresh) == tuple))
    args.min_hsv_thresh = eval("'" + args.min_hsv_thresh + "'")
    args.max_hsv_thresh = eval("'" + args.max_hsv_thresh + "'")
    assert(int(args.deinterlace) == 0 or int(args.deinterlace) == 1)
    assert(int(args.denoise) == 0 or int(args.denoise) == 1)


def convert_args_to_correct_datatypes(args):
    """
    @brief  Convert the parameter strings to the right datatypes.
    @param[in,out]  args  Parsed command line parameters.
    @returns nothing.
    """
    args.min_hsv_thresh = eval(args.min_hsv_thresh)
    args.max_hsv_thresh = eval(args.max_hsv_thresh)
    args.deinterlace = bool(int(args.deinterlace))
    args.denoise = bool(int(args.denoise))


def main(): 
    # Process command line parameters
    parser = argparse.ArgumentParser()
    args = parse_command_line_parameters(parser)
    validate_cmd_param(args)
    convert_args_to_correct_datatypes(args)

    # Read input image
    im = cv2.imread(args.input, cv2.IMREAD_UNCHANGED)

    # Segment the visible area of the endoscopic image
    segmenter = endoseg.Segmenter(min_hsv_thresh=args.min_hsv_thresh, 
                                  max_hsv_thresh=args.max_hsv_thresh, 
                                  deinterlace=args.deinterlace, denoise=args.denoise)
    seg = segmenter.segment(im)

    # Save the segmentation to file
    cv2.imwrite(args.output_seg, seg)

    # Get a crop of the rectangular area within the endoscopic circle
    rect_crop_im = segmenter.get_rect_crop(im)

    # Save the rectangular crop to file
    if '.jpg' in args.output_crop:
        cv2.imwrite(args.output_crop, rect_crop_im, [cv2.IMWRITE_JPEG_QUALITY, 100])
    else:
        cv2.imwrite(args.output_crop, rect_crop_im)

if __name__ == '__main__':
    main()
