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
from os import unlink
from tempfile import mktemp
from unittest import TestCase, TestLoader, TestSuite

from pyepisoder.episoder import DataStore, Show
from pyepisoder.episode import Episode


class DataStoreTest(TestCase):

	def setUp(self):

		self.path = mktemp()
		self.db = DataStore(self.path)

	def tearDown(self):

		unlink(self.path)

	def test_get_show_by_url(self):

		show1 = Show(u"test show", url=u"a")
		show2 = Show(u"test show 2", url=u"b")

		self.db.addShow(show1)
		self.db.addShow(show2)

		self.assertEqual(show1, self.db.getShowByUrl(u"a"))
		self.assertEqual(show2, self.db.getShowByUrl(u"b"))
		self.assertEqual(None, self.db.getShowByUrl(u"c"))

	def test_add_show(self):

		show = Show(u"test show", url=u"http://test.show")
		show = self.db.addShow(show)
		self.db.commit()

		id = show.show_id
		self.assertTrue(id > 0, "id is %d, must be > 0" % id)

		shows = self.db.getShows()
		self.assertEqual(1, len(shows))
		self.assertEqual(id, shows[0].show_id)
		self.assertEqual(u"test show", shows[0].show_name)

		show2 = Show(u"moo show", url=u"http://test.show.2")
		show2 = self.db.addShow(show2)
		id2 = show2.show_id
		self.db.commit()

		shows = self.db.getShows()
		self.assertNotEqual(id, id2)
		self.assertEqual(2, len(shows))

		ids = [x.show_id for x in shows]
		self.assertTrue(id2 in ids)

		showA = Show(u"showA", url=u"urlA")
		showB = Show(u"showA", url=u"urlB")
		showC = Show(u"showB", url=u"urlB")

		self.db.addShow(showA)
		self.db.commit()
		self.assertEqual(3, len(self.db.getShows()))

		self.db.addShow(showB)
		self.db.commit()
		self.assertEqual(4, len(self.db.getShows()))

		with self.assertRaises(Exception):
			self.db.addShow(showC)
			self.db.commit()

	def test_add_episode(self):

		show = Show(u"some show", url=u"foo")
		show = self.db.addShow(show)
		self.db.commit()

		episode1 = Episode(show, u"Some episode", 3, 10, date.today(),
								u"FOO", 30)
		episode2 = Episode(show, u"No episode", 3, 12, date.today(),
								u"FOO", 32)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.commit()

		episodes = self.db.getEpisodes()
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def test_search(self):

		show = Show(u"some show")
		show = self.db.addShow(show)
		episode1 = Episode(show, u"first episode", 3, 10, date.today(),
								u"FOO", 30)
		episode2 = Episode(show, u"Second episode", 3, 12, date.today(),
								u"FOO", 32)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.commit()

		episodes = self.db.search(u"first")
		self.assertTrue(episode1 in episodes)
		self.assertFalse(episode2 in episodes)

		episodes = self.db.search(u"second")
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.db.search(u"episode")
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.db.search(u"some show")
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def test_remove_show(self):

		show1 = Show(u"random show", url=u"z")
		show2 = Show(u"other show", url=u"x")

		show1 = self.db.addShow(show1)
		show2 = self.db.addShow(show2)
		self.db.commit()

		now = date.today()
		episode1 = Episode(show1, u"first", 1, 1, now, u"x", 1)
		episode2 = Episode(show1, u"second",1, 2, now, u"x", 1)
		episode3 = Episode(show2, u"first", 1, 1, now, u"x", 1)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)
		self.db.commit()

		episodes = self.db.getEpisodes()
		self.assertEqual(3, len(episodes))

		self.db.removeShow(show1.show_id)
		self.db.commit()

		episodes = self.db.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual(episode3, episodes[0])

	def test_rollback(self):

		show = Show(u"some show")
		show = self.db.addShow(show)
		self.db.commit()

		episode1 = Episode(show, u"first episode", 3, 10, date.today(),
								u"FOO", 30)
		episode2 = Episode(show, u"Second episode", 3, 12, date.today(),
								u"FOO", 32)

		self.db.addEpisode(episode1)
		self.db.rollback()
		self.db.addEpisode(episode2)
		self.db.commit()

		episodes = self.db.getEpisodes()
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def test_get_episodes(self):

		show = Show(u"some show")
		show = self.db.addShow(show)

		today = date.today()
		yesterday = today - timedelta(1)
		before = yesterday - timedelta(1)
		tomorrow = today + timedelta(1)

		episode1 = Episode(show, u"episode1", 1, 1, before, u"x", 1)
		episode2 = Episode(show, u"episode2", 1, 2, yesterday, u"x", 2)
		episode3 = Episode(show, u"episode3", 1, 3, today, u"x", 3)
		episode4 = Episode(show, u"episode4", 1, 4, tomorrow, u"x", 4)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)
		self.db.addEpisode(episode4)

		episodes = self.db.getEpisodes(basedate = before, n_days=1)
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertFalse(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.db.getEpisodes(basedate = before, n_days=0)
		self.assertTrue(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertFalse(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.db.getEpisodes(basedate = today, n_days=0)
		self.assertFalse(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.db.getEpisodes(basedate = yesterday,n_days=2)
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

	def test_remove_before(self):

		show = Show(u"some show")
		show = self.db.addShow(show)

		today = date.today()
		yesterday = today - timedelta(1)
		before = yesterday - timedelta(1)
		tomorrow = today + timedelta(1)

		episode1 = Episode(show, u"episode1", 1, 1, before, u"x", 1)
		episode2 = Episode(show, u"episode2", 1, 2, yesterday, u"x", 2)
		episode3 = Episode(show, u"episode3", 1, 3, today, u"x", 3)
		episode4 = Episode(show, u"episode4", 1, 4, tomorrow, u"x", 4)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)
		self.db.addEpisode(episode4)

		episodes = self.db.getEpisodes(basedate = before, n_days=10)
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

		self.db.removeBefore(today)
		episodes = self.db.getEpisodes(basedate = before, n_days=10)
		self.assertFalse(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

	def test_remove_before_with_show(self):

		show1 = self.db.addShow(Show(u"some show", url=u"a"))
		show2 = self.db.addShow(Show(u"some other show", url=u"b"))

		today = date.today()
		yesterday = today - timedelta(1)

		episode1 = Episode(show1, u"episode1", 1, 1, yesterday, u"x", 1)
		episode2 = Episode(show1, u"episode1", 1, 2, yesterday, u"x", 1)
		episode3 = Episode(show2, u"episode1", 1, 2, yesterday, u"x", 1)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)

		self.db.removeBefore(today, show=show1)
		episodes = self.db.getEpisodes(basedate = yesterday, n_days=10)
		self.assertEqual(1, len(episodes))

	def test_duplicate_episodes(self):

		show = self.db.addShow(Show(u"some show"))
		self.assertEqual(0, len(self.db.getEpisodes()))

		today = date.today()
		episode1 = Episode(show, u"e", 1, 1, today, u"x", 1)
		episode2 = Episode(show, u"f", 1, 1, today, u"x", 1)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode1)
		episodes = self.db.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual(u"e", episodes[0].title)

		self.db.addEpisode(episode2)
		episodes = self.db.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual(u"f", episodes[0].title)

	def test_clear(self):

		show = self.db.addShow(Show(u"some show", url=u"urlX"))
		self.assertEqual(0, len(self.db.getEpisodes()))

		today = date.today()
		episode1 = Episode(show, u"e", 1, 1, today, u"x", 1)
		episode2 = Episode(show, u"e", 1, 2, today, u"x", 1)
		episode3 = Episode(show, u"e", 1, 3, today, u"x", 1)
		episode4 = Episode(show, u"e", 1, 3, today, u"x", 1)
		episode5 = Episode(show, u"e", 1, 4, today, u"x", 1)

		self.db.addEpisode(episode1)
		self.db.addEpisode(episode2)
		self.db.addEpisode(episode3)
		self.db.commit()

		self.assertEqual(3, len(self.db.getEpisodes()))

		self.db.clear()
		self.assertEqual(0, len(self.db.getEpisodes()))

		self.db.addEpisode(episode4)
		self.db.addEpisode(episode5)
		self.assertEqual(2, len(self.db.getEpisodes()))


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(DataStoreTest))
	return suite
