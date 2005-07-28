#!/bin/sh
# episoder test suite, http://tools.desire.ch/episoder/
#
# Copyright (c) 2005 Stefan Ott. All rights reserved.
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

set_up() {
	TMPFILE=/tmp/episoder.testdata.temp1
	TMPFILE2=/tmp/episoder.testdata.temp2
}

tear_down() {
	rm -f $TMPFILE
	rm -f $TMPFILE2
}

test_remove_old_episodes() {
	. ../scripts/episoder-builddb.sh

	# test using DATE_TEXT
	cp data/remove_old_episodes.sample $TMPFILE
	DATE_TEXT=2005-08-01
	remove_old_episodes

	DIFF=`diff $TMPFILE data/remove_old_episodes.output`
	if [ ! -z "$DIFF" ]; then
		echo The cleaned file does not match the expected output:
		diff $TMPFILE data/remove_old_episodes.output
	fi

	# test without DATE_TEXT
	TODAY=`date +%Y-%m-%d`
	DATE_TEXT=
	echo `date +%Y-%m-%d -d "-2 days"` Idiotic fake entry > $TMPFILE
	echo `date +%Y-%m-%d -d "-1 day"` Idiotic fake entry >> $TMPFILE
	echo `date +%Y-%m-%d` Idiotic fake entry >> $TMPFILE
	echo `date +%Y-%m-%d -d "+1 day"` Idiotic fake entry >> $TMPFILE
	echo `date +%Y-%m-%d -d "+340 days"` Idiotic fake entry >> $TMPFILE
	remove_old_episodes
	NUM=`cat $TMPFILE | wc -l`
	if [ $NUM -ne 4 ]; then
		echo The cleaned file contains $NUM entries instead of the expected 4
	fi
}

set_up
test_remove_old_episodes
tear_down
