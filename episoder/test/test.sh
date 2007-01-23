#!/bin/sh
# episoder test suite, http://episoder.sourceforge.net/
#
# Copyright (c) 2005-2007 Stefan Ott. All rights reserved.
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
	UNZIP_FILE=/tmp/episoder.testdata.unzip
}

tear_down() {
	rm -f $TMPFILE
	rm -f $TMPFILE2
	rm -f $UNZIP_FILE
}

clear_files() {
	tear_down
}

test_remove_old_episodes() {
	clear_files

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

test_parse_tvcom_run() {
	FILENO=$1

	echo -n .
	clear_files
	bzip2 -dc data/tvcom.sample${FILENO}.bz2 > $UNZIP_FILE
	WGETFILE=$UNZIP_FILE

	parse_tvcom

	if [ ! -z "`diff $TMPFILE data/tvcom.output${FILENO}`" ]; then
		echo "The tvcom plugin's output is wrong at file #${FILENO}:"
		diff $TMPFILE data/tvcom.output${FILENO}
	fi
	echo .
	echo "$1 done - <enter> to continue"
	read
}

test_parse_tvcom() {
	echo -n .

	. ../plugins/episoder_plugin_tvcom.sh
	
	#url='&season=0'
	EPISODER_HOME=../plugins
	OUTPUT_FORMAT="%airdate %show %seasonx%epnum: %eptitle [%prodnum] (%totalep)"

	for file in data/tvcom.sample*bz2; do
		num=`echo $file | sed -r 's/.*sample(.*)\.bz2/\1/'`
		test_parse_tvcom_run $num
	done
}

test_tvcom_multi() {
	. ../plugins/episoder_plugin_tvcom.sh

	EPISODER_HOME=../plugins
	WGET="touch"

	base="/tmp/episoder-tvcom-multi"
	url="$base?season=2"
	tvcom_get_files

	url="$base&season=2"
	tvcom_get_files

	url="$base?season=0"
	tvcom_get_files

	url="$base"
	tvcom_get_files
}

test_parse_epguides_run() {
	FILENO=$1

	echo -n .
	clear_files
	bzip2 -dc data/epguides.sample${FILENO}.bz2 > $UNZIP_FILE
	WGETFILE=$UNZIP_FILE

	parse_epguides

	if [ ! -z "`diff $TMPFILE data/epguides.output${FILENO}`" ]; then
		echo "The epguide plugin's output is wrong at file #${FILENO}:"
		diff $TMPFILE data/epguides.output${FILENO}
	fi
	echo -n .
}

test_parse_epguides() {
	echo -n .

	. ../plugins/episoder_plugin_epguides.sh

	EPISODER_HOME=../plugins
	OUTPUT_FORMAT="%airdate %show %seasonx%epnum: %eptitle (%totalep)"
	
	for file in data/epguides.sample*bz2; do
		num=`echo $file | sed -r 's/.*sample(.*)\.bz2/\1/'`
		test_parse_epguides_run $num
	done
}


set_up
test_remove_old_episodes
#test_parse_tvcom
#test_tvcom_multi
test_parse_epguides
tear_down
echo .
