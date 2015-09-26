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

from __future__ import absolute_import

from datetime import date, timedelta
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer
from sqlalchemy import MetaData, Sequence, Table, Text
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import clear_mappers, create_session, mapper, relation

import logging

from .episode import Episode
from .plugins import parser_for

version='0.7.2'


class DataStore(object):

	def __init__(self, path):

		self.logger = logging.getLogger('DataStore')

		if path.find('://') > -1:
			engine = create_engine(path, convert_unicode=True)
		else:
			engine = create_engine('sqlite:///%s' % path)

		self.conn = engine.connect()
		self.metadata = MetaData()
		self.metadata.bind = engine
		self.session = create_session(bind=engine)
		self.session.begin()
		self._initdb()


	def __str__(self):

		return 'DataStore(%s)' % self.conn


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

		self.logger.debug('Found v%s schema' % meta['schema'])

		if meta['schema'] == '-1':
			self.logger.debug('Automatic schema updates disabled')
			return

		if meta['schema'] < '3':
			self.logger.info('Updating database schema')
			self.episodes.drop()
			self.shows.drop()
			self._initdb()
			self.session.commit()
			self.session.begin()

			insert = self.meta.insert().values(key='schema',
					value=3)
			self.conn.execute(insert)


	def _initdb(self):

		clear_mappers()

		self.shows = Table('shows', self.metadata,
			Column('show_id', Integer,
				Sequence('shows_show_id_seq'),
				primary_key=True),
			Column('show_name', Text),
			Column('url', Text, unique=True),
			Column('updated', DateTime),
			Column('enabled', Boolean),
			Column('status', Integer, default=Show.RUNNING),
			extend_existing=True)

		showmapper = mapper(Show, self.shows, properties={
			'name': self.shows.c.show_name,
			'episodes': relation(Episode, backref='show',
				cascade='all')
		})

		self.meta = Table('meta', self.metadata,
			Column('key', Text, primary_key=True),
			Column('value', Text),
			extend_existing=True)

		self.episodes = Table('episodes', self.metadata,
			Column('show_id', ForeignKey('shows.show_id'),
				primary_key=True),
			Column('num', Integer, primary_key=True),
			Column('airdate', Date),
			Column('season', Integer, primary_key=True),
			Column('title', Text),
			Column('totalnum', Integer),
			Column('prodnum', Text),
			extend_existing=True)

		episodemapper = mapper(Episode, self.episodes, properties={
			'title': self.episodes.c.title,
			'season': self.episodes.c.season,
			'episode': self.episodes.c.num,
			'airdate': self.episodes.c.airdate,
			'prodnum': self.episodes.c.prodnum,
			'total': self.episodes.c.totalnum
		})

		self.metadata.create_all()


	def getExpiredShows(self):

		today = date.today()
		deltaRunning = timedelta(2)	# 2 days
		deltaSuspended = timedelta(7)	# 1 week
		deltaNotRunning = timedelta(14)	# 2 weeks

		shows = self.session.query(Show).filter(or_(
				and_(
					Show.enabled == True,
					Show.status == Show.RUNNING,
					Show.updated < today - deltaRunning
				),
				and_(
					Show.enabled == True,
					Show.status == Show.SUSPENDED,
					Show.updated < today - deltaSuspended
				),
				and_(
					Show.enabled == True,
					Show.status == Show.ENDED,
					Show.updated < today - deltaNotRunning
				)
		))

		return shows.all()


	def getEnabledShows(self):

		shows = self.session.query(Show).filter(Show.enabled == True)
		return shows.all()


	def getShowByUrl(self, url):

		shows = self.session.query(Show).filter(Show.url == url)

		if shows.count() < 1:
			return None

		return shows.first()


	def getShowById(self, id):

		shows = self.session.query(Show).filter(Show.show_id == id)

		if shows.count() < 1:
			return None

		return shows.first()


	def addShow(self, show):

		show = self.session.merge(show)
		self.session.flush()
		return show


	def removeShow(self, id):

		shows = self.session.query(Show).filter(Show.show_id == id)

		if shows.count() < 1:
			self.logger.error('No such show')
			return

		self.session.delete(shows.first())
		self.session.flush()


	def getShows(self):

		select = self.shows.select()
		result = select.execute()

		shows = []

		for show in result:
			shows.append(show)

		return shows


	def addEpisode(self, episode):

		self.session.merge(episode)
		self.session.flush()


	def getEpisodes(self, basedate=date.today(), n_days=0):

		shows = []
		episodes = []

		enddate = basedate + timedelta(n_days)

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

			episodes.append(episode)

		return episodes


	def search(self, search):

		shows = []
		episodes = []

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


	def removeBefore(self, date, show=None):

		episodes = self.session.query(Episode).filter(
				Episode.airdate < date)

		if show:
			episodes = episodes.filter(
					Episode.show_id == show.show_id)

		for episode in episodes:
			self.session.delete(episode)

		self.commit()


class Show(object):

	RUNNING = 1
	SUSPENDED = 2
	ENDED = 3

	def __init__(self, name, id=-1, url='', updated=date(1970, 1, 1)):

		self.name = name
		self.url = url
		self.updated = updated
		self.status = Show.RUNNING
		self.episodes = []
		self.enabled = True


	def addEpisode(self, episode):

		self.episodes.append(episode)


	def setRunning(self):

		self.status = Show.RUNNING


	def setSuspended(self):

		self.status = Show.SUSPENDED


	def setEnded(self):

		self.status = Show.ENDED


	def update(self, store, args):

		parser = parser_for(self.url)

		if not parser:
			raise RuntimeError('No parser found for %s' % self.url)

		if 'agent' in args:
			parser.user_agent = args.agent

		parser.parse(self, store, args)


	def removeEpisodesBefore(self, store, date):

		logging.debug('Removing episodes from before %s' % date)
		store.removeBefore(date, show=self)


	def __str__(self):

		return 'Show("%s")' % self.name


	def __eq__(self, other):

		return (self.name == other.name and self.url == other.url)
