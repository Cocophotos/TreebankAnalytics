#!/usr/bin/env python3

from setuptools import setup, find_packages
import treebankanalytics

setup(
    name='TreebankAnalytics',
    description='Column-Oriented Treebank Analytics (CoNLL-X like)',
    author='Corentin Ribeyre',
    author_email='corentin.ribeyre@gmail.com',
    version="v1.1.2",
    license= 'MIT',
    platforms=["any"],
    packages=find_packages(exclude = ['ez_setup',
        '*.tests', '*.tests.*', 'tests.*', 'tests']),
    install_requires=['pyyaml'],

    #We use nose for testing, it's far easier than the classic method
    test_suite="nose.collector",
    tests_require=['nose'],

    entry_points = {
        'console_scripts': [
            'TreebankAnalytics = treebankanalytics.main:main'
        ],
    },
)
