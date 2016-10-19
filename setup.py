#!/usr/bin/env python
# encoding: utf-8
# from __future__ import absolute_import, division, print_function

from setuptools import setup, find_packages

setup(
    name='anthemav',
    version='0.0.3',
    description='Automation Library for Anthem AV receivers',
    long_description=open('README.md').read(),
    author='Tim Inglis',
    url="https://github.com/tinglis1/anthemav",
    license='BSD',
    author_email='tinglis1@gmail.com',
    packages=find_packages(),
    install_requires=['requests'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Home Automation",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: PyPy"
    ]
)
