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

from pyepisoder.database import Meta


class MetaInformationTest(TestCase):

	def test_str_and_repr(self):

		meta = Meta()
		meta.key = "version"
		meta.value = "1.0"

		self.assertEqual(str(meta), "Meta: version = 1.0")
		self.assertEqual(repr(meta), "Meta: version = 1.0")

def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(MetaInformationTest))
	return suite
