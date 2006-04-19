/<span class="f-18 f-bold">All Seasons<\/span>/ {
	parse = "true"
	season = 0
}
/<span class="f-18 f-bold">Season .*<\/span>/ {
	parse = "true"
	season = substr($0, 38, index($0, "</span>") - 38)
}
/<\/div id="main-col">/ { parse = "false" }
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
/summary.html">/ {
	if (parse == "true") {
		start = index($0, "summary.html") + 14
		end = index($0, "</a>") - start
		eptitle = substr($0, start, end)
	}
}
/[0-9]\/[0-9][0-9]*\/[0-9]*$/ {
	epdate = $1
}
/ *[-_a-zA-Z0-9]$/ {
	if (prodnum_coming == "true") {
		# assuming the prod# never contains spaces
		prodnum = $1
		prodnum_coming = "false"
	}
}
/[a-zA-Z0-9]$/ {
	if (epnum_coming == "true") {
		totalep = $1
		if (! firstep) {
			firstep = totalep
		}
		if (season == 0) {
			epnum = 0
		} else {
			epnum = totalep - (firstep - 1)
			if (epnum < 10) epnum = 0 epnum
		}
		epnum_coming = "false"
	}
}
/ *<.tr>$/ {
	if (parse == "true" && epnum != "") {
		if (epdate != "0/0/0") {
			show_episode(show,totalep,season,epnum,prodnum,epdate,eptitle)
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
		epnum = ""
	}
}
/^ *$/ {
	prodnum_coming = "false"
	epnum_coming = "false"
}
/<td class="f-666 f-11 ta-c" style="width:1%;">/ {
	prodnum_coming = "true"
}
/<td class="first f-bold ta-c" style="width:1%;" nowrap="nowrap">/ {
	epnum_coming = "true"
}

END {
	if (VERBOSE == "true") {
		if (dropped == 0) { dropped="0" }
		if (kept == 0) { kept="0" }
		printf "Kept %s, dropped %s. ",kept,dropped
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
