# episoder, https://github.com/cockroach/episoder
#
# Copyright (C) 2004-2015 Stefan Ott. All rights reserved.
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


class Episode(object):

	def __init__(self, show, name, season, episode, date, prodnum, total):
		self._show = show
		self.title = name
		self.season = int(season)
		self.episode = int(episode)
		self.airdate = date
		self.prodnum = unicode(prodnum)
		self.total = int(total)
		self.show_id = self._show.show_id

	def setAirDate(self, airdate):
		# meh, hack to make sure that we actually get a date object
		airdate.isoformat()
		self.__airdate = airdate

	def getAirDate(self):
		return self.__airdate

	def _setSeason(self, season):
		self._season = int(season)

	def _getSeason(self):
		return self._season

	def _setEpisode(self, episode):
		self._episode = int(episode)

	def _getEpisode(self):
		return self._episode

	def _setTotal(self, total):
		self._total = int(total)

	def _getTotal(self):
		return self._total

	def __str__(self):
		return "%s %dx%02d: %s" % (self._show.name, self.season,
			self.episode, self.title)

	def __eq__(self, other):
		return (self.show_id == other.show_id and
			self.season == other.season and
			self.episode == other.episode)

	def _getShow(self):
		return self._show

	def _setShow(self, show):
		self._show = show
		show.show_id = show.show_id


	airdate = property(getAirDate, setAirDate)
	season = property(_getSeason, _setSeason)
	episode = property(_getEpisode, _setEpisode)
	total = property(_getTotal, _setTotal)
	show = property(_getShow, _setShow)
