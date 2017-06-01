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

from __future__ import absolute_import

import logging

from datetime import date, datetime, timedelta
from os import fdopen
from re import search, match
from tempfile import mkstemp

import requests

from .episode import Episode
from .sources import TVDB


def parser_for(url):

	parsers = [ TVDB, EpguidesParser, TVComDummyParser ]

	for parser in parsers:
		if parser.accept(url):
			return parser()

	return None


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

		(fd, name) = mkstemp()
		with fdopen(fd, "wb") as file:
			file.write(response.text.encode("utf8"))

		self.logger.debug("Stored in %s" % name)

		with open(name, "rb") as file:
			for line in file:
				self._parse_line(line.decode("utf8"), show, db)

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
		return 'dummy tv.com parser to detect old urls (DO NOT USE)'

	@staticmethod
	def accept(url):

		exp = 'http://(www.)?tv.com/.*'
		return match(exp, url)

	def parse(self, source, db, args):

		logging.error("The url %s is no longer supported" % source.url)

	def login(self):

		pass


class ConsoleRenderer(object):

	def __init__(self, format, dateformat):
		self.logger = logging.getLogger('ConsoleRenderer')
		self.format = format
		self.dateformat = dateformat


	def _render(self, episode, color, endColor):

		string = self.format
		airdate = episode.airdate.strftime(self.dateformat)
		string = string.replace('%airdate', airdate)
		string = string.replace('%show', episode.show.name)
		string = string.replace('%season', str(episode.season))
		string = string.replace('%epnum', "%02d" % episode.episode)
		string = string.replace('%eptitle', episode.title)
		string = string.replace('%totalep', str(episode.total))
		string = string.replace('%prodnum', episode.prodnum)
		print ("%s%s%s" % (color, string, endColor))


	def render(self, episodes, color=True):

		today = date.today()
		yesterday = today - timedelta(1)
		tomorrow = today + timedelta(1)

		if color:
			red = '\033[31;1m'
			cyan = '\033[36;1m'
			grey = '\033[30;0m'
			green = '\033[32;1m'
			yellow = '\033[33;1m'
		else:
			red = ''
			cyan = ''
			grey = ''
			green = ''
			yellow = ''

		for episode in episodes:
			if episode.airdate == yesterday:
				color = red
			elif episode.airdate == today:
				color = yellow
			elif episode.airdate == tomorrow:
				color = green
			elif episode.airdate > tomorrow:
				color = cyan
			else:
				color = grey

			self._render(episode, color, grey)
