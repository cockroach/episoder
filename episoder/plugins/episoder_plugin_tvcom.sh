# episoder tv.com plugin, http://tools.desire.ch/episoder/
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

	print "Parsing show: $SHOW"

	echo "`cat $WGETFILE`" | while read line; do
		print_next_status

		if [ -z "$PARSE" ] && [ ! -z "`echo $line | grep '<h3 class="pl-5">All Seasons</h3>'`" ]; then
			print -e "\b Found start of data area, parsing ..."
			PARSE=true
		elif [ ! -z "$PARSE" ] && [ ! -z "`echo $line | grep '<div class="gray-box pod cb ml-10 mb-10 f-bold f-med-gray f-12">'`" ]; then
			print -e "\b Found end of data area."
			PARSE=''
			break
		fi
		if [ ! -z "$PARSE" ]; then
			MATCH=`echo $line | grep '[a-zA-Z0-9]: *$'`
			if [ ! -z "$MATCH" ]; then
				EPISODE_TOTAL_NUMBER=`echo $MATCH | sed 's/\([0-9]*\):.*/\1/'`
				print -ne "\b Found episode $EPISODE_TOTAL_NUMBER, date:_"
			fi
			if [ ! -z "$EPISODE_TOTAL_NUMBER" ]; then
				MATCH=`echo $line | grep '</strong>$'`
				if [ ! -z "$MATCH" ]; then
					EPISODE_NAME=`echo $line | sed 's/\(.*\)&nbsp;<.strong>/\1/'`
				fi
			fi
			if [ ! -z "$EPISODE_NAME" ]; then
				MATCH=`echo $line | grep ' *[0-9]/[0-9][0-9]*/[0-9]*$'`
			    	if [ ! -z "$MATCH" ]; then
			        	EPISODE_DATE=$MATCH
					print -en "\b $EPISODE_DATE"
	
					if [ "$EPISODE_DATE" != "0/0/0" ]; then
					    print -n ", number:_"
					else
					    print ', DROPPED - no date'
					    EPISODE_DATE=''
					fi
				fi
			fi
			if [ ! -z "$EPISODE_DATE" ]; then
				MATCH=`echo $line | grep ' </td>$' | sed 's/^\(.*\) <.td>$/\1/'`
				if [ ! -z "$MATCH" ] && [ "$MATCH" != "&nbsp;" ]; then
					EPISODE_PRODNUM=$MATCH
				fi
			fi
			if [ ! -z "$EPISODE_DATE" ]; then
				MATCH=`echo $line | grep '[0-9] - [0-9]'`
				if [ ! -z "$MATCH" ]; then
					SEASON=`echo $line | sed 's/.*>\([0-9]*\) - [0-9].*/\1/'`
					EPISODE_NUMBER=`echo $line | sed 's/.*[0-9] - \([0-9]*\).*/\1/' | sed 's/^\([0-9]\)$/0\1/'`
					put_episode `date +%Y-%m-%d -d ${EPISODE_DATE}` ${SHOW// /_} ${SEASON} ${EPISODE_NUMBER} ${EPISODE_NAME// /_} ${EPISODE_TOTAL_NUMBER} ${EPISODE_PRODNUM// /_}
					print -e "\b ${SEASON}x${EPISODE_NUMBER} (${EPISODE_PRODNUM})"
					EPISODE_DATE=''
					EPISODE_TOTAL_NUMBER=''
					EPISODE_PRODNUM=''
				fi
			fi
		fi
	done
	print -e "\b done"
}

get_tvcom_urls() {
	grep -e "| \{25\}.*$url" $WGETFILE | sed 's:.*<a href="\(.*\)">.*</a>.*:\1:'
}

parse_tvcom() {
	MATCH=`echo $url | grep '&season=0'`
	if [ -z "`echo $url | grep '&season=0'`" ]; then 
		echo "ERROR: Please make sure your url points to the 'all seasons' page (season=0)" >&2
		exit 1
	fi
	
	do_parse_tvcom
}

match_tvcom() {
	echo $1 | grep 'tv.com'
}

EPISODER_PLUGINS[${#EPISODER_PLUGINS[*]}]='tvcom'
