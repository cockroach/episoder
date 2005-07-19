# episoder-showlist.sh, http://tools.desire.ch/episoder/
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

get_date_by_offset() {
	OFFSET=$1
	echo `date +"%Y-%m-%d" -d "+$OFFSET days"`
}

show_episode_list() {
	YESTERDAY=`get_date_by_offset -1`
	TODAY=`get_date_by_offset 0`

	if [ -z "$DATE_FORMAT" ]; then
		DATE_FORMAT="%a, %b %d, %Y"
	fi

	echo -ne "\E[31;1m"	# color: red
	grep "^$YESTERDAY" $EPISODER_DATAFILE | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $YESTERDAY`/"

	echo -ne "\E[33;1m"	# color: yellow
	grep "^$TODAY" $EPISODER_DATAFILE | sed s/^/\>/ | sed s/$/\</ | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT"`/"

	echo -ne "\E[32;1m"	# color: green 

	for ((day=1; day <= $NUM_DAYS; day++)); do
		DATE=`get_date_by_offset $day`
		grep "^$DATE" $EPISODER_DATAFILE | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $DATE`/"
	done

	echo -ne "\E[30;0m"	# color: back to normal
}
