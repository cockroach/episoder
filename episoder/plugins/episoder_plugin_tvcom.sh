#!/bin/sh
# episoder_plugin_tvcom.sh v0.2.2, http://tools.desire.ch/episoder/
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

do_parse_tvcom() {
    SHOW=`grep '<title>' $WGETFILE | sed 's/.*<title>\(.*\) Episode List.*/\1/'`
    SEASON_NUMBER=`grep '<h3 class="pl-5">Season .*</h3>' $WGETFILE | sed 's:.*<h3 class="pl-5">Season \(.*\)</h3>.*:\1:'`
    print "Parsing show: $SHOW, Season $SEASON_NUMBER"

    echo "`cat $WGETFILE`" | while read line
    do
	print_next_status
	MATCH=`echo $line | grep '[0-9]: *$'`
	if [ ! -z "$MATCH" ]; then
	    EPISODE_NUMBER=${MATCH/:/}
	    EPISODE_NUMBER=`echo $EPISODE_NUMBER | sed 's/^\([0-9]\)$/0\1/'`
	    print -ne "\b Found episode $EPISODE_NUMBER, looking for date:_"
	fi
	if [ ! -z "$EPISODE_NUMBER" ]; then
	    MATCH=`echo $line | grep ' *[0-9]/[0-9][0-9]*/[0-9]*$'`
	    if [ ! -z "$MATCH" ]; then
	        EPISODE_DATE=$MATCH
		print -en "\b $EPISODE_DATE"
		
		if [ "$EPISODE_DATE" != "0/0/0" ]; then
		    echo `date +%Y-%m-%d -d ${EPISODE_DATE}` ${SHOW} ${SEASON_NUMBER}x${EPISODE_NUMBER} | sed s/\ /_/g >> $TMPFILE
		    print ", OK"
		else
		    print ', DROPPED - no date'
		fi

		EPISODE_NUMBER=""
	    fi
	fi
    done
    print -e "\b done"
}

get_tvcom_urls() {
	grep -e "| \{25\}.*$url" $WGETFILE | sed 's:.*<a href="\(.*\)">.*</a>.*:\1:'
}

parse_tvcom() {
	do_parse_tvcom

	MATCH=`echo $url | grep '&season'`
	if [ -z $MATCH ]; then
		# we have an index page (= season 1) and need to fetch & parse
		# all the subpages (other seasons)
		for URL in `get_tvcom_urls`; do
			wget -U "$WGET_USER_AGENT" $URL -O $WGETFILE $WGET_ARGS
			do_parse_tvcom
		done
	fi
}

match_tvcom() {
    echo $1 | grep 'tv.com'
}

EPISODER_PLUGINS[${#EPISODER_PLUGINS[*]}]='tvcom'
