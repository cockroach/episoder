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

from pyepisoder.sources import TVDB, Epguides, TVCom, ParserSelector

class SourcesTest(TestCase):

	def test_parser_for(self):

		sel = ParserSelector.instance()

		parser1 = sel.parser_for("12345")
		self.assertTrue(isinstance(parser1, TVDB))

		parser2 = sel.parser_for("12346")
		self.assertTrue(isinstance(parser2, TVDB))

		self.assertEqual(parser1, parser2)

		parser = sel.parser_for("http://www.epguides.com/test/")
		self.assertTrue(isinstance(parser, Epguides))

		parser = sel.parser_for("http://www.tv.com/test/")
		self.assertTrue(isinstance(parser, TVCom))

		parser = sel.parser_for("http://www.googe.com/")
		self.assertIsNone(parser)


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(SourcesTest))
	return suite
