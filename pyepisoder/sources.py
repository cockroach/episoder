# episoder, https://github.com/cockroach/episoder
#
# Copyright (C) 2004-2017 Stefan Ott. All rights reserved.
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

import json
import logging
import requests

from re import search, match
from datetime import datetime

from .episoder import Show
from .episode import Episode


def parser_for(url):

	parsers = [ TVDB, EpguidesParser, TVComDummyParser ]

	for parser in parsers:
		if parser.accept(url):
			return parser()

	return None


class InvalidLoginError(Exception):

	pass


class TVDBShowNotFoundError(Exception):

	pass


class TVDBNotLoggedInError(Exception):

	pass


class TVDBOffline(object):

	def __init__(self, tvdb):

		self._tvdb = tvdb

	def _post_login(self, data):

		url = "https://api.thetvdb.com/login"
		headers = {"Content-type": "application/json"}
		body = json.dumps(data).encode("utf8")
		response = requests.post(url, body, headers=headers)
		data = response.json()

		if response.status_code == 401:
			raise InvalidLoginError(data.get("Error"))

		return data.get("token")

	def lookup(self, text):

		raise TVDBNotLoggedInError()

	def login(self, args):

		body = {"apikey": args.tvdb_key}
		self.token = self._post_login(body)

	def parse(self, show, db):

		raise TVDBNotLoggedInError()

	def _set_token(self, token):

		self._tvdb.change(TVDBOnline(token))

	token = property(None, _set_token)


class TVDBOnline(object):

	def __init__(self, token):

		self._token = token
		self._logger = logging.getLogger("TVDB (online)")

	def _get(self, url, params):

		url = "https://api.thetvdb.com/%s" % url
		head = {"Content-type": "application/json",
			"Authorization": "Bearer %s" % self._token}
		response = requests.get(url, headers = head, params = params)
		data = response.json()

		if response.status_code == 404:
			raise TVDBShowNotFoundError(data.get("Error"))

		return data

	def _get_episodes(self, show, page):

		id = int(show.url)
		result = self._get("series/%d/episodes" % id, {"page": page})
		return (result.get("data"), result.get("links"))

	def lookup(self, term):

		def mkshow(entry):

			name = entry.get("seriesName")
			url = str(entry.get("id")).encode("utf8").decode("utf8")
			return Show(name, url=url)

		matches = self._get("search/series", {"name": term})
		return map(mkshow, matches.get("data"))

	def login(self, args):

		pass

	def _fetch_episodes(self, show, page=1):

		def mkepisode(row):

			num = int(row.get("airedEpisodeNumber", "0"))
			aired = row.get("firstAired")
			name = row.get("episodeName") or u"Unnamed episode"
			season = int(row.get("airedSeason", "0"))
			aired = datetime.strptime(aired, "%Y-%m-%d").date()
			pnum = u"UNK"

			self._logger.debug("Found episode %s" % name)
			return Episode(show, name, season, num, aired, pnum, 0)

		def isvalid(row):

			return row.get("firstAired") not in [None, ""]

		(data, links) = self._get_episodes(show, page)
		valid = filter(isvalid, data)
		episodes = [mkepisode(row) for row in valid]

		# handle pagination
		next_page = links.get("next") or 0
		if next_page > page:
			episodes.extend(self._fetch_episodes(show, next_page))

		return episodes

	def parse(self, show, db):

		result = self._get("series/%d" % int(show.url), {})
		data = result.get("data")

		# update show data
		show.name = data.get("seriesName", show.name)
		show.updated = datetime.now()

		if data.get("status") == "Continuing":
			show.setRunning()
		else:
			show.setEnded()

		# load episodes
		episodes = sorted(self._fetch_episodes(show))
		for (idx, episode) in enumerate(episodes):

			episode.total = idx + 1
			db.addEpisode(episode)

		db.commit()


class TVDB(object):

	def __init__(self):

		self._state = TVDBOffline(self)

	def __str__(self):

		return "thetvdb.com parser"

	def login(self, args):

		self._state.login(args)

	def lookup(self, text):

		return self._state.lookup(text)

	def parse(self, show, db, args):

		return self._state.parse(show, db)

	def change(self, state):

		self._state = state

	@staticmethod
	def accept(url):

		return url.isdigit()


class EpguidesParser(object):

	def __init__(self):

		self.logger = logging.getLogger("EpguidesParser")

	def __str__(self):

		return "epguides.com parser"

	@staticmethod
	def accept(url):

		return "epguides.com/" in url

	def login(self, args):

		pass

	def guess_encoding(self, response):

		raw = response.raw.read()
		text = raw.decode("iso-8859-1")

		if "charset=iso-8859-1" in text:
			return "iso-8859-1"

		return "utf8"

	def parse(self, show, db, args):

		headers = {"User-Agent": args.agent}
		response = requests.get(show.url, headers=headers)
		response.encoding = self.guess_encoding(response)

		for line in response.text.split("\n"):
			self._parse_line(line, show, db)

		show.updated = datetime.now()
		db.commit()

	def _parse_line(self, line, show, db):

		# Name of the show
		match = search("<title>(.*)</title>", line)
		if match:
			title = match.groups()[0]
			show.name = title.split(" (a ")[0]

		# Current status (running / ended)
		match = search('<span class="status">(.*)</span>', line)
		if match:
			text = match.groups()[0]
			if "current" in text:
				show.setRunning()
			else:
				show.setEnded()
		else:
			match = search("aired.*to.*[\d+]", line)
			if match:
				show.setEnded()

		# Known formatting supported by this fine regex:
		# 4.     1-4            19 Jun 02  <a [..]>title</a>
		#   1.  19- 1   01-01    5 Jan 88  <a [..]>title</a>
		# 23     3-05           27/Mar/98  <a [..]>title</a>
		# 65.   17-10           23 Apr 05  <a [..]>title</a>
		# 101.   5-15           09 May 09  <a [..]>title</a>
		# 254.    - 5  05-254   15 Jan 92  <a [..]>title</a>

		match = search("^ *(\d+)\.? +(\d*)- ?(\d+) +([a-zA-Z0-9-]*)"\
		" +(\d{1,2}[ /][A-Z][a-z]{2}[ /]\d{2}) *<a.*>(.*)</a>", line)

		if match:

			fields = match.groups()
			(total, season, epnum, prodnum, day, title) = fields

			day = day.replace("/", " ")
			airtime = datetime.strptime(day, "%d %b %y")

			self.logger.debug("Found episode %s" % title)
			db.addEpisode(Episode(show, title, season or 0, epnum,
						airtime.date(), prodnum, total))


class TVComDummyParser(object):

	def __str__(self):
		return "dummy tv.com parser to detect old urls"

	@staticmethod
	def accept(url):

		exp = "http://(www.)?tv.com/.*"
		return match(exp, url)

	def parse(self, source, db, args):

		logging.error("The url %s is no longer supported" % source.url)

	def login(self):

		pass
