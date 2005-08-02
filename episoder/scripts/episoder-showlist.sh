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

	if [ -z "$DATE_TEXT" ]; then
		DATE_REF="+$OFFSET days"
	else
		DATE_REF="+$OFFSET days $DATE_TEXT"
	fi
	
	echo `date +"%Y-%m-%d" -d "$DATE_REF"`
}

show_episode_list() {
	color_default='\E[30;0m'
	color_red='\E[31;1m'
	color_yellow='\E[33;1m'
	color_green='\E[32;1m'
	color_lightblue='\E[36;1m'
	color_gray=$color_default
	

	if [ -z "$DATE_FORMAT" ]; then
		DATE_FORMAT="%a, %b %d, %Y"
	fi
	
	if [ -z "$SEARCHALL_TEXT" ]; then

		YESTERDAY=`get_date_by_offset -1`
		TODAY=`get_date_by_offset 0`
		TOMORROW=`get_date_by_offset 1`

		echo -ne ${color_red}
		grep "^$YESTERDAY" $EPISODER_DATAFILE | grep $GREP_ARGS "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $YESTERDAY`/"

		echo -ne ${color_yellow}
		grep "^$TODAY" $EPISODER_DATAFILE | grep $GREP_ARGS "$SEARCH_TEXT" | sed 's/.*/>\0</' | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $TODAY`/"

		echo -ne ${color_green}	
		grep "^$TOMORROW" $EPISODER_DATAFILE | grep $GREP_ARGS "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $TOMORROW`/"

		echo -ne ${color_lightblue}
		for ((day=2; day <= $NUM_DAYS; day++)); do
			DATE=`get_date_by_offset $day`
			grep "^$DATE" $EPISODER_DATAFILE | grep $GREP_ARGS "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $DATE`/"
		done

	else
		echo -ne ${color_gray}	# color: Gray 
		grep $GREP_ARGS "$SEARCHALL_TEXT" $EPISODER_DATAFILE | while read line; do
			DATE=${line:0:10}
			output=`echo $line | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/\`date +\"$DATE_FORMAT\" -d $DATE\`/" | sed -e "s/$SEARCHALL_TEXT/\\\\\E${color_green}\0\\\\\E${color_gray}/${SED_ARGS}g"`
			echo -e $output
		done
	fi
	echo -ne ${color_default}
}
