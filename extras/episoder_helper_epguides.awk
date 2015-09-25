# episoder epguides.com parser helper
#
# Copyright (C) 2006-2014 Stefan Ott. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

/^<a name='latest' id='latest' \/>&bull; Season/ {
	# remove ^M
	gsub(/\015/, "", $6)

	# Some files come with bullets before the season number and an anchor
	# before the bullet
	season = $6

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
	epnum = int(substr($0, index($0, "-")+1, 2))

	prodnum = substr($0, 16, 9)
	gsub(/^ */, "", prodnum)
	gsub(/ *$/, "", prodnum)

	pos = match($0, /([1-3]?[0-9]\/[A-Z][a-z][a-z]\/[0-9][0-9]) /)
	epdate = substr($0, pos, RLENGTH)
	gsub(/ *$/, "", epdate)
	gsub(/\//, " ", epdate)

	eptitle = substr($0, 40)
	pos = index(eptitle, ">")

	# remove recap and trailer links from html
	sub(/<span class='recap'.*<\/span>/, "", eptitle)
	sub(/<span class='Trailers'.*<\/span>/, "", eptitle)

	# remove href and trailing </a>
	sub(/<a.*href=['"].*['"]>/, "", eptitle)
	sub(/<\/a>/, "", eptitle)

	# remove trailing white spaces
	gsub(/[ \t\f\n\r\v]*$/, "", eptitle)

	show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle)
}

/^ *[0-9]+\./ {
	totalep = substr ($1, 0, index($1, "."))
	gsub (/\.$/, "", totalep)
	epnum = int(substr($0, index($0, "-")+1, 2))

	prodnum = substr($0, 16, 9)
	gsub(/^ */, "", prodnum)
	gsub(/ *$/, "", prodnum)

	pos = match($0, /([1-3]?[0-9] [A-Z][a-z][a-z] [0-9][0-9]) /)
	epdate = substr($0, pos, RLENGTH)
	gsub(/ *$/, "", epdate)

	eptitle = substr($0, 40)
	pos = index(eptitle, ">")

	# remove recap and trailer links from html
	sub(/<span class='recap'.*<\/span>/, "", eptitle)
	sub(/<span class='Trailers'.*<\/span>/, "", eptitle)

	# remove href and trailing </a>
	sub(/<a.*href=['"].*['"]>/, "", eptitle)
	sub(/<\/a>/, "", eptitle)

	# remove trailing white spaces
	gsub(/[ \t\f\n\r\v]*$/, "", eptitle)

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
