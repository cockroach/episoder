/<h3 class="pl-5">All Seasons<\/h3>/ { parse = "true" }
/<div class="gray-box pod cb ml-10 mb-10 f-bold f-med-gray f-12">/ { parse = "false" }
/<title>.*Episode List/ {
	start = index($0, "<title>") + 7
	end = index($0, " Episode List") - start
	show = substr($0, start, end)
	if (VERBOSE == "true") {
		printf " %s... ",show
	}
	if (VERY_VERBOSE == "true") {
		printf "\n"
	}
	
}
/^ *[a-zA-Z0-9]+: *$/ {
	if (parse == "true") {
		epnum = substr($1,1,index($1,":")-1)
	}
}
/&nbsp;<\/strong>/ { 
	eptitle = substr($0, 22, index($0, "&nbsp;</strong>") - 22)
}
/[0-9]\/[0-9][0-9]*\/[0-9]*$/ {
	epdate = $1
}
/[-_a-zA-Z0-9] *<\/td>$/ {
	# assuming the prod# never contains spaces
	prodnum = $1
}
/([0-9] - [0-9])/ {
	episode = substr($0, 121, index($0, "</td>") - 121)
	split(episode, fields, / - /)
	season = fields[1]
	episode = fields[2]
	if (episode < 10) episode = 0 episode

	if (epdate != "0/0/0") {
		show_episode(show,epnum,season,episode,prodnum,epdate,eptitle)
		if (VERBOSE == "true") {
			kept++
		}
		if (VERY_VERBOSE == "true") {
			printf "Keeping %s %sx%s - %s\n",show,season,episode,eptitle
		}
	} else {
		if (VERBOSE == "true") {
			dropped++
		}
		if (VERY_VERBOSE == "true") {
			printf "Dropping %s %sx%s - %s\n",show,season,episode,eptitle
		}
	}
	prodnum = ""
	epdate = ""
}

END { 
	if (VERBOSE == "true") {
	if (dropped == 0) { dropped="0" }
	if (kept == 0) { kept="0" }
		printf "Keeping %s.  Dropping %s.  ",kept,dropped
	}
}

function show_episode(show, totalep, season, epnum, prodnum, epdate, eptitle) {
	output = format
	command = "date +%Y-%m-%d -d " epdate
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
	print output >> TMPFILE
}
