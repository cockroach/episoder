# episoder epguides.com plugin, http://episoder.sourceforge.net/
#
# Copyright (c) 2004-2008 Stefan Ott. All rights reserved.
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

parse_epguides() {
	local url="$1"
	local wgetfile="$2"
	local log=$( tempfile )
	local yamlfile=$( tempfile )
	local awkscript="${EPISODER_HOME}/episoder_parser_epguides.awk"

	awk -f ${awkscript} output="${yamlfile}" ${wgetfile} >> ${log} 2>&1
	local retcode=$?

	rm -f ${wgetfile}

	if [ ${retcode} -eq 0 ] ; then
		rm -f ${log}
		echo ${yamlfile}
		return 0
	else
		echo "Awk script failed, debug output:" >&2
		cat ${log} >&2
		rm -f ${log}
		rm -f ${yamlfile}
		return 2
	fi
}

match_epguides() {
	local url="$1"
	echo ${url} | grep 'epguides.com'
}

url=$1
wgetfile=$2

if [ ! -z "$( match_epguides ${url} )" ] ; then
	echo "Accepting ${url} in epguides.com plugin" >&2
	parse_epguides "${url}" "${wgetfile}"
	exit $?
else
	exit 1
fi
