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

class TestDataStore(unittest.TestCase):
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

		id = show.show_id

		self.assertTrue(id > 0, "id is %d, must be > 0" % id)
		shows = self.store.getShows()

		self.assertEqual(1, len(shows))
		self.assertEqual(id, shows[0].show_id)
		self.assertEqual('test show', shows[0].show_name)

		show2 = episoder.Show('moo show', url='http://test.show.2')
		show2 = self.store.addShow(show2)
		id2 = show2.show_id
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
		self.assertEqual(3, len(self.store.getShows()))

		self.store.addShow(showB)
		self.assertEqual(4, len(self.store.getShows()))

		try:
			self.store.addShow(showC)
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
		self.assertFalse(self._accept('http://epguides.com/Lost'))
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
		self.assertEquals(102, len(self.store.getEpisodes(then, 99999)))

		self.store.clear()
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_bsg.html')
		self.assertEquals(74, len(self.store.getEpisodes(then, 99999)))

		self.store.clear()
		self.assertEquals(0, len(self.store.getEpisodes()))
		self._parse('test/testdata/epguides_eureka.html')
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEquals(43, len(episodes))
		self.assertEquals('Best in Faux', episodes[27].title)

		self.store.clear()
		self._parse('test/testdata/epguides_american_idol.html')
		episodes = self.store.getEpisodes(then, 99999)

		self.assertEquals('Pride Goeth Before The Fro',
				episodes[10].title)

		self.store.clear()
		self._parse('test/testdata/epguides_midsomer_murders.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[1]

		self.assertEquals(1, episode.season)
		self.assertEquals(1, episode.episode)

		# this one lacks a season number somewhere
		self.store.clear()
		self._parse('test/testdata/epguides_48_hours_mistery.html')

		self._parse('test/testdata/epguides_kr2008.html')
		show = self.store.getShowByUrl(
				'test/testdata/epguides_kr2008.html')
		self.assertEquals(episoder.Show.ENDED, show.status)

		self.store.clear()
		self._parse('test/testdata/epguides_buzzcocks.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[20]
		self.assertEquals(
			'Zoë Ball, Louis Eliot, Graham Norton, Keith Duffy',
			episodes[20].title.encode('utf8'))

class testTVComParser(unittest.TestCase):
	def setUp(self):
		self.path = tempfile.mktemp()
		self.store = episoder.DataStore(self.path)
		self.parser = plugins.TVComParser()

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
		url = 'test/testdata/tvcom_%s ' % show
		show = self.store.getShowByUrl(url)

		if not show:
			show = episoder.Show('Unnamed', url=url)
			show = self.store.addShow(show)

		self.parser._fetchPage = self._openfile
		self.parser.parse(show, self.store)

	def _accept(self, url):
		return self.parser.accept(url)

	def testAccept(self):
		self.assertFalse(self._accept('http://epguides.com/Lost'))
		self.assertFalse(self._accept('http://www.tv.com/Lost'))
		self.assertTrue(self._accept
				('http://www.tv.com/monk/show/9130/'))
		self.assertTrue(self._accept
				('http://www.tv.com/black-books/show/5108/'))
		self.assertTrue(self._accept
				('http://www.tv.com/battlestar-galactica-2003/show/23557/'))
		self.assertTrue(self._accept
				('http://www.tv.com/south-park/show/344/'))
		self.assertTrue(self._accept
				('http://www.tv.com/penn-and-teller-bullsh!/show/17579/'))
		self.assertTrue(self._accept
				('http://www.tv.com/True+Blood/show/74645/'))
		self.assertTrue(self._accept
				('http://www.tv.com/Eastbound+%26+Down/show/75067/'))

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

		show = self.store.getShowByUrl('test/testdata/tvcom_csi ')
		self.assertEqual('CSI', show.name)
		self.assertEqual(episoder.Show.RUNNING, show.status)

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

	def testParseFile3(self):
		then = datetime.date(1970, 1, 1)
		self._parse('kr2008')
		show = self.store.getShowByUrl('test/testdata/tvcom_kr2008 ')

		self.assertEqual(episoder.Show.ENDED, show.status)

if __name__ == '__main__':
	unittest.main()
