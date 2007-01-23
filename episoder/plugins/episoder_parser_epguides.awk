/<html>.*<head>/ {
	# Some files don't have proper linebreaks - they'll have <html> and
	# <head> on the same line
	titleStart = index($0, "<title>") + 8;
	titlePart = substr($0, titleStart);

	titleEnd = index($0, "(a Titles ");

	set_show(substr($0, titleStart, titleEnd - titleStart - 1));
}

/^<meta name="description"/ {
	start = index($0, "of the TV series") + 17;
	end = index($0, ".\"");
	set_show(substr($0, start, end - start));
}

/^<META NAME="description"/ {
	start = index($0, "of the TV series") + 17;
	end = index($0, ".\"");
	set_show(substr($0, start, end - start));
}

function set_show(showName) {
	if (SHOW_NAME == "") {
		show = showName
	} else {
		show = SHOW_NAME
	}

	if (VERBOSE == "true") {
		printf " %s...", show
	}
	if (VERY_VERBOSE == "true") {
		printf "\n"
	}
}

/^Season/ {
	season = strtonum($2)
}

/^ *[0-9]+\./ {
	totalep = substr ($1, 0, index($1, "."))
	epnum = substr($0, 10, 2)
	if (epnum < 10) {
		epnum = 0 substr(epnum, 2, 1)
	}

	prodnum = substr($0, 16, 9)
	epdate = substr($0, 28, 10)
	gsub (/ *$/, "", epdate)
	epnameHTML = substr($0, 40)
	fooIndex = index(epnameHTML, ">")
	eptitle = substr(epnameHTML, fooIndex + 1, length(epnameHTML) - fooIndex - 4)
	
	show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle)
}

BEGIN {
	IGNORECASE = 1
}

END {
	if (VERBOSE == "true") {
		if (dropped == 0) { dropped="0" }
		if (kept == 0) { kept="0" }
		printf "Kept %s, dropped %s. ",kept,dropped
	}
}

function show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle) {
	if (epdate == "") {
		dropped++
		return
	}
	output = format
	command = "date +%Y-%m-%d -d '" epdate "'"
	command | getline airdate
	gsub("&", "and", eptitle)
	gsub("&", "and", show)
	gsub("%show", show, output)
	gsub("%totalep", totalep, output)
	gsub("%season", season, output)
	gsub("%epnum", epnum, output)
	gsub("%prodnum", prodnum, output)
	gsub("%airdate", airdate, output)
	gsub("%eptitle", eptitle, output)
	if (VERBOSE == "true") {
		kept++
	}
	if (VERY_VERBOSE == "true") {
		print "Found " output
	}
	print output >> TMPFILE
}
