# episoder-builddb.sh, http://episoder.sourceforge.net/
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
	if [ "$1" == "v" ] && [ "$VERY_VERBOSE" ]; then
		shift
		echo $*
	elif [ "$1" != "v" ] && [ "$VERBOSE" ]; then
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
	print "[*] Removing episodes prior to $DATE_TEXT"

	if [ -z "$DATE_TEXT" ]; then
		DATE_REF="-1 day"
	else
		DATE_REF="-1 day $DATE_TEXT"
	fi

	YESTERDAY=`date +%Y-%m-%d -d "$DATE_REF"`
	awk "{if (\$1 >= \"$YESTERDAY\") print \$0}" $TMPFILE > $TMPFILE2
	mv $TMPFILE2 $TMPFILE
}

get_episodes() {
	print "[*] Getting episodes"
	for url in `cat ~/.episoder | grep '^src=' | cut -b 5-`; do
		print -n "[*] Downloading"
		wget -U "$WGET_USER_AGENT" $url -O $WGETFILE $WGET_ARGS
		print -ne "\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b"
		parse
		rm -f $WGETFILE
	done
}

parse() {
	#print "[*] Parsing"
	for plugin in ${EPISODER_PLUGINS[@]}; do
		if [ ! -z "`match_$plugin $url`" ]; then
			print v Using $plugin plugin to parse
			parse_$plugin
		#else
	    	print v Not using $plugin plugin to parse
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
	print v TIME: $TIME
	print v TMPFILE: $TMPFILE
	print v TMPFILE2: $TMPFILE2
	print v WGETFILE: $WGETFILE
}

destroy_tmpfiles() {
	print "[*] Destroying tmpfiles"
	rm -f $TMPFILE $TMPFILE2 $WGETFILE
}

sort_tmpfile() {
	print "[*] Sorting episodes"
	cat $TMPFILE | sort > $TMPFILE2
	mv $TMPFILE2 $TMPFILE
}

write_episodes() {
	print "[*] Writing episodes"
	mv $TMPFILE $EPISODER_DATAFILE
}

build_db() {
	print "[*] Building DB"
	print "[*] Starting on ${DATE_TEXT}"
	
	if [ -z "$WGET_ARGS" ]; then WGET_ARGS="-q"; fi
    
	load_plugins
	open_tmpfiles
	get_episodes
	remove_old_episodes
	sort_tmpfile
	write_episodes
	destroy_tmpfiles
}
