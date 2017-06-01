#!/usr/bin/env python
# -*- coding: utf8 -*-

from datetime import date
from unittest import TestCase, TestSuite, TestLoader

import requests

from pyepisoder.episoder import Show
from pyepisoder.plugins import EpguidesParser

from .util import MockResponse


class RequestLog(object):

	def __init__(self):

		self.requests = []

	def get(self, url):

		name = url.split("/").pop()

		if name == "test_iso_8859_1":
			charset = "iso-8859-1"
		else:
			charset = "utf8"

		with open("test/fixtures/epguides_%s.html" % name, "rb") as f:

			data = f.read()

		return MockResponse(data, charset)


class MockDB(object):

	def __init__(self):

		self.episodes = []

	def addEpisode(self, episode):

		self.episodes.append(episode)

	def commit(self):

		pass


class EpguidesParserTest(TestCase):

	def setUp(self):

		self.parser = EpguidesParser()
		self.parser.awkfile = "extras/episoder_helper_epguides.awk"

		self.req = RequestLog()
		self._get_orig = requests.get
		requests.get = self.req.get

	def tearDown(self):

		requests.get = self._get_orig

	def test_parser_name(self):

		parser = EpguidesParser()
		self.assertEqual("epguides.com parser", str(parser))

	def test_accept(self):

		parser = EpguidesParser()
		self.assertTrue(parser.accept("http://www.epguides.com/Lost"))
		self.assertFalse(parser.accept("http://epguides2.com/Lost"))
		self.assertFalse(parser.accept("http://www.tv.com/Lost"))

	def test_guess_encoding(self):

		req = RequestLog()

		res = req.get("http://epguides.com/test_iso_8859_1")
		self.assertEqual("iso-8859-1", self.parser.guess_encoding(res))

		res = req.get("http://epguides.com/bsg")
		self.assertEqual("utf8", self.parser.guess_encoding(res))

	def test_parse(self):

		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/lost")
		show.show_id = 93
		self.parser.parse(show, db)

		self.assertEqual("Lost", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(121, len(db.episodes))

		ep = db.episodes[0]
		self.assertEqual("Pilot (1)", ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(1, ep.episode)
		self.assertEqual(date(2004, 9, 22), ep.airdate)

		ep = db.episodes[9]
		self.assertEqual("Raised by Another", ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(10, ep.episode)
		self.assertEqual(date(2004, 12, 1), ep.airdate)

		ep = db.episodes[25]
		self.assertEqual("Man of Science, Man of Faith", ep.title)
		self.assertEqual(2, ep.season)
		self.assertEqual(1, ep.episode)
		self.assertEqual(date(2005, 9, 21), ep.airdate)

		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/bsg")
		show.show_id = 120
		self.parser.parse(show, db)

		self.assertEqual("Battlestar Galactica (2003)", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(73, len(db.episodes))

		ep = db.episodes[0]
		self.assertEqual("33", ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(1, ep.episode)
		self.assertEqual(date(2005, 1, 14), ep.airdate)

	def test_format_2(self):

		# Another format
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/eureka")
		show.show_id = 138
		self.parser.parse(show, db)

		self.assertEqual("Eureka", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(76, len(db.episodes))

		ep = db.episodes[0]
		self.assertEqual("Pilot", ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(1, ep.episode)
		self.assertEqual(date(2006, 7, 18), ep.airdate)

		ep = db.episodes[9]
		self.assertEqual("Purple Haze", ep.title)
		self.assertEqual(1, ep.season)
		self.assertEqual(10, ep.episode)
		self.assertEqual(date(2006, 9, 19), ep.airdate)

		ep = db.episodes[27]
		self.assertEqual("Best in Faux", ep.title)
		self.assertEqual(3, ep.season)
		self.assertEqual(3, ep.episode)
		self.assertEqual(date(2008, 8, 12), ep.airdate)

	def test_format_3(self):

		# Yet another format
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/midsomer_murders")
		show.show_id = 168
		self.parser.parse(show, db)

		self.assertEqual("Midsomer Murders", show.name)
		self.assertEqual(Show.RUNNING, show.status)
		self.assertEqual(101, len(db.episodes))

		episode = db.episodes[0]
		self.assertEqual(1, episode.season)
		self.assertEqual(1, episode.episode)
		self.assertEqual("Written in Blood", episode.title)
		self.assertEqual(date(1998, 3, 22), episode.airdate)

		episode = db.episodes[5]
		self.assertEqual(2, episode.season)
		self.assertEqual(2, episode.episode)
		self.assertEqual("Strangler's Wood", episode.title)
		self.assertEqual(date(1999, 2, 3), episode.airdate)

	def test_fancy_utf8_chars(self):

		# This one contains an illegal character somewhere
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/american_idol")
		show.show_id = 192
		self.parser.parse(show, db)

		self.assertEqual("American Idol", show.name)
		self.assertEqual(Show.RUNNING, show.status)
		self.assertTrue(len(db.episodes) >= 11)

		episode = db.episodes[11]
		self.assertEqual(u"Pride Goeth Before The ‘Fro", episode.title)
		self.assertEqual(1, episode.season)
		self.assertEqual(12, episode.episode)

	def test_missing_season_number(self):

		# This one lacks a season number somewhere
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/48_hours_mistery")
		show.show_id = 210
		self.parser.parse(show, db)

		self.assertEqual("48 Hours Mystery", show.name)
		self.assertEqual(Show.RUNNING, show.status)
		self.assertEqual(150, len(db.episodes))

		episode = db.episodes[0]
		self.assertEqual(19, episode.season)
		self.assertEqual(1, episode.episode)
		self.assertEqual("January 1988 Debut of 48 Hours",episode.title)
		self.assertEqual(date(1988, 1, 15), episode.airdate)
		self.assertEqual("01-01", episode.prodnum)

	def test_ended_show(self):

		# This one is no longer on the air
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/kr2008")
		show.show_id = 229
		self.parser.parse(show, db)

		self.assertEqual("Knight Rider (2008)", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(17, len(db.episodes))

		episode = db.episodes[3]
		self.assertEqual(1, episode.season)
		self.assertEqual(4, episode.episode)
		self.assertEqual("A Hard Day's Knight", episode.title)
		self.assertEqual(date(2008, 10, 15), episode.airdate)
		self.assertEqual("104", episode.prodnum)

	def test_encoding(self):

		# This one has funny characters
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/buzzcocks")
		show.show_id = 248
		self.parser.parse(show, db)

		self.assertEqual(u"Never Mind the Buzzcocks", show.name)
		self.assertEqual(Show.RUNNING, show.status)

		self.assertTrue(len(db.episodes) >= 21)
		episode = db.episodes[20]
		self.assertEqual(3, episode.season)
		self.assertEqual(4, episode.episode)
		title = u"Zoë Ball, Louis Eliot, Graham Norton, Keith Duffy"
		self.assertEqual(title, episode.title)
		self.assertEqual(date(1998, 3, 20), episode.airdate)

	def test_with_anchor(self):

		# This one has an anchor tag before the bullet for season 6
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/futurama")
		show.show_id = 267
		self.parser.parse(show, db)

		self.assertEqual("Futurama", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(124, len(db.episodes))

		episode = db.episodes.pop()
		self.assertEqual(7, episode.season)
		self.assertEqual(26, episode.episode)
		self.assertEqual("Meanwhile", episode.title)
		self.assertEqual(date(2013, 9, 4), episode.airdate)

	def test_with_trailer_and_recap(self):

		# This one has [Trailer] and [Recap] in episode titles
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/house")
		show.show_id = 285
		self.parser.parse(show, db)

		self.assertEqual("House, M.D.", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(176, len(db.episodes))

		episode = db.episodes[len(db.episodes) - 3]
		self.assertEqual(8, episode.season)
		self.assertEqual(20, episode.episode)
		self.assertEqual("Post Mortem", episode.title)
		self.assertEqual(date(2012, 5, 7), episode.airdate)

		episode = db.episodes[len(db.episodes) - 2]
		self.assertEqual("Holding On", episode.title)

	def test_encoding_iso8859_1(self):

		# Explicitly test ISO 8859-1 encoding
		db = MockDB()
		show = Show(u"none", url=u"http://epguides.com/test_iso_8859_1")
		show.show_id = 306
		self.parser.parse(show, db)

		self.assertEqual(len(db.episodes), 1)
		self.assertEqual(u"Episoder ISO-8859-1 Tëst", show.name)

		episode = db.episodes[0]
		self.assertEqual(u"äöü", episode.title)


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(EpguidesParserTest))
	return suite
