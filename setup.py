#!/usr/bin/env python
import os
import sys

from distutils.core import setup
from distutils.sysconfig import get_python_lib

# files to install
files = []

# man page
manpage = "episoder.1"
files.append((os.path.join(sys.prefix, "share", "man", "man1"), [manpage]))

# awk parser
awkfile = os.path.join("extras", "episoder_helper_epguides.awk")
files.append((os.path.join(sys.prefix, "share", "episoder"), [awkfile]))

# documentation
doc_files = ["AUTHORS", "CHANGELOG", "COPYING", "FAQ", "README", "README.tvcom" ]

for file in doc_files:
	files.append((os.path.join(sys.prefix, "share", "episoder"), [file]))

if __name__ == '__main__':
	LONG_DESCRIPTION = \
"""episoder is a tool to tell you about new episodes of your favourite TV shows."""

	from pyepisoder.episoder import version

	setup(	name			= 'episoder',
		version			= version,
		license			= 'GPLv2',
		description		= 'TV episode notifier',
		author			= 'Stefan Ott',
		author_email		= 'stefan@ott.net',
		url			= 'http://episoder.sf.net/',
		packages		= [ 'pyepisoder' ],
		scripts			= [ 'episoder' ],
		long_description	= LONG_DESCRIPTION,
		data_files		= files,
		requires		= [ 'beautifulsoup', 'pysqlite2', 'yaml' ]
	)
