#!/usr/bin/env python
import os
import sys

from setuptools import setup

# files to install
files = []

# man page
manpage = "episoder.1"
files.append((os.path.join(sys.prefix, "share", "man", "man1"), [manpage]))

# awk parser
awkfile = os.path.join("extras", "episoder_helper_epguides.awk")
files.append((os.path.join(sys.prefix, "share", "episoder"), [awkfile]))

# documentation
doc_files = ["AUTHORS", "CHANGELOG", "COPYING", "README"]

for file in doc_files:
	files.append((os.path.join(sys.prefix, "share", "episoder"), [file]))

setup(	name			= 'episoder',
	version			= '0.7.0',
	license			= 'GPLv3',
	description		= 'TV episode notifier',
	author			= 'Stefan Ott',
	author_email		= 'stefan@ott.net',
	url			= 'http://code.ott.net/projects/episoder',
	packages		= [ 'pyepisoder' ],
	scripts			= [ 'episoder' ],
	long_description	= 'episoder is a tool to tell you about new episodes of your favourite TV shows.',
	data_files		= files,
	install_requires	= [ 'beautifulsoup', 'pyyaml', 'sqlalchemy>=0.7', 'tvdb_api' ]
)
