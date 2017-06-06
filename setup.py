#!/usr/bin/env python
from os import path
from setuptools import setup

# fallback
__version__ = "0.0.0"

# files to install
files = []

# man page
manpage = "episoder.1"
files.append((path.join("man", "man1"), ["episoder.1"]))

# documentation
for file in ["AUTHORS", "CHANGELOG", "COPYING", "README"]:
	files.append((path.join("doc", "episoder"), [file]))

# get version number
exec(open("pyepisoder/version.py").read())

files.append((path.join("doc", "episoder", "examples"), ["home.episoder"]))

setup(	name			= "episoder",
	version			= __version__,
	license			= "GPLv3",
	description		= "TV episode notifier",
	author			= "Stefan Ott",
	author_email		= "stefan@ott.net",
	url			= "https://github.com/cockroach/episoder",
	packages		= ["pyepisoder"],
	test_suite		= "test",
	scripts			= ["episoder"],
	long_description	= "episoder is a tool to tell you about new episodes of your favourite TV shows",
	data_files		= files,
	install_requires	= ["argparse", "requests", "sqlalchemy>=0.7"],
	classifiers		= [
		"Development Status :: 5 - Production/Stable",
		"Environment :: Console",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
		"Natural Language :: English",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2.6",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
		"Topic :: Multimedia :: Video"
	]
)
