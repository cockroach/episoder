# episoder, https://github.com/cockroach/episoder
# -*- coding: utf8 -*-
#
# Copyright (C) 2004-2017 Stefan Ott. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import requests
from datetime import date, datetime

from unittest import TestCase, TestSuite, TestLoader

from pyepisoder.episoder import Show
from pyepisoder.sources import TVDB, TVDBNotLoggedInError, InvalidLoginError
from pyepisoder.sources import TVDBShowNotFoundError

from .util import MockResponse, MockArgs


class FakeRequest(object):

	def __init__(self, method, url, body, headers, params):

		self.method = method
		self.url = url
		self.body = body
		self.headers = headers
		self.params = params


class MockRequests(object):

	def __init__(self):

		self.requests = []

	def load_fixture(self, name):

		with open("test/fixtures/tvdb_%s.json" % name, "rb") as file:

			data = file.read()

		return data

	def fixture(self, name, code):

		response = self.load_fixture(name)
		return MockResponse(response, "utf8", code)

	def get_search(self, url, headers, params):

		term = params.get("name")

		if term == "Frasier":
			return self.fixture("search_frasier", 200)
		elif term == "Friends":
			return self.fixture("search_friends", 200)

		return self.fixture("error_404", 404)

	def get_episodes(self, url, headers, params):

		id = int(url.split("/")[-2])
		p = params.get("page", 1)

		try:
			return self.fixture("test_show_%d_%d_eps" % (id,p), 200)
		except IOError:
			return self.fixture("error_404", 404)

	def get_show(self, url, headers, params):

		id = int(url.split("/")[-1])

		try:
			return self.fixture("test_show_%d" % id, 200)
		except IOError:
			return self.fixture("error_404", 404)

	def get(self, url, headers={}, params={}):

		req = FakeRequest("GET", url, "", headers, params)
		self.requests.append(req)

		if url.startswith("https://api.thetvdb.com/search/series"):

			return self.get_search(url, headers, params)

		elif url.startswith("https://api.thetvdb.com/series"):

			if url.endswith("/episodes"):
				return self.get_episodes(url, headers, params)
			else:
				return self.get_show(url, headers, params)

		return MockResponse("{}", "utf8", 404)

	def post_login(self, body, headers):

		data = json.loads(body)
		key = data.get("apikey")

		if key == "fake-api-key":

			text = '{ "token": "fake-token" }'
			return MockResponse(text.encode("utf8"), "utf8", 200)

		text = '{"Error": "Not Authorized"}'
		return MockResponse(text.encode("utf8"), "utf8", 401)

	def post(self, url, body, headers = {}):

		req = FakeRequest("POST", url, body, headers, {})
		self.requests.append(req)

		if url.startswith("https://api.thetvdb.com/login"):

			return self.post_login(body.decode("utf8"), headers)

		return MockResponse("{}", "utf8", 404)


class MockStore(object):

	def __init__(self):

		self.episodes = []

	def addEpisode(self, episode):

		self.episodes.append(episode)

	def commit(self):

		pass


