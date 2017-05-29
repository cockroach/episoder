#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import tempfile
import datetime

from unittest import TestCase, TestLoader, TestSuite

import pyepisoder.episoder as episoder


class DataStoreTest(TestCase):

	def setUp(self):

		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)

	def tearDown(self):

		os.unlink(self.path)

	def testGetShowByUrl(self):

		show1 = episoder.Show('test show', url='a')
		show2 = episoder.Show('test show 2', url='b')

		self.store.addShow(show1)
		self.store.addShow(show2)

		self.assertEqual(show1, self.store.getShowByUrl('a'))
		self.assertEqual(show2, self.store.getShowByUrl('b'))

		self.assertEqual(None, self.store.getShowByUrl('c'))

	def testAddShow(self):

		show = episoder.Show('test show', url='http://test.show')
		show = self.store.addShow(show)
		self.store.commit()

		id = show.show_id

		self.assertTrue(id > 0, "id is %d, must be > 0" % id)
		shows = self.store.getShows()

		self.assertEqual(1, len(shows))
		self.assertEqual(id, shows[0].show_id)
		self.assertEqual('test show', shows[0].show_name)

		show2 = episoder.Show('moo show', url='http://test.show.2')
		show2 = self.store.addShow(show2)
		id2 = show2.show_id
		self.store.commit()

		shows = self.store.getShows()

		self.assertNotEqual(id, id2)

		self.assertEqual(2, len(shows))

		ids = []
		for show in shows:
			ids.append(show.show_id)

		self.assertTrue(id2 in ids)

		showA = episoder.Show('showA', url='urlA')
		showB = episoder.Show('showA', url='urlB')
		showC = episoder.Show('showB', url='urlB')

		self.store.addShow(showA)
		self.store.commit()
		self.assertEqual(3, len(self.store.getShows()))

		self.store.addShow(showB)
		self.store.commit()
		self.assertEqual(4, len(self.store.getShows()))

		try:
			self.store.addShow(showC)
			self.store.commit()
			self.assertTrue(False)
		except Exception:
			pass

	def testAddEpisode(self):

		show = episoder.Show('some show', url='foo')
		show = self.store.addShow(show)
		self.store.commit()

		episode1 = episoder.Episode(show, 'Some episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'No episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.commit()

		episodes = self.store.getEpisodes()

		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testSearch(self):

		show = episoder.Show('some show')
		show = self.store.addShow(show)
		episode1 = episoder.Episode(show, 'first episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'Second episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.commit()

		episodes = self.store.search('first')
		self.assertTrue(episode1 in episodes)
		self.assertFalse(episode2 in episodes)

		episodes = self.store.search('second')
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.store.search('episode')
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.store.search('some show')
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testRemoveShow(self):

		show1 = episoder.Show('random show', url='z')
		show2 = episoder.Show('other show', url='x')

		show1 = self.store.addShow(show1)
		show2 = self.store.addShow(show2)
		self.store.commit()

		now = datetime.date.today()
		episode1 = episoder.Episode(show1, 'first', 1, 1, now, 'x', 1)
		episode2 = episoder.Episode(show1, 'second', 1, 2, now, 'x', 1)
		episode3 = episoder.Episode(show2, 'first', 1, 1, now, 'x', 1)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)
		self.store.commit()

		episodes = self.store.getEpisodes()
		self.assertEqual(3, len(episodes))

		self.store.removeShow(show1.show_id)
		self.store.commit()

		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual(episode3, episodes[0])

	def testRollback(self):

		show = episoder.Show('some show')
		show = self.store.addShow(show)
		self.store.commit()

		episode1 = episoder.Episode(show, 'first episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'Second episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(episode1)
		self.store.rollback()
		self.store.addEpisode(episode2)
		self.store.commit()

		episodes = self.store.getEpisodes()

		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testGetEpisodes(self):

		show = episoder.Show('some show')
		show = self.store.addShow(show)

		today = datetime.date.today()
		yesterday = today - datetime.timedelta(1)
		before = yesterday - datetime.timedelta(1)
		tomorrow = today + datetime.timedelta(1)

		episode1 = episoder.Episode(show, 'episode1', 1, 1,
				before, 'x', 1)
		episode2 = episoder.Episode(show, 'episode2', 1, 2,
				yesterday, 'x', 2)
		episode3 = episoder.Episode(show, 'episode3', 1, 3,
				today, 'x', 3)
		episode4 = episoder.Episode(show, 'episode4', 1, 4,
				tomorrow, 'x', 4)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)
		self.store.addEpisode(episode4)

		episodes = self.store.getEpisodes(basedate = before, n_days=1)
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertFalse(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.store.getEpisodes(basedate = before, n_days=0)
		self.assertTrue(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertFalse(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.store.getEpisodes(basedate = today, n_days=0)
		self.assertFalse(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertFalse(episode4 in episodes)

		episodes = self.store.getEpisodes(basedate = yesterday,n_days=2)
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

	def testRemoveBefore(self):

		show = episoder.Show('some show')
		show = self.store.addShow(show)

		today = datetime.date.today()
		yesterday = today - datetime.timedelta(1)
		before = yesterday - datetime.timedelta(1)
		tomorrow = today + datetime.timedelta(1)

		episode1 = episoder.Episode(show, 'episode1', 1, 1,
				before, 'x', 1)
		episode2 = episoder.Episode(show, 'episode2', 1, 2,
				yesterday, 'x', 2)
		episode3 = episoder.Episode(show, 'episode3', 1, 3,
				today, 'x', 3)
		episode4 = episoder.Episode(show, 'episode4', 1, 4,
				tomorrow, 'x', 4)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)
		self.store.addEpisode(episode4)

		episodes = self.store.getEpisodes(basedate = before, n_days=10)
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

		self.store.removeBefore(today)
		episodes = self.store.getEpisodes(basedate = before, n_days=10)
		self.assertFalse(episode1 in episodes)
		self.assertFalse(episode2 in episodes)
		self.assertTrue(episode3 in episodes)
		self.assertTrue(episode4 in episodes)

	def testRemoveBeforeWithShow(self):

		show1 = episoder.Show('some show', url='a')
		show1 = self.store.addShow(show1)

		show2 = episoder.Show('some other show', url='b')
		show2 = self.store.addShow(show2)

		today = datetime.date.today()
		yesterday = today - datetime.timedelta(1)

		episode1 = episoder.Episode(show1, 'episode1', 1, 1,
				yesterday, 'x', 1)
		episode2 = episoder.Episode(show1, 'episode1', 1, 2,
				yesterday, 'x', 1)
		episode3 = episoder.Episode(show2, 'episode1', 1, 2,
				yesterday, 'x', 1)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)

		self.store.removeBefore(today, show=show1)
		episodes = self.store.getEpisodes(basedate = yesterday, n_days=10)
		self.assertEqual(1, len(episodes))

	def testDuplicateEpisodes(self):

		today = datetime.date.today()

		show = episoder.Show('some show')
		show = self.store.addShow(show)
		self.assertEqual(0, len(self.store.getEpisodes()))

		episode1 = episoder.Episode(show, 'e', 1, 1, today, 'x', 1)
		episode2 = episoder.Episode(show, 'f', 1, 1, today, 'x', 1)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode1)
		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual('e', episodes[0].title)

		self.store.addEpisode(episode2)
		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEqual('f', episodes[0].title)

	def testClear(self):

		today = datetime.date.today()

		show = episoder.Show('some show', url='urlX')
		show = self.store.addShow(show)
		self.assertEqual(0, len(self.store.getEpisodes()))

		episode1 = episoder.Episode(show, 'e', 1, 1, today, 'x', 1)
		episode2 = episoder.Episode(show, 'e', 1, 2, today, 'x', 1)
		episode3 = episoder.Episode(show, 'e', 1, 3, today, 'x', 1)
		episode4 = episoder.Episode(show, 'e', 1, 3, today, 'x', 1)
		episode5 = episoder.Episode(show, 'e', 1, 4, today, 'x', 1)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)
		self.store.commit()

		self.assertEqual(3, len(self.store.getEpisodes()))

		self.store.clear()
		self.assertEqual(0, len(self.store.getEpisodes()))

		self.store.addEpisode(episode4)
		self.store.addEpisode(episode5)
		self.assertEqual(2, len(self.store.getEpisodes()))


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(DataStoreTest))
	return suite
