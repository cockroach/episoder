#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import tempfile
import datetime

from unittest import TestCase, TestSuite, TestLoader

import pyepisoder.episoder as episoder
import pyepisoder.plugins as plugins


class EpguidesParserTest(TestCase):

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
		self.assertEqual(0, len(self.store.getEpisodes()))
		self._parse('test/fixtures/epguides_lost.html')
		self.store.commit()
		self.assertEqual(121, len(self.store.getEpisodes(then, 99999)))

		show = self.store.getShowByUrl(
				'test/fixtures/epguides_lost.html')
		self.assertEqual('Lost', show.name)
		self.assertEqual(episoder.Show.ENDED, show.status)

		self._parse('test/fixtures/epguides_lost.html')
		self.store.commit()
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEqual(121, len(episodes))

		ep = episodes[0]
		self.assertEqual('Pilot (1)', ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(1, ep.episode)

		ep = episodes[9]
		self.assertEqual('Raised by Another', ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(10, ep.episode)

		ep = episodes[25]
		self.assertEqual('Man of Science, Man of Faith', ep.title)
		self.assertEqual(2, ep.season)
		self.assertEqual(1, ep.episode)

		self.store.clear()
		self.assertEqual(0, len(self.store.getEpisodes()))
		self._parse('test/fixtures/epguides_bsg.html')
		self.assertEqual(73, len(self.store.getEpisodes(then, 99999)))

	def testEpguidesFormat2(self):

		# Another format
		then = datetime.date(1970, 1, 1)
		self.assertEqual(0, len(self.store.getEpisodes()))
		self._parse('test/fixtures/epguides_eureka.html')
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEqual(76, len(episodes))

		ep = episodes[0]
		self.assertEqual('Pilot', ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(1, ep.episode)

		ep = episodes[9]
		self.assertEqual('Purple Haze', ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(10, ep.episode)

		ep = episodes[27]
		self.assertEqual('Best in Faux', ep.title)
		self.assertEqual(3, ep.season)
		self.assertEqual(3, ep.episode)

	def testEpguidesFormat3(self):

		# Yet another format
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_midsomer_murders.html')
		episodes = self.store.getEpisodes(then, 99999)

		episode = episodes[0]
		self.assertEqual(1, episode.season)
		self.assertEqual(1, episode.episode)
		self.assertEqual('Written in Blood', episode.title)

		episode = episodes[5]
		self.assertEqual(2, episode.season)
		self.assertEqual(2, episode.episode)
		self.assertEqual("Strangler's Wood", episode.title)

	def testEpguidesRemoveIllegalChars(self):

		# This one contains an illegal character somewhere
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_american_idol.html')
		episodes = self.store.getEpisodes(then, 99999)

		episode = episodes[10]
		self.assertEqual('Pride Goeth Before The Fro', episode.title)
		self.assertEqual(1, episode.season)
		self.assertEqual(12, episode.episode)

	def testEpguidesMissingSeasonNumber(self):

		# This one lacks a season number somewhere
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_48_hours_mistery.html')
		episodes = self.store.getEpisodes(then, 99999)
		self.assertEqual(31, len(episodes))

		episode = episodes[0]
		self.assertEqual(19, episode.season)
		self.assertEqual(1, episode.episode)

	def testEpguidesEndedShow(self):

		# This one is no longer on the air
		self._parse('test/fixtures/epguides_kr2008.html')
		show = self.store.getShowByUrl(
				'test/fixtures/epguides_kr2008.html')
		self.assertEqual(episoder.Show.ENDED, show.status)

	def testEpguidesEncoding(self):

		# This one has funny characters
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_buzzcocks.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[20]
		self.assertEqual(
			'Zoë Ball, Louis Eliot, Graham Norton, Keith Duffy',
			episode.title.encode('utf8'))

	def testEpguidesWithAnchor(self):

		# This one has an anchor tag before the bullet for season 6
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_futurama.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes.pop()
		self.assertEqual(7, episode.season)

	def testEpguidesWithTrailerAndRecap(self):

		# This one has [Trailer] and [Recap] in episode titles
		then = datetime.date(1970, 1, 1)
		self._parse('test/fixtures/epguides_house.html')
		episodes = self.store.getEpisodes(then, 99999)
		episode = episodes[len(episodes) - 3]
		self.assertEqual('Post Mortem', episode.title)

		episode = episodes[len(episodes) - 2]
		self.assertEqual('Holding On', episode.title)


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(EpguidesParserTest))
	return suite
