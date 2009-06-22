#!/usr/bin/env python
import os
import shutil
import logging
import unittest
import tempfile
import datetime

import pyepisoder.episoder as episoder
import pyepisoder.plugins as plugins

class TestDataStore(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)

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

		self.store.addShow('showA', 'urlA')
		self.assertEqual(3, len(self.store.getShows()))

		self.store.addShow('showA', 'urlB')
		self.assertEqual(4, len(self.store.getShows()))

		self.store.addShow('showA', 'urlB')
		self.assertEqual(4, len(self.store.getShows()))

		self.store.addShow('showB', 'urlB')
		self.assertEqual(5, len(self.store.getShows()))

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

	def testDuplicateEpisodes(self):
		today = datetime.date.today()

		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)
		self.assertEqual(0, len(self.store.getEpisodes()))

		episode1 = episoder.Episode(show, 'e', 1, 1, today, 'x', 1)
		episode2 = episoder.Episode(show, 'f', 1, 1, today, 'x', 1)

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode1)
		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEquals('e', episodes[0].title)

		self.store.addEpisode(show_id, episode2)
		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEquals('f', episodes[0].title)

	def testClear(self):
		today = datetime.date.today()

		show = episoder.Show('some show')
		show_id = self.store.addShow(show.name)
		self.assertEqual(0, len(self.store.getEpisodes()))

		episode1 = episoder.Episode(show, 'e', 1, 1, today, 'x', 1)
		episode2 = episoder.Episode(show, 'e', 1, 2, today, 'x', 1)
		episode3 = episoder.Episode(show, 'e', 1, 3, today, 'x', 1)
		episode4 = episoder.Episode(show, 'e', 1, 3, today, 'x', 1)
		episode5 = episoder.Episode(show, 'e', 1, 4, today, 'x', 1)

		self.store.addEpisode(show_id, episode1)
		self.store.addEpisode(show_id, episode2)
		self.store.addEpisode(show_id, episode3)
		self.store.commit()

		self.assertEqual(3, len(self.store.getEpisodes()))

		self.store.clear()
		self.assertEqual(0, len(self.store.getEpisodes()))

		self.store.addEpisode(show_id, episode4)
		self.store.addEpisode(show_id, episode5)
		self.assertEqual(2, len(self.store.getEpisodes()))

class testEpguidesParser(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)
		self.parser = plugins.EpguidesParser()
		self.parser.awkfile = 'extras/episoder_helper_epguides.awk'

	def tearDown(self):
		os.unlink(self.path)

	def _accept(self, url):
		return self.parser.accept(url)

	def _parse(self, file):
		self.parser.parseFile(file, self.store)

	def testAccept(self):
		self.assertTrue(self._accept('http://www.epguides.com/Lost'))
		self.assertFalse(self._accept('http://epguides.com/Lost'))
		self.assertFalse(self._accept('http://www.tv.com/Lost'))

	def testParseFile(self):
		then = datetime.date(1970, 1, 1)
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_lost.html')
		self.store.commit()
		self.assertEquals(102, len(self.store.getEpisodes(then, 99999)))
		self.store.clear()
		self.assertEquals(0, len(self.store.getEpisodes()))

		self._parse('test/testdata/epguides_bsg.html')
		self.assertEquals(74, len(self.store.getEpisodes(then, 99999)))

class testTVComParser(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)
		self.parser = plugins.TVComParser()
		self.parser.episodes = {}

	def tearDown(self):
		os.unlink(self.path)

	def _openfile(self, url):
		(base, url) = url.split(' ')
		if url.endswith('guide'):
			file = base + '_guide.html'
		else:
			file = base + '_list.html'

		tmp = tempfile.mktemp()
		shutil.copyfile(file, tmp)
		return tmp

	def _parse(self, show):
		self.parser._fetchPage = self._openfile
		source = {'url': 'test/testdata/tvcom_%s ' % show }
		self.parser.parse(source, self.store)

	def testParseFile1(self):
		then = datetime.date(1970, 1, 1)
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('csi')
		self.assertEquals(206, len(self.store.getEpisodes(then, 99999)))

		episodes = self.store.search({'search': 'Hammer'})
		self.assertEqual(1, len(episodes))
		episode = episodes[0]
		self.assertEqual('If I Had A Hammer...', episode.title)
		self.assertEqual(9, episode.season)
		self.assertEqual(21, episode.episode)
		self.assertEqual(datetime.date(2009, 4, 23), episode.airdate)
		self.assertEqual('921', episode.prodnum)
		self.assertEqual(203, episode.total)
		self.assertEqual('CSI', episode.show.name)

	def testParseFile2(self):
		then = datetime.date(1970, 1, 1)
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('tds')
		self.assertEquals(1697,len(self.store.getEpisodes(then, 99999)))

		episodes = self.store.search({'search': 'James Spader'})
		self.assertEqual(1, len(episodes))
		episode = episodes[0]
		self.assertEqual('James Spader', episode.title)
		self.assertEqual(8, episode.season)
		self.assertEqual(63, episode.episode)
		self.assertEqual(datetime.date(2003, 11, 19), episode.airdate)
		self.assertEqual('8063', episode.prodnum)
		self.assertEqual(835, episode.total)
		self.assertEqual('The Daily Show', episode.show.name)

if __name__ == '__main__':
	unittest.main()