class TVDBTest(TestCase):

	def setUp(self):

		self.req = MockRequests()
		self.args = MockArgs("fake-api-key", "episoder/test")

		self.__get_orig = requests.get
		self.__post_orig = requests.post
		requests.get = self.req.get
		requests.post = self.req.post

	def tearDown(self):

		requests.get = self.__get_orig
		requests.post = self.__post_orig

	def test_parser_name(self):

		parser = TVDB()
		self.assertEqual(u"thetvdb.com parser", str(parser))

	def test_need_login(self):

		tvdb = TVDB()
		with self.assertRaises(TVDBNotLoggedInError):
			tvdb.lookup(u"Frasier", self.args)

		tvdb.login(MockArgs("fake-api-key"))
		tvdb.lookup(u"Frasier", self.args)

		tvdb.login(MockArgs("fake-api-key"))
		tvdb.lookup(u"Frasier", self.args)

	def test_login(self):

		tvdb = TVDB()
		tvdb.login(MockArgs("fake-api-key"))

		reqs = len(self.req.requests)
		self.assertTrue(reqs > 0)

		req = self.req.requests[-1]
		self.assertEqual(req.url, "https://api.thetvdb.com/login")
		self.assertEqual(req.method, "POST")
		self.assertEqual(req.body.decode("utf8"),
						'{"apikey": "fake-api-key"}')
		headers = req.headers
		self.assertEqual(headers.get("Content-type"),"application/json")

		tvdb.login(MockArgs("fake-api-key"))
		self.assertEqual(reqs, len(self.req.requests))

	def test_login_failure(self):

		tvdb = TVDB()

		with self.assertRaises(InvalidLoginError):
			tvdb.login(MockArgs("wrong-api-key"))

		with self.assertRaises(InvalidLoginError):
			tvdb.login(MockArgs("wrong-api-key"))

		with self.assertRaises(InvalidLoginError):
			tvdb.login(MockArgs("wrong-api-key"))

		tvdb.login(MockArgs("fake-api-key"))

	def test_search_no_hit(self):

		tvdb = TVDB()
		tvdb.login(MockArgs("fake-api-key"))

		with self.assertRaises(TVDBShowNotFoundError):
			tvdb.lookup("NoSuchShow", self.args)

	def test_search_single(self):

		tvdb = TVDB()
		tvdb.login(MockArgs("fake-api-key"))

		shows = list(tvdb.lookup("Frasier", self.args))

		req = self.req.requests[-1]
		self.assertEqual(req.url,
					"https://api.thetvdb.com/search/series")
		self.assertEqual(req.params, {"name": "Frasier"})
		self.assertEqual(req.method, "GET")
		self.assertEqual(req.body, "")

		content_type = req.headers.get("Content-type")
		self.assertEqual(content_type, "application/json")

		auth = req.headers.get("Authorization")
		self.assertEqual(auth, "Bearer fake-token")

		self.assertEqual(len(shows), 1)
		show = shows[0]
		self.assertEqual(show.name, "Frasier")
		self.assertEqual(show.url, "77811")

	def test_search_multiple(self):

		tvdb = TVDB()
		tvdb.login(MockArgs("fake-api-key"))

		shows = list(tvdb.lookup("Friends", self.args))

		self.assertEqual(len(shows), 3)
		self.assertEqual(shows[0].name, "Friends")
		self.assertEqual(shows[1].name, "Friends (1979)")
		self.assertEqual(shows[2].name, "Friends of Green Valley")

	def test_accept_url(self):

		self.assertTrue(TVDB.accept("123"))
		self.assertFalse(TVDB.accept("http://www.epguides.com/test"))

	def test_encoding_utf8(self):

		tvdb = TVDB()
		tvdb.login(self.args)

		show = Show(u"unnamed show", url=u"73739")
		show.show_id = 73739 # TODO: wtf?
		self.assertTrue(TVDB.accept(show.url))
		store = MockStore()

		tvdb.parse(show, store, self.args)

		self.assertEqual("Lost", show.name)
		self.assertEqual(Show.ENDED, show.status)
		self.assertEqual(len(store.episodes), 1)

		episode = store.episodes[0]
		self.assertEqual(episode.title, u"Exposé")


	def test_parse(self):

		tvdb = TVDB()

		show = Show(u"unnamed show", url=u"260")
		show.show_id = 260 # TODO: wtf?
		self.assertTrue(TVDB.accept(show.url))
		store = MockStore()

		with self.assertRaises(TVDBNotLoggedInError):
			tvdb.parse(show, None, self.args)

		tvdb.login(self.args)
		tvdb.parse(show, store, self.args)

		req = self.req.requests[-2]
		self.assertEqual(req.url, "https://api.thetvdb.com/series/260")
		self.assertEqual(req.params, {})
		self.assertEqual(req.method, "GET")
		self.assertEqual(req.body, "")

		content_type = req.headers.get("Content-type")
		self.assertEqual(content_type, "application/json")

		auth = req.headers.get("Authorization")
		self.assertEqual(auth, "Bearer fake-token")

		req = self.req.requests[-1]
		self.assertEqual(req.url,
				"https://api.thetvdb.com/series/260/episodes")
		self.assertEqual(req.params, {"page": 1})
		self.assertEqual(req.method, "GET")
		self.assertEqual(req.body, "")

		content_type = req.headers.get("Content-type")
		self.assertEqual(content_type, "application/json")

		auth = req.headers.get("Authorization")
		self.assertEqual(auth, "Bearer fake-token")

		self.assertEqual(show.name, "test show")
		self.assertEqual(show.status, Show.RUNNING)

		timediff = datetime.now() - show.updated
		self.assertTrue(timediff.total_seconds() < 1)

		self.assertEqual(len(store.episodes), 2)

		episode = store.episodes[0]
		self.assertEqual(episode.title, "Unnamed episode")
		self.assertEqual(episode.season, 0)
		self.assertEqual(episode.episode, 0)
		self.assertEqual(episode.airdate, date(1990, 1, 18))
		self.assertEqual(episode.prodnum, "UNK")
		self.assertEqual(episode.total, 1)

		episode = store.episodes[1]
		self.assertEqual(episode.title, "The Good Son")
		self.assertEqual(episode.season, 1)
		self.assertEqual(episode.episode, 1)
		self.assertEqual(episode.airdate, date(1993, 9, 16))
		self.assertEqual(episode.total, 2)

	def test_parse_paginated(self):

		tvdb = TVDB()
		store = MockStore()
		show = Show(u"unnamed show", url=u"261")
		show.show_id = 261

		tvdb.login(self.args)
		tvdb.parse(show, store, self.args)

		self.assertEqual(show.status, Show.ENDED)
		self.assertEqual(len(store.episodes), 8)

		episode = store.episodes[0]
		self.assertEqual(episode.title, "First")

		episode = store.episodes[1]
		self.assertEqual(episode.title, "Second")

		episode = store.episodes[2]
		self.assertEqual(episode.title, "Third")

		episode = store.episodes[3]
		self.assertEqual(episode.title, "Fourth")

		episode = store.episodes[4]
		self.assertEqual(episode.title, "Fifth")

		episode = store.episodes[5]
		self.assertEqual(episode.title, "Sixth")

		episode = store.episodes[6]
		self.assertEqual(episode.title, "Seventh")

		episode = store.episodes[7]
		self.assertEqual(episode.title, "Eighth")

	def test_parse_invalid_show(self):

		tvdb = TVDB()
		tvdb.login(self.args)

		show = Show(u"test show", url=u"293")

		with self.assertRaises(TVDBShowNotFoundError):
			tvdb.parse(show, None, self.args)

	def test_parse_show_with_invalid_data(self):

		tvdb = TVDB()
		store = MockStore()
		tvdb.login(self.args)
		show = Show(u"unnamed show", url=u"262")
		show.show_id = 262

		tvdb.parse(show, store, self.args)
		self.assertEqual(len(store.episodes), 2)

	def test_user_agent(self):

		tvdb = TVDB()
		store = MockStore()
		show = Show(u"unnamed show", url=u"262")
		show.show_id = 262

		tvdb.login(self.args)
		tvdb.lookup("Frasier", self.args)
		tvdb.parse(show, store, self.args)

		self.assertEqual(len(self.req.requests), 4)

		req = self.req.requests[0]
		headers = req.headers
		self.assertEqual(headers.get("User-Agent"), "episoder/test")

		req = self.req.requests[1]
		headers = req.headers
		self.assertEqual(headers.get("User-Agent"), "episoder/test")

		req = self.req.requests[2]
		headers = req.headers
		self.assertEqual(headers.get("User-Agent"), "episoder/test")

		req = self.req.requests[3]
		headers = req.headers
		self.assertEqual(headers.get("User-Agent"), "episoder/test")


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(TVDBTest))
	return suite
