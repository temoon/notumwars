#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Setup for NotumWars Twitter application.
"""


from distutils.core import setup


setup(
    name         = "notumwars",
    version      = "0.0.1.1pa",
    description  = "Anarchy Online Notum Wars notifications for Twitter.",
    author       = "Tema Novikov",
    author_email = "temoon@temoon.pp.ru",
    download_url = "https://github.com/temoon/notumwars",
    
    scripts = (
        "bin/aochat",
    ),
    
    data_files = (
        ("/usr/local/etc", ("etc/notumwars.conf",)),
    ),
    
    classifiers = (
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
    ),
)
