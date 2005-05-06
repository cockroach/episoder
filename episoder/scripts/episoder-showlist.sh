#!/bin/sh
# episoder-showlist.sh v0.2.2, http://tools.desire.ch/episoder/
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

get_date_by_offset() {
    OFFSET=$1
    CURRENT_DATE=`date +%Y-%m-%d`
    CURRENT_DATE_SECONDS=`date +%s -d $CURRENT_DATE`
    echo $((CURRENT_DATE_SECONDS + $OFFSET * 86400))
}

get_seconds_by_date() {
    DATE=$1
    echo `date +%s -d $DATE`
}

get_date_by_string() {
    STRING=$1
    echo `date +"%a, %b %d, %Y" -d $STRING`
}

show_episode_list() {
    YESTERDAY=`get_date_by_offset -1`
    TODAY=`get_date_by_offset 0`
    TOMORROW=`get_date_by_offset 1`

    for episode in `cat $EPISODER_DATAFILE | head -n 3 | sed 's/\ /_/g'`; do
        episode=`echo $episode | sed 's/_/\ /g'`
        DATE=`echo $episode | cut -d ' ' -f 1`
        NAME=`echo $episode | cut -b 12-`
        if [ "`get_seconds_by_date $DATE`" -eq "$TODAY" ]; then
    	    echo -e "\E[33;1m>`get_date_by_string ${DATE}`<  ${NAME}\E[30;0m"
        elif [ "`get_seconds_by_date $DATE`" -eq "$TOMORROW" ]; then
	    echo -e "\E[32;1m `get_date_by_string ${DATE}`   ${NAME}\E[30;0m"
        elif [ "`get_seconds_by_date $DATE`" -eq "$YESTERDAY" ]; then
	    echo -e "\E[31;1m `get_date_by_string ${DATE}`   ${NAME}\E[30;0m"
        fi
    done
}
