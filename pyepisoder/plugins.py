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

from datetime import date, timedelta


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
