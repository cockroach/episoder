# episoder tv.com plugin, http://episoder.sourceforge.net/
#
# Copyright (c) 2004-2007 Stefan Ott. All rights reserved.
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

parse_tvcom() {
	awk -f $EPISODER_HOME/episoder_parser_tvcom.awk format="$OUTPUT_FORMAT" TMPFILE="$TMPFILE" VERBOSE="$VERBOSE" VERY_VERBOSE="$VERY_VERBOSE" $WGETFILE 
}

match_tvcom() {
	echo $1 | grep 'tv.com'
}

exit 1

EPISODER_PLUGINS[${#EPISODER_PLUGINS[*]}]='tvcom'
