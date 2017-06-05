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

import logging

from os import unlink
from datetime import date, timedelta
from tempfile import mktemp
from unittest import TestCase, TestLoader, TestSuite

from pyepisoder.episoder import Database
from pyepisoder.database import Show, Episode


class DatabaseTest(TestCase):

	def setUp(self):

		logging.basicConfig(level=logging.ERROR)
		logging.disable(logging.ERROR)
		self.db = Database("sqlite://")
		self.tempfiles = []

	def tearDown(self):

		for f in self.tempfiles:
			unlink(f)

	def test_str_and_repr(self):

		name = str(self.db)
		self.assertEqual(name, "Episoder Database at sqlite://")

		name = repr(self.db)
		self.assertEqual(name, "Database(sqlite://)")

	def test_get_show_by_url(self):

		show1 = self.db.add_show(Show(u"test show", url=u"a"))
		show2 = self.db.add_show(Show(u"test show 2", url=u"b"))

		self.assertEqual(show1, self.db.get_show_by_url(u"a"))
		self.assertEqual(show2, self.db.get_show_by_url(u"b"))
		self.assertEqual(None, self.db.get_show_by_url(u"c"))

	def test_get_show_by_id(self):

		show1 = self.db.add_show(Show(u"test show", url=u"a"))
		show2 = self.db.add_show(Show(u"test show 2", url=u"b"))

		self.assertEqual(show1, self.db.get_show_by_id(show1.id))
		self.assertEqual(show2, self.db.get_show_by_id(show2.id))
		self.assertEqual(None, self.db.get_show_by_id(99999))

	def test_add_show(self):

		show = self.db.add_show(Show(u"test show", url=u"http://test2"))
		self.assertTrue(show.id > 0)

		shows = self.db.get_shows()
		self.assertEqual(1, len(shows))
		self.assertIn(show, shows)
		self.db.commit()

		show2 = self.db.add_show(Show(u"moo show", url=u"http://test"))
		self.assertTrue(show2.id > 0)
		self.assertNotEqual(show.id, show2.id)
		self.db.commit()

		shows = self.db.get_shows()
		self.assertEqual(2, len(shows))
		self.assertIn(show, shows)
		self.assertIn(show2, shows)

		self.db.add_show(Show(u"showA", url=u"urlA"))
		self.assertEqual(3, len(self.db.get_shows()))
		self.db.commit()

		self.db.add_show(Show(u"showA", url=u"urlB"))
		self.assertEqual(4, len(self.db.get_shows()))
		self.db.commit()

		with self.assertRaises(Exception):
			self.db.add_show(Show(u"showB", url=u"urlB"))
			self.db.commit()

		self.db.rollback()
		self.assertEqual(4, len(self.db.get_shows()))

	def test_add_episode(self):

		show = Show(u"some show", url=u"foo")
		show = self.db.add_show(show)
		self.db.commit()

		ep1 = Episode(u"Some episode", 3, 10, date.today(), u"FOO", 30)
		ep2 = Episode(u"No episode", 3, 12, date.today(), u"FOO", 32)
		self.db.add_episode(ep1, show)
		self.db.add_episode(ep2, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertTrue(ep1 in episodes)
		self.assertTrue(ep2 in episodes)

	def test_search(self):

		show = self.db.add_show(Show(u"some show"))
		ep1 = Episode(u"first episode", 3, 10, date.today(), u"FOO", 30)
		ep2 = Episode(u"Second episode", 3, 12, date.today(), u"FOO", 32)

		self.db.add_episode(ep1, show)
		self.db.add_episode(ep2, show)
		self.db.commit()

		episodes = self.db.search(u"first")
		self.assertIn(ep1, episodes)
		self.assertNotIn(ep2, episodes)

		episodes = self.db.search(u"second")
		self.assertNotIn(ep1, episodes)
		self.assertIn(ep2, episodes)

		episodes = self.db.search(u"episode")
		self.assertIn(ep1, episodes)
		self.assertIn(ep2, episodes)

		episodes = self.db.search(u"some show")
		self.assertIn(ep1, episodes)
		self.assertIn(ep2, episodes)

	def test_remove_invalid_show(self):

		self.db.remove_show(0)

	def test_remove_show(self):

		show1 = self.db.add_show(Show(u"random show", url=u"z"))
		show2 = self.db.add_show(Show(u"other show", url=u"x"))
		self.db.commit()

		now = date.today()
		episode1 = Episode(u"first", 1, 1, now, u"x", 1)
		episode2 = Episode(u"second",1, 2, now, u"x", 1)
		episode3 = Episode(u"first", 1, 1, now, u"x", 1)

		self.db.add_episode(episode1, show1)
		self.db.add_episode(episode2, show1)
		self.db.add_episode(episode3, show2)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(3, len(episodes))

		self.db.remove_show(show1.id)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(1, len(episodes))
		self.assertIn(episode3, episodes)

	def test_rollback(self):

		show = Show(u"some show")
		show = self.db.add_show(show)
		self.db.commit()

		ep1 = Episode(u"first", 3, 10, date.today(), u"FOO", 30)
		self.db.add_episode(ep1, show)
		self.db.rollback()

		ep2 = Episode(u"Second", 3, 12, date.today(), u"FOO", 32)
		self.db.add_episode(ep2, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertFalse(ep1 in episodes)
		self.assertTrue(ep2 in episodes)

	def test_get_episodes(self):

		show = self.db.add_show(Show(u"some show"))

		today = date.today()
		yesterday = today - timedelta(1)
		before = yesterday - timedelta(1)
		tomorrow = today + timedelta(1)

		episode1 = Episode(u"episode1", 1, 1, before, u"x", 1)
		episode2 = Episode(u"episode2", 1, 2, yesterday, u"x", 2)
		episode3 = Episode(u"episode3", 1, 3, today, u"x", 3)
		episode4 = Episode(u"episode4", 1, 4, tomorrow, u"x", 4)

		self.db.add_episode(episode1, show)
		self.db.add_episode(episode2, show)
		self.db.add_episode(episode3, show)
		self.db.add_episode(episode4, show)

		self.db.commit()

		episodes = self.db.get_episodes(basedate = before, n_days=1)
		self.assertIn(episode1, episodes)
		self.assertIn(episode2, episodes)
		self.assertNotIn(episode3, episodes)
		self.assertNotIn(episode4, episodes)

		episodes = self.db.get_episodes(basedate = before, n_days=0)
		self.assertIn(episode1, episodes)
		self.assertNotIn(episode2, episodes)
		self.assertNotIn(episode3, episodes)
		self.assertNotIn(episode4, episodes)

		episodes = self.db.get_episodes(basedate = today, n_days=0)
		self.assertNotIn(episode1, episodes)
		self.assertNotIn(episode2, episodes)
		self.assertIn(episode3, episodes)
		self.assertNotIn(episode4, episodes)

		episodes = self.db.get_episodes(basedate = yesterday,n_days=2)
		self.assertNotIn(episode1, episodes)
		self.assertIn(episode2, episodes)
		self.assertIn(episode3, episodes)
		self.assertIn(episode4, episodes)

	def test_remove_before(self):

		show = self.db.add_show(Show(u"some show"))

		today = date.today()
		yesterday = today - timedelta(1)
		before = yesterday - timedelta(1)
		tomorrow = today + timedelta(1)

		episode1 = Episode(u"episode1", 1, 1, before, u"x", 1)
		episode2 = Episode(u"episode2", 1, 2, yesterday, u"x", 2)
		episode3 = Episode(u"episode3", 1, 3, today, u"x", 3)
		episode4 = Episode(u"episode4", 1, 4, tomorrow, u"x", 4)

		self.db.add_episode(episode1, show)
		self.db.add_episode(episode2, show)
		self.db.add_episode(episode3, show)
		self.db.add_episode(episode4, show)
		self.db.commit()

		episodes = self.db.get_episodes(basedate = before, n_days=10)
		self.assertIn(episode1, episodes)
		self.assertIn(episode2, episodes)
		self.assertIn(episode3, episodes)
		self.assertIn(episode4, episodes)

		self.db.remove_before(today)
		episodes = self.db.get_episodes(basedate = before, n_days=10)
		self.assertNotIn(episode1, episodes)
		self.assertNotIn(episode2, episodes)
		self.assertIn(episode3, episodes)
		self.assertIn(episode4, episodes)

	def test_remove_before_with_show(self):

		show1 = self.db.add_show(Show(u"some show", url=u"a"))
		show2 = self.db.add_show(Show(u"some other show", url=u"b"))

		today = date.today()
		yesterday = today - timedelta(1)

		episode1 = Episode(u"episode1", 1, 1, yesterday, u"x", 1)
		episode2 = Episode(u"episode1", 1, 2, yesterday, u"x", 1)
		episode3 = Episode(u"episode1", 1, 2, yesterday, u"x", 1)

		self.db.add_episode(episode1, show1)
		self.db.add_episode(episode2, show1)
		self.db.add_episode(episode3, show2)

		self.db.commit()

		episodes = self.db.get_episodes(basedate = yesterday, n_days=10)
		self.assertIn(episode1, episodes)
		self.assertIn(episode2, episodes)
		self.assertIn(episode3, episodes)

		self.db.remove_before(today, show=show1)

		episodes = self.db.get_episodes(basedate = yesterday, n_days=10)
		self.assertNotIn(episode1, episodes)
		self.assertNotIn(episode2, episodes)
		self.assertIn(episode3, episodes)

	def test_duplicate_episodes(self):

		today = date.today()
		show = self.db.add_show(Show(u"some show"))
		self.assertEqual(0, len(self.db.get_episodes()))

		episode1 = Episode(u"e", 1, 1, today, u"x", 1)
		self.db.add_episode(episode1, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(1, len(episodes))
		self.assertIn(episode1, episodes)

		episode2 = Episode(u"f", 1, 1, today, u"x", 1)
		self.db.add_episode(episode2, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(1, len(episodes))
		self.assertIn(episode2, episodes)

	def test_clear(self):

		today = date.today()
		show = self.db.add_show(Show(u"some show", url=u"urlX"))
		self.assertEqual(0, len(self.db.get_episodes()))

		episode1 = Episode(u"e", 1, 1, today, u"x", 1)
		episode2 = Episode(u"e", 1, 2, today, u"x", 1)
		episode3 = Episode(u"e", 1, 3, today, u"x", 1)
		episode4 = Episode(u"e", 1, 3, today, u"x", 1)
		episode5 = Episode(u"e", 1, 4, today, u"x", 1)

		self.db.add_episode(episode1, show)
		self.db.add_episode(episode2, show)
		self.db.add_episode(episode3, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(3, len(episodes))
		self.assertIn(episode1, episodes)
		self.assertIn(episode2, episodes)
		self.assertIn(episode3, episodes)

		self.db.clear()
		self.assertEqual(0, len(self.db.get_episodes()))

		self.db.add_episode(episode4, show)
		self.db.add_episode(episode5, show)
		self.db.commit()

		episodes = self.db.get_episodes()
		self.assertEqual(2, len(episodes))
		self.assertIn(episode4, episodes)
		self.assertIn(episode5, episodes)

	def test_using_existing_database(self):

		path = mktemp()
		self.tempfiles.append(path)

		db = Database(path)
		self.assertEqual(len(db.get_shows()), 0)
		db.close()

		db = Database(path)
		self.assertEqual(len(db.get_shows()), 0)
		db.close()

	def test_set_get_schema_version(self):

		self.assertEqual(self.db.get_schema_version(), 4)

		self.db.set_schema_version(1)
		self.assertEqual(self.db.get_schema_version(), 1)

		self.db.set_schema_version(2)
		self.assertEqual(self.db.get_schema_version(), 2)

	def test_get_expired_shows(self):

		then = date(2017, 6, 4)

		# show1 -> running
		show1 = self.db.add_show(Show(u"1", url=u"1"))
		show1.updated = then
		show1.status = Show.RUNNING

		# show2 -> paused
		show2 = self.db.add_show(Show(u"2", url=u"2"))
		show2.updated = then
		show2.status = Show.SUSPENDED

		# show3 -> ended
		show3 = self.db.add_show(Show(u"3", url=u"3"))
		show3.updated = then
		show3.status = Show.ENDED

		self.db.commit()

		# all shows updated today, nothing expired
		shows = self.db.get_expired_shows(today=then)
		self.assertNotIn(show1, shows)
		self.assertNotIn(show2, shows)
		self.assertNotIn(show3, shows)

		# all shows updated 2 days ago, still nothing expired
		shows = self.db.get_expired_shows(today=then + timedelta(2))
		self.assertNotIn(show1, shows)
		self.assertNotIn(show2, shows)
		self.assertNotIn(show3, shows)

		# all shows updated 3 days ago, show1 should be expired
		shows = self.db.get_expired_shows(today=then + timedelta(3))
		self.assertIn(show1, shows)
		self.assertNotIn(show2, shows)
		self.assertNotIn(show3, shows)

		# all shows updated 8 days ago, shows 1 and 2 should be expired
		shows = self.db.get_expired_shows(today=then + timedelta(8))
		self.assertIn(show1, shows)
		self.assertIn(show2, shows)
		self.assertNotIn(show3, shows)

		# all shows updated 15 days ago, all shows should be expired
		shows = self.db.get_expired_shows(today=then + timedelta(15))
		self.assertIn(show1, shows)
		self.assertIn(show2, shows)
		self.assertIn(show3, shows)

		# disabled shows never expire
		show1.enabled = False
		show2.enabled = False
		show3.enabled = False
		self.db.commit()

		shows = self.db.get_expired_shows(today=then + timedelta(15))
		self.assertNotIn(show1, shows)
		self.assertNotIn(show2, shows)
		self.assertNotIn(show3, shows)

	def test_get_enabled_shows(self):

		show1 = self.db.add_show(Show(u"1", url=u"1"))
		show1.enabled = False

		show2 = self.db.add_show(Show(u"2", url=u"2"))
		self.db.commit()

		shows = self.db.get_enabled_shows()
		self.assertNotIn(show1, shows)
		self.assertIn(show2, shows)

def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(DatabaseTest))
	return suite
