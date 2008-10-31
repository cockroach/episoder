#!/usr/bin/env python
#
# episoder old episode remover, http://episoder.sourceforge.net/
#
# Copyright (c) 2004-2008 Stefan Ott. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# $Id$

import sys
import datetime
from episoder import *

def usage():
	print "Usage: %s <datafile> <days-in-past> [base-date]" % sys.argv[0]
	print "base-date can be specified as YYYY-MM-DD"

def main(argv=sys.argv):
	if len(argv) < 3:
		usage()
		return 1

	try:
		dbfile=argv[1]
		daysInPast=int(argv[2])
	except ValueError:
		usage()
		print "\nInvalid value for days-in-past"
		return 2

	if (len(argv) == 4):
		baseDateData = argv[3].split('-')
		if len(baseDateData) != 3:
			usage()
			return 4
		baseDate = datetime.date(int(baseDateData[0]),
			int(baseDateData[1]), int(baseDateData[2]))
		try:
			baseDate = datetime.date(int(baseDateData[0]),
				int(baseDateData[1]), int(baseDateData[2]))
		except TypeError:
			usage()
			print "\nInvalid value for base-date"
			return 5
	else:
		baseDate = datetime.date.today()

	data = EpisoderData(dbfile)
	try:
		data.load()
		data.removeBefore(baseDate, daysInPast)
		data.save()
	except IOError:
		print "Could not open %s" % dbfile
		return 3

if __name__ == "__main__":
	sys.exit(main())
