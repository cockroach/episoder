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

from sys import stdout
from datetime import date, timedelta


class ConsoleRenderer(object):

	RED = "\033[31;1m"
	CYAN = "\033[36;1m"
	GREY = "\033[30;0m"
	GREEN = "\033[32;1m"
	YELLOW = "\033[33;1m"

	def __init__(self, format, dateformat, dest=stdout):

		self._format = format
		self._dateformat = dateformat
		self._dest = dest

	def _render_color(self, text, col):

		self._dest.write("%s%s%s\n" % (col, text, ConsoleRenderer.GREY))

	def _render_no_color(self, string, _):

		self._dest.write("%s\n" % (string))

	def _render(self, episode, render, color):

		string = self._format
		airdate = episode.airdate.strftime(self._dateformat)
		string = string.replace("%airdate", airdate)
		string = string.replace("%show", episode.show.name)
		string = string.replace("%season", str(episode.season))
		string = string.replace("%epnum", "%02d" % episode.episode)
		string = string.replace("%eptitle", episode.title)
		string = string.replace("%totalep", str(episode.total))
		string = string.replace("%prodnum", episode.prodnum)

		render(string, color)

	def render(self, episodes, use_colors=True):

		today = date.today()
		yesterday = today - timedelta(1)
		tomorrow = today + timedelta(1)

		if use_colors:
			render = self._render_color
		else:
			render = self._render_no_color

		for episode in episodes:

			if episode.airdate == yesterday:
				color = ConsoleRenderer.RED
			elif episode.airdate == today:
				color = ConsoleRenderer.YELLOW
			elif episode.airdate == tomorrow:
				color = ConsoleRenderer.GREEN
			elif episode.airdate > tomorrow:
				color = ConsoleRenderer.CYAN
			else:
				color = ConsoleRenderer.GREY

			self._render(episode, render, color)
