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

from datetime import date
from unittest import TestCase, TestSuite, TestLoader

from pyepisoder.database import Episode, Show


class EpisodeTest(TestCase):

	def test_construct(self):

		ep = Episode(u"First", 3, 8, date(2017, 1, 1), u"0XOR", 117)

		self.assertEqual(ep.show_id, None)
		self.assertEqual(ep.episode, 8)
		self.assertEqual(ep.airdate, date(2017, 1, 1))
		self.assertEqual(ep.season, 3)
		self.assertEqual(ep.title, u"First")
		self.assertEqual(ep.totalnum, 117)
		self.assertEqual(ep.prodnum, u"0XOR")

	def test_str_and_repr(self):

		show = Show(u"TvShow", u"")
		ep = Episode(u"First", 1, 1, date(2017, 1, 1), u"http://", 1)
		ep.show = show

		self.assertEqual(str(ep), "TvShow 1x01: First")
		self.assertEqual(repr(ep), 'Episode(u"First", 1, 1, '
					'date(2017, 1, 1), u"http://", 1)')

	def test_equality(self):

		ep1 = Episode(u"First", 1, 1, date(2017, 1, 1), u"http://", 1)
		ep1.show_id = 1

		ep2 = Episode(u"Second", 2, 2, date(2017, 1, 1), u"http://", 1)
		ep2.show_id = 2

		self.assertNotEqual(ep1, ep2)

		ep1.show_id = 2
		self.assertNotEqual(ep1, ep2)

		ep1.season = 2
		self.assertNotEqual(ep1, ep2)

		ep1.episode = 2
		self.assertEqual(ep1, ep2)

		ep1.season = 1
		self.assertNotEqual(ep1, ep2)

		ep1.season = 2
		ep1.show_id = 1
		self.assertNotEqual(ep1, ep2)

	def test_sorting(self):

		ep1 = Episode(u"A", 1, 1, date(2017, 1, 1), u"", 1)
		ep2 = Episode(u"D", 2, 2, date(2017, 1, 1), u"", 1)
		ep3 = Episode(u"E", 3, 1, date(2017, 1, 1), u"", 1)
		ep4 = Episode(u"B", 1, 2, date(2017, 1, 1), u"", 1)
		ep5 = Episode(u"C", 2, 1, date(2017, 1, 1), u"", 1)

		episodes = sorted([ep1, ep2, ep3, ep4, ep5])
		self.assertEqual(episodes, [ep1, ep4, ep5, ep2, ep3])

def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(EpisodeTest))
	return suite
