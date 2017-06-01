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

from unittest import TestCase, TestSuite, TestLoader

from pyepisoder.sources import TVDB, EpguidesParser, TVComDummyParser
from pyepisoder.sources import parser_for


class SourcesTest(TestCase):

	def test_parser_for(self):

		parser = parser_for("12345")
		self.assertTrue(isinstance(parser, TVDB))

		parser = parser_for("http://www.epguides.com/test/")
		self.assertTrue(isinstance(parser, EpguidesParser))

		parser = parser_for("http://www.tv.com/test/")
		self.assertTrue(isinstance(parser, TVComDummyParser))

		parser = parser_for("http://www.googe.com/")
		self.assertIsNone(parser)


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(SourcesTest))
	return suite
