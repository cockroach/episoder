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

import logging

from datetime import datetime

from sqlalchemy import Column, Integer, Text, Date, ForeignKey, Sequence
from sqlalchemy import DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class Show(Base):

	RUNNING = 1
	SUSPENDED = 2
	ENDED = 3

	__tablename__ = "shows"

	id = Column("show_id", Integer, Sequence("shows_show_id_seq"),
							primary_key=True)
	name = Column("show_name", Text)
	url = Column(Text, unique=True)
	updated = Column(DateTime)
	enabled = Column(Boolean)
	status = Column(Integer, default=RUNNING)

	def __init__(self, name, url=u"", updated=datetime.fromtimestamp(0)):

		self.name = name
		self.url = url
		self.updated = updated
		self.status = Show.RUNNING
		self.episodes = []
		self.enabled = True

	def __str__(self):

		return "Show: %s" % self.name

	def __repr__(self):

		return 'Show(u"%s", u"%s")' % (self.name, self.url)

	def __eq__(self, other):

		return self.name == other.name and self.url == other.url

	def remove_episodes_before(self, store, date):

		logging.debug("Removing episodes from before %s", date)
		store.remove_before(date, show=self)


class Episode(Base):

	__tablename__ = "episodes"

	show_id = Column(Integer, ForeignKey(Show.id), primary_key=True)
	episode = Column("num", Integer, primary_key=True)
	airdate = Column(Date)
	season = Column(Integer, primary_key=True)
	title = Column(Text)
	totalnum = Column(Integer)
	prodnum = Column(Text)
	notified = Column(Date)
	show = relationship(Show, backref=backref("episodes", cascade="all"))

	def __init__(self, name, season, episode, aired, prodnum, total):

		self.title = name
		self.season = int(season)
		self.episode = int(episode)
		self.airdate = aired
		self.prodnum = prodnum
		self.totalnum = int(total)

	def __lt__(self, other):

		return ((self.season < other.season)
			or ((self.season == other.season)
				and (self.episode < other.episode)))

	def __str__(self):

		return "%s %dx%02d: %s" % (self.show.name, self.season,
			self.episode, self.title)

	def __repr__(self):

		return 'Episode(u"%s", %d, %d, date(%d, %d, %d), u"%s", %d)' % (
				self.title, self.season, self.episode,
				self.airdate.year, self.airdate.month,
				self.airdate.day, self.prodnum, self.totalnum)

	def __eq__(self, other):

		return (self.show_id == other.show_id
			and self.season == other.season
			and self.episode == other.episode)


class Meta(Base):

	__tablename__ = "meta"
	key = Column(Text, primary_key=True)
	value = Column(Text)

	def __str__(self):

		return "Meta: %s = %s" % (self.key, self.value)

	def __repr__(self):

		return str(self)
