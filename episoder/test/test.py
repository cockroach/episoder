#!/usr/bin/env python

import unittest
from episoder import *

class EpisodeTest(unittest.TestCase):
	def testConstruct(self):
		episode = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 28)
		self.assertEqual(episode.title, 'Random')
		self.assertEqual(episode.season, 2)
		self.assertEqual(episode.episode, 14)
		self.assertEqual(episode.airdate, datetime.date(2008, 10, 01))
		self.assertEqual(episode.prodnum, 'Num01')
		self.assertEqual(episode.total, 28)

	def testEqual(self):
		episodeA = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 28)
		episodeB = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 28)
		episodeC = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 29)
		self.assertEqual(episodeA, episodeB)
		self.assertNotEqual(episodeA, episodeC)

class ShowTest(unittest.TestCase):
	def setUp(self):
		self.show = Show('My Random Show')

	def testConstruct(self):
		self.assertEqual('My Random Show', self.show.title)

	def testAddEpisode(self):
		episodeA = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 28)
		episodeB = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 29)
		self.show.addEpisode(episodeA)

		self.assertTrue(episodeA in self.show.episodes,
			"Episode not in list")
		self.assertFalse(episodeB in self.show.episodes,
			"Wrong episode in list")

	def testRemoveEpisodesBefore(self):
		episodeA = Episode('Random', 2, 14, datetime.date(2008, 10, 01),
			'Num01', 28)
		episodeB = Episode('Random', 2, 14, datetime.date(2008, 10, 02),
			'Num01', 28)
		episodeC = Episode('Random', 2, 14, datetime.date(2008, 10, 03),
			'Num01', 28)
		episodeD = Episode('Random', 2, 14, datetime.date(2008, 10, 04),
			'Num01', 28)
		episodeE = Episode('Random', 2, 14, datetime.date(2008, 10, 05),
			'Num01', 28)

		self.show.addEpisode(episodeA)
		self.show.addEpisode(episodeB)
		self.show.addEpisode(episodeC)
		self.show.addEpisode(episodeD)
		self.show.addEpisode(episodeE)

		show = Show('TestShow')

		show.episodes = self.show.episodes
		show.removeEpisodesBefore(datetime.date(2008, 10, 03))
		self.assertTrue(episodeC in show.episodes)
		self.assertFalse(episodeB in show.episodes)

		show.episodes = self.show.episodes
		show.removeEpisodesBefore(datetime.date(2008, 10, 05))
		self.assertTrue(episodeE in show.episodes)
		self.assertEqual(len(show.episodes), 1)

class EpisoderDataTest(unittest.TestCase):
	def setUp(self):
		self.data = EpisoderData('data/parsed01.yaml')
		self.data.load()

	def testLoad(self):
		show = self.data.shows[0]
		self.assertEqual(95, len(show.episodes))

		episode = Episode('Paternity', 1, 2, datetime.date(2004, 11, 23),
			'HOU-105', 2)
		self.assertEqual(episode, show.episodes[1])

	def testRemoveBefore(self):
		self.data.removeBefore(datetime.date(2008, 9, 23), 0)
		show = self.data.shows[0]
		self.assertEqual(8, len(show.episodes))

		self.data.load()
		self.data.removeBefore(datetime.date(2008, 9, 17), 0)
		show = self.data.shows[0]
		self.assertEqual(8, len(show.episodes))

		self.data.load()
		self.data.removeBefore(datetime.date(2008, 9, 17), 1)
		show = self.data.shows[0]
		self.assertEqual(9, len(show.episodes))

if __name__ == "__main__":
	unittest.main()
