#!/usr/bin/env python
import os
import unittest
import tempfile
import datetime

import pyepisoder.episoder as episoder
import pyepisoder.plugins as plugins

class TestDataStore(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)
		self.store.clear()

	def tearDown(self):
		os.unlink(self.path)

	def testAddShow(self):
		id = self.store.addShow('test show')
		self.assertTrue(id > 0)
		shows = self.store.getShows()

		self.assertEqual(1, len(shows))
		self.assertEqual((id, 'test show'), shows[0])

		id2 = self.store.addShow('moo show')
		shows = self.store.getShows()

		self.assertNotEqual(id, id2)

		self.assertEqual(2, len(shows))
		self.assertTrue((id2, 'moo show') in shows)

	def testAddEpisode(self):
		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)
		episode1 = episoder.Episode(show, 'Some episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'No episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode2)
		self.store.commit()

		episodes = self.store.getEpisodes()

		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testSearch(self):
		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)
		episode1 = episoder.Episode(show, 'first episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'Second episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode2)
		self.store.commit()

		episodes = self.store.search({'search': 'first'})
		self.assertTrue(episode1 in episodes)
		self.assertFalse(episode2 in episodes)

		episodes = self.store.search({'search': 'second'})
		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.store.search({'search': 'episode'})
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

		episodes = self.store.search({'search': 'some show'})
		self.assertTrue(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testRollback(self):
		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)
		self.store.commit()

		episode1 = episoder.Episode(show, 'first episode', 3,
				10, datetime.date.today(), 'FOO', 30)
		episode2 = episoder.Episode(show, 'Second episode', 3,
				12, datetime.date.today(), 'FOO', 32)

		self.store.addEpisode(show_id, episode1)
		self.store.rollback()
		self.store.addEpisode(show_id, episode2)
		self.store.commit()

		episodes = self.store.getEpisodes()

		self.assertFalse(episode1 in episodes)
		self.assertTrue(episode2 in episodes)

	def testGetEpisodes(self):
		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)

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

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode2)
		self.store.addEpisode(show_id, episode3)
		self.store.addEpisode(show_id, episode4)

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
		show_id = self.store.addShow(show.name)

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

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode2)
		self.store.addEpisode(show_id, episode3)
		self.store.addEpisode(show_id, episode4)

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

if __name__ == '__main__':
	unittest.main()
