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

import sqlite3
from sqlalchemy import Table, MetaData, create_engine, or_, and_
from sqlalchemy.orm import create_session

from .database import Episode, Show, Meta


class Database(object):

	def __init__(self, path):

		self._path = path
		self.logger = logging.getLogger("Database")

		self.open()
		self._initdb()

	def __str__(self):

		return "Episoder Database at %s" % self._path

	def __repr__(self):

		return "Database(%s)" % self._path

	def _initdb(self):

		# Initialize the database if all tables are missing
		tables = [Show, Episode, Meta]
		tables = map(lambda x: x.__table__.exists, tables)
		found = [x for x in tables if x(bind=self.engine)]

		if len(found) < 1:
			Show.__table__.create(bind=self.engine)
			Episode.__table__.create(bind=self.engine)
			Meta.__table__.create(bind=self.engine)
			self.set_schema_version(4)

	def open(self):

		if self._path.find("://") > -1:
			self.engine = create_engine(self._path,
							convert_unicode=True)
		else:
			self.engine = create_engine("sqlite:///%s" % self._path)

		self.conn = self.engine.connect()
		self.metadata = MetaData()
		self.metadata.bind = self.engine
		self.session = create_session(bind=self.engine)
		self.session.begin()

	def close(self):

		self.session.commit()
		self.session.close()
		self.conn.close()
		self.engine.dispose()

	def set_schema_version(self, version):

		meta = Meta()
		meta.key = "schema"
		meta.value = "%d" % version

		self.session.merge(meta)
		self.session.flush()

	def get_schema_version(self):

		if not Meta.__table__.exists(bind=self.engine):
			return 1

		res = self.session.query(Meta).get("schema")
		if res:
			return int(res.value)

		return 0

	def clear(self):

		episodes = self.session.query(Episode).all()

		for episode in episodes:
			self.session.delete(episode)

		self.session.flush()

	def migrate(self):

		schema_version = self.get_schema_version()
		self.logger.debug("Found schema version %s", schema_version)

		if schema_version < 0:

			self.logger.debug("Automatic schema updates disabled")
			return

		if schema_version == 1:

			# Upgrades from version 1 are rather harsh, we
			# simply drop and re-create the tables
			self.logger.debug("Upgrading to schema version 2")

			table = Table("episodes", self.metadata, autoload=True)
			table.drop()

			table = Table("shows", self.metadata, autoload=True)
			table.drop()

			Show.__table__.create(bind=self.engine)
			Episode.__table__.create(bind=self.engine)
			Meta.__table__.create(bind=self.engine)

			schema_version = 4
			self.set_schema_version(schema_version)

		if schema_version == 2:

			# Add two new columns to the shows table
			self.logger.debug("Upgrading to schema version 3")

			# We can only do this with sqlite databases
			assert self.engine.driver == "pysqlite"

			self.close()

			upgrade = sqlite3.connect(self._path)
			upgrade.execute("ALTER TABLE shows "
					"ADD COLUMN enabled TYPE boolean")
			upgrade.execute("ALTER TABLE shows "
					"ADD COLUMN status TYPE integer")
			upgrade.close()

			self.open()
			schema_version = 3
			self.set_schema_version(schema_version)

		if schema_version == 3:

			# Add a new column to the episodes table
			self.logger.debug("Upgrading to schema version 4")

			# We can only do this with sqlite databases
			assert self.engine.driver == "pysqlite"

			self.close()

			upgrade = sqlite3.connect(self._path)
			upgrade.execute("ALTER TABLE episodes "
					"ADD COLUMN notified TYPE date")
			upgrade.close()

			self.open()
			schema_version = 4
			self.set_schema_version(schema_version)

	def get_expired_shows(self, today=date.today()):

		delta_running = timedelta(2)	# 2 days
		delta_suspended = timedelta(7)	# 1 week
		delta_ended = timedelta(14)	# 2 weeks

		shows = self.session.query(Show).filter(or_(
				and_(
					Show.enabled,
					Show.status == Show.RUNNING,
					Show.updated < today - delta_running
				),
				and_(
					Show.enabled,
					Show.status == Show.SUSPENDED,
					Show.updated < today - delta_suspended
				),
				and_(
					Show.enabled,
					Show.status == Show.ENDED,
					Show.updated < today - delta_ended
				)
		))

		return shows.all()

	def get_enabled_shows(self):

		shows = self.session.query(Show).filter(Show.enabled)
		return shows.all()

	def get_show_by_url(self, url):

		shows = self.session.query(Show).filter(Show.url == url)

		if shows.count() < 1:
			return None

		return shows.first()

	def get_show_by_id(self, show_id):

		return self.session.query(Show).get(show_id)

	def add_show(self, show):

		show = self.session.merge(show)
		self.session.flush()
		return show

	def remove_show(self, show_id):

		show = self.session.query(Show).get(show_id)

		if not show:
			self.logger.error("No such show")
			return

		episodes = self.session.query(Episode)

		for episode in episodes.filter(Episode.show_id == show.id):
			self.session.delete(episode)

		self.session.delete(show)
		self.session.flush()

	def get_shows(self):

		return self.session.query(Show).all()

	def add_episode(self, episode, show):

		episode.show_id = show.id
		self.session.merge(episode)
		self.session.flush()

	def get_episodes(self, basedate=date.today(), n_days=0):

		enddate = basedate + timedelta(n_days)

		return self.session.query(Episode).\
			filter(Episode.airdate >= basedate). \
			filter(Episode.airdate <= enddate). \
			order_by(Episode.airdate).all()

	def search(self, search):

		return self.session.query(Episode).\
			filter(or_( \
				Episode.title.like("%%%s%%" % search),
				Show.name.like("%%%s%%" % search))). \
			order_by(Episode.airdate).all()

	def commit(self):

		self.session.commit()
		self.session.begin()

	def rollback(self):

		self.session.rollback()
		self.session.begin()

	def remove_before(self, then, show=None):

		eps = self.session.query(Episode).filter(Episode.airdate < then)

		if show:
			eps = eps.filter(Episode.show == show)

		for episode in eps:
			self.session.delete(episode)

		self.commit()
