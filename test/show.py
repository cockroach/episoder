#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import tempfile
import datetime

from unittest import TestCase, TestSuite, TestLoader

import pyepisoder.episoder as episoder

class ShowTest(TestCase):

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


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(ShowTest))
	return suite
