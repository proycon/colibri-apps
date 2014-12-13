#!/usr/bin/env python3
# -*- coding: utf8 -*-

from setuptools import setup

setup(
    name = "colibriapps",
    version = "0.2",
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Colibri Applications. NLP tools based on Colibri Core"),
    license = "GPL",
    keywords = "nlp colibri",
    url = "https://github.com/proycon/colibri-apps",
    packages=['colibriapps'],
    long_description="Colibri-MT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points = {
        'console_scripts': [
            'colibri-graphview = graphview:main',
            'colibri-predictor = predictor:main',
        ]
    },
    package_data = {},
    install_requires=['colibricore >= 0.5']
)
