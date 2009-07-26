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
import datetime
from sqlalchemy import *
from sqlalchemy.orm import *
import logging

version="0.5.3"

class DataStore(object):
	def __init__(self, path):
		self.logger = logging.getLogger('DataStore')
		engine = create_engine('sqlite:///%s' % path)
		self.conn = engine.connect()
		self.metadata = MetaData()
		self.metadata.bind = engine
		self.session = create_session(bind=engine)
		self.session.begin()
		self._initdb()

	def __str__(self):
		return "DataStore(%s)" % self.conn

	def clear(self):
		episodes = self.session.query(Episode).all()

		for episode in episodes:
			self.session.delete(episode)

		self.session.flush()

	def update(self):
		result = self.meta.select().execute()
		meta = {}

		for key in result:
			meta[key[0]] = key[1]

		if not 'schema' in meta:
			meta['schema'] = '1'

		self.logger.debug("Found v%s schema" % meta['schema'])

		if meta['schema'] == '1':
			self.logger.info("Updating database schema")
			self.shows.drop()
			self.episodes.drop()
			self._initdb()
			self.session.commit()
			self.session.begin()

			meta['schema'] = '2'
			insert = self.meta.insert().values(key='schema',
					value=meta['schema'])
			self.conn.execute(insert)

	def _initdb(self):
		clear_mappers()
		self.shows = Table('shows', self.metadata,
			Column('show_id', Integer,
				Sequence('shows_show_id_seq'),
				primary_key=True),
			Column('show_name', Text),
			Column('url', Text),
			Column('updated', DateTime),
			useexisting=True)
		showmapper = mapper(Show, self.shows, properties={
			'name': self.shows.c.show_name
		})

		self.meta = Table('meta', self.metadata,
			Column('key', Text),
			Column('value', Text),
			useexisting=True)

		self.episodes = Table('episodes', self.metadata,
			Column('show_id', ForeignKey("shows.show_id"),
				primary_key=True),
			Column('num', Integer, primary_key=True),
			Column('airdate', Date),
			Column('season', Integer, primary_key=True),
			Column('title', Text),
			Column('totalnum', Integer),
			Column('prodnum', Text),
			useexisting=True)
		episodemapper = mapper(Episode, self.episodes, properties={
			'title': self.episodes.c.title,
			'season': self.episodes.c.season,
			'episode': self.episodes.c.num,
			'airdate': self.episodes.c.airdate,
			'prodnum': self.episodes.c.prodnum,
			'total': self.episodes.c.totalnum
		})

		self.metadata.create_all()

	def addShow(self, showName, url=''):
		shows = self.session.query(Show) \
				.filter(Show.name == showName) \
				.filter(Show.url == url).all()

		if len(shows) > 0:
			show = shows[0]
		else:
			show = Show(showName, url=url)
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
		self.session.merge(episode)
		self.session.flush()

	def getEpisodes(self, basedate=datetime.date.today(), n_days=0):
		shows = []
		episodes = []

		enddate = basedate + datetime.timedelta(n_days)

		data = self.session.query(Episode).add_entity(Show). \
			select_from(self.episodes.join(self.shows)). \
			filter(Episode.airdate >= basedate). \
			filter(Episode.airdate <= enddate). \
			order_by(Episode.airdate)

		for row in data:
			(episode, show) = row
			episode.show = show

			if show in shows:
				show = shows[shows.index(show)]
			else:
				shows.append(show)

			#episode.airdate = datetime.datetime.strptime(
			#		episode.airdate, "%Y-%m-%d").date()
#			episode = Episode(show, ep.title, ep.season, ep.episode,
#					ep.airdate, ep.prodnum, ep.total)
			episodes.append(episode)

		return episodes

	def search(self, options):
		shows = []
		episodes = []

		search = options['search']

		data = self.session.query(Episode).add_entity(Show). \
			select_from(self.episodes.join(self.shows)). \
			filter(or_( \
				Episode.title.like('%%%s%%' % search),
				Show.name.like('%%%s%%' % search))). \
			order_by(Episode.airdate)

		for row in data:
			(episode, show) = row
			episode.show = show

			if show in shows:
				show = shows[shows.index(show)]
			else:
				shows.append(show)

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

class Episode(object):
	def __init__(self, show, title, season, episode, airdate, prodnum,
			total):
		assert isinstance(show, Show)
		self.show = show
		self.title = title
		self.season = int(season)
		self.episode = int(episode)
		self.airdate = airdate
		self.prodnum = str(prodnum)
		self.total = int(total)

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
		return "%s %dx%02d: %s" % (self.show.name, self.season,
			self.episode, self.title)

	def __eq__(self, other):
		return (self.show == other.show and
			self.season == other.season and
			self.episode == other.episode)

	airdate = property(getAirDate, setAirDate)
	season = property(_getSeason, _setSeason)
	episode = property(_getEpisode, _setEpisode)
	total = property(_getTotal, _setTotal)

class Show(object):
	def __init__(self, name, id=-1, url='',updated=datetime.datetime.now()):
		self.name = name
		self.url = url
		self.updated = updated
		self.episodes = []

	def addEpisode(self, episode):
		self.episodes.append(episode)

	def __str__(self):
		return 'Show("%s")' % self.name

	def __eq__(self, other):
		return (self.name == other.name and
			self.url == other.url)
