# episoder, https://github.com/cockroach/episoder
# -*- coding: utf8 -*-
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

from datetime import date, timedelta
from tempfile import mktemp
from unittest import TestCase, TestSuite, TestLoader
from os import unlink

from pyepisoder.episoder import DataStore, Show
from pyepisoder.episode  import Episode


class ShowTest(TestCase):

	def setUp(self):

		self.path = mktemp()
		self.db = DataStore(self.path)
		self.show = Show(u"A", url=u"a")
		self.show = self.db.addShow(self.show)

	def tearDown(self):

		unlink(self.path)

	def test_remove_episodes_before(self):

		now = date.today()
		then = now - timedelta(3)

		show2 = Show(u"B", url=u"b")
		show2 = self.db.addShow(show2)

		episode1 = Episode(self.show, u"e", 1, 1, now, u"x", 1)
		episode2 = Episode(self.show, u"e", 1, 2, then, u"x", 1)
		episode3 = Episode(show2, u"e", 1, 3, now, u"x", 1)
		episode4 = Episode(show2, u"e", 1, 4, then, u"x", 1)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)
		self.db.addEpisode(episode4)
		self.db.commit()

		episodes = self.db.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(4, len(episodes))

		show2.removeEpisodesBefore(self.db, now)

		episodes = self.db.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(3, len(episodes))

		self.show.removeEpisodesBefore(self.db, now)

		episodes = self.db.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(2, len(episodes))


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(ShowTest))
	return suite
