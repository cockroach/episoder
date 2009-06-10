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
from sqlalchemy import *
from sqlalchemy.orm import join, mapper, clear_mappers, sessionmaker, create_session

version="0.5.0"

class DataStore(object):
	def __init__(self, path):
		#self.engine = 'postgres'
		#self.host = 'localhost'
		#self.user = 'webisoder'
		#self.pw = 'webisoder'
		#self.name = 'webisoder'

		#self.db = create_engine('%s://%s:%s@%s/%s' % (
		#	self.engine, self.user, self.pw, self.host, self.name
		#))
		engine = create_engine('sqlite:///%s' % path)
		self.conn = engine.connect()
		self.metadata = MetaData()
		self.metadata.bind = engine
		self.session = create_session(bind=engine)
		self.session.begin()

	def clear(self):
		self._initdb()

	def _initdb(self):
		clear_mappers()
		self.shows = Table('shows', self.metadata,
			Column('show_id', Integer,
			Sequence('shows_show_id_seq'), primary_key=True),
			Column('show_name', String))
		self.shows.create()
		showmapper = mapper(Show, self.shows, properties={
			'name': self.shows.c.show_name,
		})

		self.episodes = Table('episodes', self.metadata,
			Column('show_id', ForeignKey("shows.show_id"), primary_key=True),
			Column('num', Integer, primary_key=True),
			Column('airdate', Text),
			Column('season', Integer, primary_key=True),
			Column('title', Text),
			Column('totalnum', Integer),
			Column('prodnum', Text))
		self.episodes.create()
		episodemapper = mapper(Episode, self.episodes, properties={
			'title': self.episodes.c.title,
			'season': self.episodes.c.season,
			'episode': self.episodes.c.num,
			'airdate': self.episodes.c.airdate,
			'prodnum': self.episodes.c.prodnum,
			'total': self.episodes.c.totalnum
		})

	def addShow(self, showName):
		show = Show(showName)
		self.session.add(show)
		self.session.flush()
		return show.show_id

	def getShows(self):
		select = self.shows.select()
		result = select.execute()

		shows = []

		for show in result:
			shows.append((show.show_id, show.show_name))

		return shows

	def addEpisode(self, show_id, episode):
		episode.show_id = show_id
		self.session.add(episode)
		self.session.flush()
		return

	def getEpisodes(self, basedate=datetime.date.today(), n_days=0):
		joined = join(self.episodes, self.shows)
		select = joined.select(use_labels=True)
		result = select.execute()

		shows = []
		episodes = []

		query = self.session.query(joined)
		query = query.filter(Episode.airdate >= basedate)
		query = query.filter(Episode.airdate <= basedate +
				datetime.timedelta(n_days))

		for row in query.all():
			show = Show(row.show_name, row.show_id)
			if show in shows:
				show = shows[shows.index(show)]
			else:
				shows.append(show)
			airdate = datetime.datetime.strptime(
					row.airdate, "%Y-%m-%d")

			episode = Episode(show, row.title, row.season, row.num,
					airdate, row.prodnum, row.totalnum)
			episodes.append(episode)

		return episodes

	def search(self, options):
		search = options['search']
		joined = join(self.episodes, self.shows)

		query = self.session.query(joined).filter(or_(
			Episode.title.like('%%%s%%' % search),
			Show.name.like('%%%s%%' % search)))

		shows = []
		episodes = []

		for row in query.all():
			show = Show(row.show_name, row.show_id)
			if show in shows:
				show = shows[shows.index(show)]
			else:
				shows.append(show)
			airdate = datetime.datetime.strptime(
					row.airdate, "%Y-%m-%d")

			episode = Episode(show, row.title, row.season, row.num,
					airdate, row.prodnum, row.totalnum)
			episodes.append(episode)

		return episodes

	def commit(self):
		self.session.commit()
		self.session.begin()

	def rollback(self):
		self.session.rollback()
		self.session.begin()

	def removeBefore(self, date):
		episodes = self.session.query(Episode).filter(
				Episode.airdate < date).all()

		for episode in episodes:
			self.session.delete(episode)

		self.commit()

class DataStore2(object):
	def __init__(self, path):
		self.logger = logging.getLogger('DataStore')
		self.conn = sqlite3.connect(path)

	def clear(self):
		self._initdb()

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

	def getEpisodes(self, basedate=datetime.date.today(), n_days=0):
		result = self.conn.execute("""
			SELECT show_id, show_name, title, season, num, airdate,
			prodnum, totalnum FROM episodes NATURAL JOIN shows WHERE
			airdate >= ? AND airdate <= ? ORDER BY airdate ASC
			""", [basedate, basedate + datetime.timedelta(n_days)])

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

	def search(self, options):
		search = options['search']

		result = self.conn.execute("""
			SELECT show_id, show_name, title, season, num, airdate,
			prodnum, totalnum FROM episodes NATURAL JOIN shows WHERE
			title LIKE "%%%s%%" OR show_name LIKE "%%%s%%" ORDER BY
			airdate ASC
			""" % (search, search))

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
		assert isinstance(show, Show)
		self.show = show
		self.title = str(title)
		self.season = int(season)
		self.episode = int(episode)
		self.airdate = airdate
		self.prodnum = str(prodnum)
		self.total = int(total)

	def _setAirDate(self, airdate):
		# meh, hack to make sure that we actually get a date object
		airdate.isoformat()
		self._airdate = airdate

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

	def __eq__(self, other):
		return (self.show == other.show and
			self.season == other.season and
			self.episode == other.episode)

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
