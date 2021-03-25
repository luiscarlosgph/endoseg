#!/usr/bin/env python
# -*- coding: utf-8 -*-
import setuptools
import unittest

setuptools.setup(name='endoseg',
    version='0.1.0',
    description='Python module to segment the visible circular area of endoscopic images.',
    author='Luis C. Garcia-Peraza Herrera',
    author_email='luiscarlos.gph@gmail.com',
    license='MIT License',
    url='https://github.com/luiscarlosgph/endoseg',
    packages=['endoseg'],
    package_dir={'endoseg' : 'src'}, 
    install_requires = ['numpy', 'grabcut', 'cv2'],
    #test_suite = 'tests',
)
