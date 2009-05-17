# episoder, http://episoder.sourceforge.net/
#
# Copyright (C) 2004-2009 Stefan Ott. All rights reserved.
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

import sys
import sqlite3
import logging
import datetime

version="0.5.0"

class DataStore(object):
	def __init__(self, path):
		self.logger = logging.getLogger('DataStore')
		self.conn = sqlite3.connect(path)

	def clear(self):
		try:
			self._initdb()
		except sqlite3.OperationalError, msg:
			self.logger.error(msg)
			self.logger.error('If you have an old episoder data ' +
				'file, please move it away')
			sys.stderr.write('ERROR\n')
			sys.exit(10)

	def _initdb(self):
		self.conn.execute('DROP TABLE IF EXISTS shows')
		self.conn.execute('CREATE TABLE shows (show_id INTEGER ' +
			'PRIMARY KEY, show_name TEXT)')

		self.conn.execute('DROP TABLE IF EXISTS episodes')
		self.conn.execute('CREATE TABLE episodes (show_id INTEGER,' +
				' num INTEGER, airdate TEXT, season INTEGER,' +
				' title TEXT, totalnum INTEGER, prodnum TEXT)')

	def addShow(self, show):
		result = self.conn.execute('INSERT INTO shows VALUES (NULL, ?)',
				[show])
		return result.lastrowid

	def getShows(self):
		shows = self.conn.execute('SELECT * FROM shows')
		return shows.fetchall()

	def getEpisodes(self, basedate=datetime.date.today(), n_days=0):
		episodes = []
		result = self.conn.execute('SELECT show_id, show_name, title,' +
			'season, num, airdate, prodnum, totalnum FROM ' +
			'episodes NATURAL JOIN shows WHERE airdate >= ? AND ' +
			'airdate <= ? ORDER BY airdate ASC', [basedate,
				basedate + datetime.timedelta(n_days)])

		shows = []
		episodes = []

		for item in result.fetchall():
			show = Show(item[1], item[0])
			if show in shows:
				show = shows[shows.index(show)]
			else:
				shows.append(show)

			airdate = datetime.datetime.strptime(item[5],"%Y-%m-%d")

			episode = Episode(show, item[2], item[3], item[4],
				airdate.date(), item[6], item[7])
			episodes.append(episode)

		return episodes

	def addEpisode(self, show, episode):
		num = episode.episode
		airdate = episode.airdate
		season = episode.season
		title = episode.title
		totalnum = episode.total
		prodnum = episode.prodnum

		self.conn.execute('INSERT INTO episodes VALUES (?, ?, ?, ?,' +
				'?, ?, ?)', [show, num, airdate, season, title,
					totalnum, prodnum])

	def commit(self):
		self.conn.commit()

	def rollback(self):
		self.conn.rollback()

	def removeBefore(self, date):
		self.conn.execute('DELETE FROM episodes WHERE airdate < ?',
				[date.isoformat()])
		self.commit()

class Episode(object):
	def __init__(self, show, title, season, episode, airdate, prodnum,
			total):
		self.show = show
		self.title = str(title)
		self.season = int(season)
		self.episode = int(episode)
		self.airdate = airdate
		self.prodnum = str(prodnum)
		self.total = int(total)

	def _setAirDate(self, airdate):
		self._airdate = airdate.isoformat()

	def _getAirDate(self):
		return self._airdate

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
		return "%s %dx%02d: %s" % (self.show.name, self.season,
				self.episode, self.title)

	airdate = property(_getAirDate, _setAirDate)
	season = property(_getSeason, _setSeason)
	episode = property(_getEpisode, _setEpisode)
	total = property(_getTotal, _setTotal)

class Show(object):
	def __init__(self, name, id=-1):
		self.name = name
		self.episodes = []

	def addEpisode(self, episode):
		self.episodes.append(episode)

	def __str__(self):
		return 'Show("%s")' % self.name

	def __eq__(self, other):
		return self.name == other.name
