#!/bin/sh
# episoder-builddb.sh, http://tools.desire.ch/episoder/
#
# Copyright (c) 2004, 2005 Stefan Ott. All rights reserved.
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

load_plugins() {
	print "[*] Loading plugins"
	EPISODER_PLUGINS=( )

	for file in $EPISODER_HOME/episoder_plugin_*.sh; do
        	. $file
	done
}

print() {
	if [ "$VERBOSE" ]; then
		echo $*
	fi
}

print_next_status() {
	if [ "$VERBOSE" ]; then
		status=('/' '-' '\' '|')
        	STATUS_INDEX=$(((STATUS_INDEX+1) % 4))
		echo -ne "\b${status[((STATUS_INDEX))]}"
	fi
}

remove_old_episodes() {
	print "[*] Removing old episodes"
	rm -f $TMPFILE2 && touch $TMPFILE2
	YESTERDAY=$((`date +%s -d $TODAY` - 86400))
	for episode in `cat $TMPFILE`; do
		DATE=`echo $episode | cut -b 1-10`
		UNIX_DATE=`date +%s -d $DATE`
		if [ ! $UNIX_DATE -lt $YESTERDAY ]; then
			echo $episode >> $TMPFILE2
			COMMENT="Keeping $episode"
		else
			COMMENT="Dropping $episode"
		fi
		print $COMMENT
	done
	mv $TMPFILE2 $TMPFILE
}

get_episodes() {
	print "[*] Getting episodes"
	TODAY=`date +%Y-%m-%d`
	for url in `cat ~/.episoder | grep '^src=' | cut -b 5-`; do
		wget -U "$WGET_USER_AGENT" $url -O $WGETFILE $WGET_ARGS
		parse
		remove_old_episodes
		rm -f $WGETFILE
	done
}

parse() {
	print "[*] Parsing"
	for plugin in ${EPISODER_PLUGINS[@]}; do
		if [ ! -z "`match_$plugin $url`" ]; then
			print Using $plugin plugin to parse
			parse_$plugin
		else
	    		print Not using $plugin plugin to parse
		fi
	done
}

open_tmpfiles() {
	print "[*] Opening tmpfiles"
	TIME=`date +%N`
	TMPFILE="/tmp/episoder.data.$TIME"
	TMPFILE2="/tmp/episoder.temp.$TIME"
	WGETFILE="/tmp/episoder.wget.$TIME"
	rm -f $TMPFILE $TMPFILE2 $WGETFILE
	touch $TMPFILE $TMPFILE2 $WGETFILE
	print TIME: $TIME
	print TMPFILE: $TMPFILE
	print TMPFILE2: $TMPFILE2
	print WGETFILE: $WGETFILE
}

destroy_tmpfiles() {
	print "[*] Destroying tmpfiles"
	rm -f $TMPFILE $TMPFILE2 $WGETFILE
}

sort_tmpfile() {
	print "[*] Sorting tmpfiles"
	for item in `cat $TMPFILE | sort`; do
		item=`echo $item | sed s/_/\ /g`
		ITEM_UNIX_TIME=`echo $item | cut -d ' ' -f 1`
		ITEM_DATE=`date -d $ITEM_UNIX_TIME +%d-%b-%Y`
		echo $item >> $TMPFILE2
	done
	if [ -f "$TMPFILE2" ]; then
    		mv $TMPFILE2 $TMPFILE
	fi
}

write_episodes() {
	print "[*] Writing episodes"
	mv $TMPFILE $EPISODER_DATAFILE
}

build_db() {
	print "[*] Building DB"
	if [ -z "$WGET_ARGS" ]; then WGET_ARGS="-q"; fi
    
	load_plugins
	open_tmpfiles
	get_episodes
	sort_tmpfile
	write_episodes
	destroy_tmpfiles
}
