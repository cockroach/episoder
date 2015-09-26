#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import shutil
import logging
import unittest
import tempfile
import datetime

import pyepisoder.episoder as episoder
import pyepisoder.plugins as plugins

class DataStoreTest(unittest.TestCase):
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
			self.assertTrue(false)
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
		self.assertEquals(3, len(episodes))

		self.store.removeShow(show1.show_id)
		self.store.commit()

		episodes = self.store.getEpisodes()
		self.assertEquals(1, len(episodes))
		self.assertEquals(episode3, episodes[0])

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
		self.assertEquals(1, len(episodes))


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
		self.assertEquals('e', episodes[0].title)

		self.store.addEpisode(episode2)
		episodes = self.store.getEpisodes()
		self.assertEqual(1, len(episodes))
		self.assertEquals('f', episodes[0].title)

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

class ShowTest(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)
		self.show = episoder.Show('A', url='a')
		self.show = self.store.addShow(self.show)

	def tearDown(self):
		os.unlink(self.path)

	def testRemoveEpisodesBefore(self):
		now = datetime.date.today()
		then = now - datetime.timedelta(3)

		show2 = episoder.Show('B', url='b')
		show2 = self.store.addShow(show2)

		episode1 = episoder.Episode(self.show, 'e', 1, 1, now, 'x', 1)
		episode2 = episoder.Episode(self.show, 'e', 1, 2, then, 'x', 1)
		episode3 = episoder.Episode(show2, 'e', 1, 3, now, 'x', 1)
		episode4 = episoder.Episode(show2, 'e', 1, 4, then, 'x', 1)

		self.store.addEpisode(episode1)
		self.store.addEpisode(episode2)
		self.store.addEpisode(episode3)
		self.store.addEpisode(episode4)
		self.store.commit()

		episodes = self.store.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(4, len(episodes))

		show2.removeEpisodesBefore(self.store, now)

		episodes = self.store.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(3, len(episodes))

		self.show.removeEpisodesBefore(self.store, now)

		episodes = self.store.getEpisodes(basedate = then, n_days=10)
		self.assertEqual(2, len(episodes))

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
		show = self.store.getShowByUrl(file)

		if not show:
			show = episoder.Show(name='', url=file)
			show = self.store.addShow(show)

		self.parser.show = show
		self.parser.parseFile(file, self.store)

	def testAccept(self):
		self.assertTrue(self._accept('http://www.epguides.com/Lost'))
		self.assertFalse(self._accept('http://epguides2.com/Lost'))
		self.assertFalse(self._accept('http://www.tv.com/Lost'))

	def testParseFile(self):
		then = datetime.date(1970, 1, 1)
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_lost.html')
		self.store.commit()
		self.assertEquals(102, len(self.store.getEpisodes(then, 99999)))

		show = self.store.getShowByUrl(
				'test/testdata/epguides_lost.html')
		self.assertEquals('Lost', show.name)
		self.assertEquals(episoder.Show.RUNNING, show.status)

		self._parse('test/testdata/epguides_lost.html')
		self.store.commit()
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEquals(102, len(episodes))

		ep = episodes[0]
		self.assertEquals('Pilot (1)', ep.title)
		self.assertEquals(1, ep.season)
		self.assertEquals(1, ep.episode)

		ep = episodes[9]
		self.assertEquals('Raised by Another', ep.title)
		self.assertEquals(1, ep.season)
		self.assertEquals(10, ep.episode)

		ep = episodes[24]
		self.assertEquals('Man of Science, Man of Faith', ep.title)
		self.assertEquals(2, ep.season)
		self.assertEquals(1, ep.episode)

		self.store.clear()
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_bsg.html')
		self.assertEquals(74, len(self.store.getEpisodes(then, 99999)))

	def testEpguidesFormat2(self):
		# Another format
		then = datetime.date(1970, 1, 1)
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_eureka.html')
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEquals(76, len(episodes))

		ep = episodes[0]
		self.assertEquals('Pilot', ep.title)
		self.assertEquals(1, ep.season)
		self.assertEquals(1, ep.episode)

		ep = episodes[9]
		self.assertEquals('Purple Haze', ep.title)
		self.assertEquals(1, ep.season)
		self.assertEquals(10, ep.episode)

		ep = episodes[27]
		self.assertEquals('Best in Faux', ep.title)
		self.assertEquals(3, ep.season)
		self.assertEquals(3, ep.episode)

	def testEpguidesFormat3(self):
		# Yet another format
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_midsomer_murders.html')
		episodes = self.store.getEpisodes(then, 99999)

		episode = episodes[0]
		self.assertEquals(1, episode.season)
		self.assertEquals(1, episode.episode)
		self.assertEquals('Written in Blood', episode.title)

		episode = episodes[5]
		self.assertEquals(2, episode.season)
		self.assertEquals(2, episode.episode)
		self.assertEquals("Strangler's Wood", episode.title)

	def testEpguidesRemoveIllegalChars(self):
		# This one contains an illegal character somewhere
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_american_idol.html')
		episodes = self.store.getEpisodes(then, 99999)

		episode = episodes[10]
		self.assertEquals('Pride Goeth Before The Fro', episode.title)
		self.assertEquals(1, episode.season)
		self.assertEquals(12, episode.episode)

	def testEpguidesMissingSeasonNumber(self):
		# This one lacks a season number somewhere
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_48_hours_mistery.html')
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEquals(31, len(episodes))

		episode = episodes[0]
		self.assertEquals(19, episode.season)
		self.assertEquals(1, episode.episode)

	def testEpguidesEndedShow(self):
		# This one is no longer on the air
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_kr2008.html')
		show = self.store.getShowByUrl(
				'test/testdata/epguides_kr2008.html')
		self.assertEquals(episoder.Show.ENDED, show.status)

	def testEpguidesEncoding(self):
		# This one has funny characters
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_buzzcocks.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[20]
		self.assertEquals(
			'Zoë Ball, Louis Eliot, Graham Norton, Keith Duffy',
			episodes[20].title.encode('utf8'))

	def testEpguidesWithAnchor(self):
		# This one has an anchor tag before the bullet for season 6
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_futurama.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes.pop()
		self.assertEquals(6, episode.season)

	def testEpguidesWithTrailerAndRecap(self):
		# This one has [Trailer] and [Recap] in episode titles
		then = datetime.date(1970, 1, 1)
		self._parse('test/testdata/epguides_house.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[len(episodes) - 3]
		self.assertEquals('Unwritten', episode.title)

		episode = episodes[len(episodes) - 2]
		self.assertEquals('Massage Therapy', episode.title)

if __name__ == '__main__':
	unittest.main()
