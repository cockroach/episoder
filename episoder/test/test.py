#!/usr/bin/env python
#coding=iso-8859-1

import os
import unittest
from BeautifulSoup import BeautifulSoup
from episoder import *
from episoder_output_plain import *
from episoder_parser_tvcom import *

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

		episode = Episode('Paternity', 1, 2,datetime.date(2004, 11, 23),
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

	def testSave(self):
		(fd, name) = mkstemp()
		data = EpisoderData(name)

		show1 = Show('TestShow1')
		show2 = Show('TestShow2')
		episode1 = Episode('Test1', 1, 2,datetime.date(2004, 11, 23),
			'HOU-105', 2)
		episode2 = Episode('Test2', 1, 2,datetime.date(2004, 11, 23),
			'HOU-105', 2)
		episode3 = Episode('Test3', 1, 2,datetime.date(2004, 11, 23),
			'HOU-105', 2)
		episode4 = Episode('Test4', 1, 2,datetime.date(2004, 11, 23),
			'HOU-105', 2)
		show1.addEpisode(episode1)
		show1.addEpisode(episode2)
		show1.addEpisode(episode3)
		show2.addEpisode(episode4)

		data.shows.append(show1)
		data.shows.append(show2)

		data.save()

		data2 = EpisoderData(name)
		data2.load()
		shows2 = data2.shows

		self.assertEquals(episode1, shows2[0].episodes[0])
		self.assertEquals(episode2, shows2[0].episodes[1])
		self.assertEquals(episode3, shows2[0].episodes[2])
		self.assertEquals(episode4, shows2[1].episodes[0])

		os.remove(name)

class PlainRendererTest(unittest.TestCase):
	def setUp(self):
		(_, datafile) = mkstemp()
		(fd, rcname) = mkstemp()
		file = fdopen(fd, 'w')
		file.write("data=%s\n" % datafile)
		file.close()
		environ['EPISODER_RC_FILE'] = rcname
		self.rcfile = rcname
		self.datafile = datafile

	def tearDown(self):
		os.remove(environ['EPISODER_RC_FILE'])
		os.remove(self.datafile)

	def testRender(self):
		data = EpisoderData('data/parsed01.yaml')
		data.load()

		renderer = PlainRenderer(data)
		renderer.render()

		file = os.stat(self.datafile)
		self.assertTrue(file.st_size > 1000)

	def __render(self):
		data = EpisoderData('data/parsed01.yaml')
		data.load()

		renderer = PlainRenderer(data)
		renderer.render()

	def __setFormatting(self, format):
		file = open(self.rcfile, 'w')
		file.write("data=%s\n" % self.datafile)
		file.write("format=%s\n" % format)
		file.close()

	def testFormatting(self):
		self.__setFormatting("%eptitle %totalep %prodnum")
		self.__render()

		file = open(self.datafile)
		contents = file.readlines()
		file.close()

		self.assertEqual("Pilot 1 HOU-101\n", contents[0])
		self.assertEqual("Paternity 2 HOU-105\n", contents[1])
		self.assertEqual("Que Será Será 52 HOU-306\n", contents[51])

		self.__setFormatting("%epnum %season %show %airdate")
		self.__render()

		file = open(self.datafile)
		contents = file.readlines()
		file.close()

		self.assertEqual("03 1 House, M.D. 2004-11-30\n", contents[2])

class TVComParserDummyFetcher(object):
	def __init__(self, file='data/tvcom_2008.1_sample_1.html'):
		self.requested = []
		self.file = file

	def urlopen(self, url):
		self.requested.append(url)
		file = open(self.file)
		data = file.read()
		file.close()
		return data

class TVComParserSeasonTest(unittest.TestCase):
	def setUp(self):
		self.url = 'e.html'
		self.season = TVComSeason(1, self.url)
		self.fetcher = TVComParserDummyFetcher()
		self.season.fetcher = self.fetcher

	def testSeasonURLGeneration(self):
		self.season.parse()
		self.assertEquals(self.fetcher.requested[0], 'e.html?season=1')

		season = TVComSeason(8, self.url)
		season.fetcher = self.fetcher
		season.parse()
		self.assertEquals(self.fetcher.requested[1], 'e.html?season=8')

	def testSeasonParse(self):
		episodes = self.season.parse()
		self.assertTrue(len(episodes) > 0)
		episode = episodes[2]

		self.assertEqual("Crate 'n Burial", episode.title)
		self.assertEqual(1, episode.season)
		self.assertEqual(3, episode.episode)
		self.assertEqual(datetime.date(2000, 10, 20), episode.airdate)
		self.assertEqual('103', episode.prodnum)
		self.assertEqual(3, episode.total)

	def testEncoding(self):
		self.fetcher.file = 'data/tvcom_2008.1_sample_2.html'
		episodes = self.season.parse()
		episode = episodes[51]
		self.assertEqual("Que Será Será", episode.title)

class TVComParserPageTest(unittest.TestCase):
	def __getSeasonDummy(self, seasonNum):
		season = TVComSeason(seasonNum, '')
		season.fetcher = TVComParserDummyFetcher(
			file='data/tvcom_2008.1_sample_3.html')
		return season.parse()

	def setUp(self):
		self.file = 'data/tvcom_2008.1_sample_2.html'
		self.url = 'e.html'
		self.page = TVComPage(self.url, self.file)
		self.page.getSeason = self.__getSeasonDummy

	def testGetSoup(self):
		soup = self.page.getSoup()
		self.assertTrue(isinstance(soup, BeautifulSoup))

	def testFindSeasons(self):
		soup = self.page.getSoup()
		seasons = self.page.findSeasons(soup)
		self.assertEqual(range(1,6), seasons)

	def testFindTitle(self):
		soup = self.page.getSoup()
		title = self.page.findTitle(soup)
		self.assertEqual('House', title)

	def testParse(self):
		self.page.cached = 'data/tvcom_2008.1_sample_3.html'
		yamlfile = self.page.parse()

		data = EpisoderData(yamlfile)
		data.load()
		show = data.shows[0]

		self.assertEquals('', show.episodes[0].prodnum)
		self.assertEquals('3T6601', show.episodes[1].prodnum)

		os.remove(yamlfile)

if __name__ == "__main__":
	unittest.main()
