# episoder epguides.com parser helper
#
# Copyright (C) 2006-2009 Stefan Ott. All rights reserved.
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
# $Id: episoder_helper_epguides.awk 172 2008-11-05 03:55:34Z stefan_ott $

/<html>.*<head>/ {
	# Some files don't have proper linebreaks - they'll have <html> and
	# <head> on the same line
	titleStart = index($0, "<title>") + 8;
	titlePart = substr($0, titleStart);

	titleEnd = index($0, "(a Titles ");

	set_show(substr($0, titleStart, titleEnd - titleStart - 1));
}

/^<h1>/ {
	sub(/<h1><a href=\".*\">/, "", $0)
	sub(/<\/a><\/h1>/, "", $0)

	# remove ^M
	gsub(/\015/, "", $0)
	set_show($0)
}

/aired from:/ {
	pos = match($0, /___/)
	if (pos == 0) {
		running="No"
	}
}

function set_show(showName) {
	gsub("'", "''", showName)
	print "- title: '" showName "'" >> output
	print "  episodes:" >> output

	printf "%s... ", showName
}

/^&bull; Season/ {
	# remove ^M
	gsub(/\015/, "", $3)

	# Some files come with bullets before the season number
	season = $3

	if (season == "") {
		season = 0
	}
}

/^Season/ {
	# Most, however, don't

	# remove ^M
	gsub(/\015/, "", $2)
	season = $2

	if (season == "") {
		season = 0
	}
}

/^<a href="guide.shtml#[0-9].*Series/ {
	pos = match($0, /guide.shtml#([0-9]+.*">)/)
	season = substr($0, pos + RLENGTH)

	pos = match(season, /[^0-9]/)
	season = substr(season, 0, pos - 1)
}

/^[0-9]+/ {
	# A data file format used for shows like Eureka
	totalep = $1
	epnum = substr($0, index($0, "-")+1, 2)

	if (epnum < 10) {
		epnum = 0 substr(epnum, 2, 1)
	}

	prodnum = substr($0, 16, 9)
	gsub (/^ */, "", prodnum)
	gsub (/ *$/, "", prodnum)

	pos = match($0, /([1-3]?[0-9]\/[A-Z][a-z][a-z]\/[0-9][0-9]) /)
	epdate = substr($0, pos, RLENGTH)
	gsub (/ *$/, "", epdate)
	gsub (/\//, " ", epdate)

	epnameHTML = substr($0, 40)
	pos = index(epnameHTML, ">")
	eptitle = substr(epnameHTML, pos + 1, length(epnameHTML) - pos - 4)
	gsub (/<$/, "", eptitle);
	gsub (/<img.*>/, "", eptitle);

	show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle)
}

/^ *[0-9]+\./ {
	totalep = substr ($1, 0, index($1, "."))
	gsub (/\.$/, "", totalep)
	epnum = substr($0, index($0, "-")+1, 2)

	if (epnum < 10) {
		epnum = 0 substr(epnum, 2, 1)
	}

	prodnum = substr($0, 16, 9)
	gsub (/^ */, "", prodnum)
	gsub (/ *$/, "", prodnum)

	pos = match($0, /([1-3]?[0-9] [A-Z][a-z][a-z] [0-9][0-9]) /)
	epdate = substr($0, pos, RLENGTH)
	gsub (/ *$/, "", epdate)

	epnameHTML = substr($0, 40)
	pos = index(epnameHTML, ">")
	eptitle = substr(epnameHTML, pos + 1, length(epnameHTML) - pos - 4)
	gsub (/<$/, "", eptitle);
	gsub (/<img.*>/, "", eptitle);


	show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle)
}

BEGIN {
	IGNORECASE = 1
	season = 0
	running = "Yes"
}

END {
	print "  running: " running >> output
	if (dropped == 0) { dropped="0" }
	if (kept == 0) { kept="0" }
	printf "Kept %s, dropped %s.\n", kept, dropped
}

function show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle) {
	if (epdate == "") {
		dropped++
		return
	}

	command = "date +%Y-%m-%d -d '" epdate "'"
	command | getline airdate
	close(command)

	gsub("'", "''", eptitle)

	print "  - title: '" eptitle "'" >> output
	print "    season: " season >> output
	print "    episode: " epnum >> output
	print "    airdate: " airdate >> output
	print "    prodnum: '" prodnum "'" >> output
	print "    totalepnum: " totalep >> output

	kept++
}
