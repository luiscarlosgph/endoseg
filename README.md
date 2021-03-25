Description
-----------
Endoseg is a Python package that facilitates the segmentation of the visible circular area of endoscopic images.

Dependencies
------------
* Numpy
```bash
# Ubuntu/Debian
$ sudo apt update
$ sudo apt install python3-pip
$ python3 -m pip install numpy --user
```

* OpenCV
```bash
# Ubuntu/Debian
$ sudo apt update
$ sudo apt install libopencv-dev python3-opencv
```

Install
-------
```bash
$ python3 -m pip install endoseg --user
```

Run
---
```bash
$ python3 -m endoseg.run --input data/demo.jpg --output data/demo_seg.png
```

Exemplary code snippet
----------------------
```python
# Read input image
im = cv2.imread('input_image.jpg', cv2.IMREAD_UNCHANGED)

# Segment the visible area of the endoscopic image
segmenter = endoseg.Segmenter()
seg = segmenter.segment(im)

# Save the segmentation to file
cv2.imwrite('output_segmentation.png', seg)
```

License
-------
This code is released under an 
[MIT license](https://github.com/luiscarlosgph/endoseg/blob/main/LICENSE).
