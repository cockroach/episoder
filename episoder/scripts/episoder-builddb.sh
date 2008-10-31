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

# Print debug information
#
# If the first argument is 'v', only print it in "very verbose" mode
#
print() {
	if [ "$1" == "v" ] && [ "$VERY_VERBOSE" ]; then
		shift
		echo $*
	elif [ "$1" != "v" ] && [ "$VERBOSE" ]; then
		echo $*
	fi
}

print_error() {
	color_red='\E[31;1m'
	print -ne ${color_red}
	print -e "[!] " $*
	color_default='\E[30;0m'
	print -ne ${color_default}
}

# Remove old episodes from the data file
#
#   $1	path to local data file
#
#   Returns the exit code from the external script which does the actual work
#
remove_old_episodes() {
	local datafile="$1"
	print "[*] Removing episodes prior to ${DATE_TEXT}"
	${EPISODER_HOME}/remove-old.py ${datafile} 1 "${DATE_TEXT}"
	local exitcode=$?
	print v "--- Returned with exit code ${exitcode}"
	[ ${exitcode} -ne 0 ] && print_error "External command failed"
	return ${exitcode}
}

# Download a file via http
#
#   $1	url to download
#   $2	local file to write to
#
#   Returns 0 on success, 1 otherwise
#
episoder_get_file() {
	local url="$1"
	local destination="$2"

	wget -U "${WGET_USER_AGENT}" "${url}" -O ${destination} ${WGET_ARGS}
	local exitcode=$?
	if [ "${exitcode}" -ne 0 ]; then
		print_error "Download failed: ${url}"
		return 1
	fi
	return 0
}

# Parse a url
#
#   $1	url to parse
#   $2	local file containing the data from the url
#
parse_url() {
	local url="$1"
	local wgetfile="$2"
	local found_parser=0

	print "[*] Calling parsers"
	for parser in ${EPISODER_HOME}/episoder_plugin_*.sh ; do
		local log_stdout=$( tempfile )
		local log_stderr=$( tempfile )
		${parser} ${url} ${wgetfile} 2>${log_stderr} >${log_stdout}
		local retcode=$?

		print v "--- Code ${retcode} from ${parser##*/}"
		print v "--- Data written to ${log_stdout}"

		if [ ${retcode} -eq 0 ] ; then
			found_parser=1
			local yamlfile=$( cat $log_stdout )
			if [ ! -z ${name} ] ; then
				sed -i "s/  title: .*/  title: ${name}/" \
					${yamlfile}
			fi
			cat ${yamlfile} >> ${yamldata}
			rm -f ${yamlfile}
			rm -f ${log_stdout}
			rm -f ${log_stderr}
			break
		elif [ ${retcode} -eq 1 ] ; then
			print "--- Rejected by ${parser}"
		else
			echo "Caught exit code ${retcode}" >>${log_stderr}
			cat ${log_stderr}
		fi
		rm -f ${log_stdout}
		rm -f ${log_stderr}
	done

	[ ${found_parser} -eq 0 ] && return 1
	return 0
}

# Get all episodes
#
#   $1	local file to write parsed data to
#
#   Returns 0 on success, 1 if no parser was found and random other values
#   otherwise
#
get_episodes() {
	local datafile="$1"

	print "[*] Getting episodes"

	# a data file to gather all the yaml output
	local yamldata=$( tempfile )

	export EPISODER_HOME

	grep '^src=' ${EPISODER_RC_FILE} | while read line; do
		local url=$( echo ${line} | cut -b 5- | cut -d ' ' -f 1 )

		print v "--- URL: ${url}"

		local htmlfile=$( tempfile )
#		episoder_get_file "${url}" "${htmlfile}"
		cp /tmp/filec5E5sv ${htmlfile}
		local exitcode=$?
		if [ ${exitcode} -ne 0 ] ; then
			rm -f ${htmlfile}
			continue
		fi

		# override the show's name
		if [ ! -z "`echo $line | grep 'name='`" ]; then
			local name=$( echo ${line} \
				| sed "s/src=.* name=\(.*\)/\1/" )
			print "[*] Overriding source's name with \"${name}\""
		else
			local name=''
		fi

		parse_url "${url}" "${htmlfile}"
		local parse_url_retcode=$?

		print v "--- Parsed with return code ${parse_url_retcode}"
		[ ${parse_url_retcode} -gt 1 ] && print_error "Parser error"

		# override the show's name
		if [ ! -z "`echo $line | grep 'name='`" ]; then
			local name=$( echo ${line} \
				| sed "s/src=.* name=\(.*\)/\1/" )
			print "[*] Overriding source's name with \"${name}\""
		else
			local name=''
		fi

		# cleanup if no error occurred
		if [ ${parse_url_retcode} -eq 0 ] ; then
			rm -f ${htmlfile}
		else
			error=${parse_url_retcode}
			mv ${htmlfile} ${htmlfile}.EPISODER.ERROR
			print_error "No parser found for ${url}"
		fi
	done

	cat ${yamldata} >> ${datafile}
	rm -f ${yamldata}
}

# Write episoder output
#
#   $1	local data file
#   $2  the output plugin to use
#
write_output() {
	local datafile=$1
	local plugin=$2
	print "[*] Writing output"
	print v "--- Using ${plugin} plugin on ${datafile}"

	${EPISODER_HOME}/episoder_output_${plugin} "${datafile}"
	local exitcode=$?

	print v "--- Returned with code ${exitcode}"
	[ ${exitcode} -ne 0 ] && print_error "Error writing output"

	rm -f ${datafile}
}

write_episodes() {
	# TODO: implement something like this
	print "[*] Writing episodes"
	mv $TMPFILE $EPISODER_DATAFILE
}

# Build the episoder database
#
build_db() {
	print "[*] Building DB"
	print "[*] Starting on ${DATE_TEXT}"

	if [ -z "$WGET_ARGS" ]; then WGET_ARGS="-q"; fi

	local datafile=$( tempfile )
	echo "Shows:" > ${datafile}

	get_episodes "${datafile}"
	get_episodes_retval=$?

	print v "--- Done building db, return code: ${get_episodes_retval}"

	if [ ${get_episodes_retval} -eq 0 ] ; then
		print v "--- Writing parsed data to data base"
		cp ${datafile} ~/.episoder-data
	fi

	[ -z "${NODATE}" ] && remove_old_episodes "${datafile}"

	write_output "${datafile}" "${OUTPUT_PLUGIN}"

#	sort_tmpfile
#	write_episodes
#	destroy_tmpfiles
}
