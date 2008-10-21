# episoder-builddb.sh, http://episoder.sourceforge.net/
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

print() {
	if [ "$1" == "v" ] && [ "$VERY_VERBOSE" ]; then
		shift
		echo $*
	elif [ "$1" != "v" ] && [ "$VERBOSE" ]; then
		echo $*
	fi
}

remove_old_episodes() {
	print "NOT IMPLEMENTED YET"
	return 0

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

episoder_get_file() {
	local url="$1"
	local destination="$2"

	wget -U "${WGET_USER_AGENT}" "${url}" -O ${destination} ${WGET_ARGS}
	EXIT_STATUS=$?
	print -ne "\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b"
	if [ "${EXIT_STATUS}" -ne 0 ]; then
		color_red='\E[31;1m'
		print -ne ${color_red}
		print -e "\nDownload failed: $url"
		color_default='\E[30;0m'
		print -ne ${color_default}
		return 1
	fi
	return 0
}

get_episodes() {
	print "[*] Getting episodes"

	# a return value of 1 means that no parser was found
	local retval=1

	# a data file to gather all the yaml output
	local yamldata=$( tempfile )

	export EPISODER_HOME
	export -f episoder_get_file

	grep '^src=' ${EPISODER_RC_FILE} | while read line; do
		local url=$( echo ${line} | cut -b 5- | cut -d ' ' -f 1 )

		# override the show's name
		if [ ! -z "`echo $line | grep 'name='`" ]; then
			local name=$( echo ${line} \
				| sed "s/src=.* name=\(.*\)/\1/" )
			print "[*] Overriding source's name with \"${name}\""
		else
			local name=''
		fi

		print "[*] Calling parsers"
		for parser in ${EPISODER_HOME}/episoder_plugin_*.sh ; do
			local log_stdout=$( tempfile )
			local log_stderr=$( tempfile )
			${parser} ${url} 2>${log_stderr} >${log_stdout}
			local retcode=$?
			if [ ${retcode} -eq 0 ] ; then
				retval=0
				local yamlfile=$( cat $log_stdout )
				if [ ! -z ${name} ] ; then
					sed -i "s/  title: .*/  title: ${name}/" ${yamlfile}
				fi
				cat ${yamlfile} >> ${yamldata}
				rm -f ${yamlfile}
				rm -f ${log_stdout}
				rm -f ${log_stderr}
				break
			elif [ ${retcode} -eq 1 ] ; then
				print "Rejected by ${parser}"
			else
				echo "Caught exit code ${retcode}" \
					>>${log_stderr}
				cat ${log_stderr}
			fi
			rm -f ${log_stdout}
			rm -f ${log_stderr}
		done
	done
#	rm -f ${yamldata}
	echo $yamldata
	return ${retval}
}

write_episodes() {
	print "[*] Writing episodes"
	mv $TMPFILE $EPISODER_DATAFILE
}

build_db() {
	print "[*] Building DB"
	print "[*] Starting on ${DATE_TEXT}"

	if [ -z "$WGET_ARGS" ]; then WGET_ARGS="-q"; fi

	get_episodes
#	if [ -z "$NODATE" ]; then remove_old_episodes; fi
#	sort_tmpfile
#	write_episodes
#	destroy_tmpfiles
}
