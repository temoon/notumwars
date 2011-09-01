#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Setup.
"""


from distutils.core import setup


setup(
    name         = "notumwars",
    version      = "0.1.0.2a",
    description  = "Anarchy Online Notum Wars notifications for Twitter.",
    author       = "Tema Novikov",
    author_email = "temoon@temoon.pp.ru",
    download_url = "https://github.com/temoon/notumwars",
    
    scripts = (
        "notumwars.py",
    ),
    
    classifiers = (
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
    ),
)
