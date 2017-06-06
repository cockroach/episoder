# episoder, https://github.com/cockroach/episoder
# -*- coding: utf8 -*-
# # Copyright (C) 2004-2017 Stefan Ott. All rights reserved.
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

from datetime import date, timedelta
from unittest import TestCase, TestSuite, TestLoader

try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO

from pyepisoder.database import Show, Episode
from pyepisoder.output import ConsoleRenderer


class OutputTest(TestCase):

	def setUp(self):

		self.show = Show(u"Test show 36")
		self.show.show_id = 36
		self.io = StringIO()

		then = date(2008, 1, 1)
		self.episode = Episode(u"Episode 41", 2, 5, then, u"NX01", 3)
		self.episode.show = self.show

	def test_str_and_repr(self):

		renderer = ConsoleRenderer("%show", "%Y%m%d", self.io)
		self.assertEqual(str(renderer), "ConsoleRenderer")
		self.assertEqual(repr(renderer),
			'ConsoleRenderer("%show", "%Y%m%d", <..>)')

		renderer = ConsoleRenderer("%show", "%Y%m%d")
		self.assertEqual(str(renderer), "ConsoleRenderer")
		self.assertEqual(repr(renderer),
			'ConsoleRenderer("%show", "%Y%m%d", <..>)')

	def test_render_airdate(self):

		renderer = ConsoleRenderer("%airdate", "%Y%m%d", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"20080101\n")

		self.episode.airdate = date(2015, 2, 3)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"20080101\n20150203\n")

	def test_render_show_name(self):

		renderer = ConsoleRenderer("%show", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"Test show 36\n")

		self.show.name = "Test 55"
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"Test show 36\nTest 55\n")

	def test_render_season_number(self):

		renderer = ConsoleRenderer("%season", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"2\n")

		self.episode.season = 12
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"2\n12\n")

	def test_render_episode_number(self):

		renderer = ConsoleRenderer("%epnum", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"05\n")

		self.episode.episode = 22
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"05\n22\n")

	def test_render_episode_title(self):

		renderer = ConsoleRenderer("%eptitle", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"Episode 41\n")

		self.episode.title = "Episode 8"
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"Episode 41\nEpisode 8\n")

	def test_render_total_episode_number(self):

		renderer = ConsoleRenderer("%totalep", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"3\n")

		self.episode.totalnum = 90
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"3\n90\n")

	def test_render_prodnum(self):

		renderer = ConsoleRenderer("%prodnum", "", self.io)
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"NX01\n")

		self.episode.prodnum = "ABCD"
		renderer.render([self.episode], False)
		self.assertEqual(self.io.getvalue(), u"NX01\nABCD\n")

	def test_render_combined(self):

		self.show.name = "Frasier"
		self.episode.airdate = date(1998, 9, 24)
		self.episode.season = 6
		self.episode.episode = 1
		self.episode.title = "Good Grief"

		fmt="%airdate: %show %seasonx%epnum - %eptitle"
		renderer = ConsoleRenderer(fmt, "%Y-%m-%d", self.io)
		renderer.render([self.episode], False)

		out=self.io.getvalue()
		self.assertEqual(out, "1998-09-24: Frasier 6x01 - Good Grief\n")

	def test_render_colors(self):

		today = date.today()

		# Two days ago -> grey
		io = StringIO()
		renderer = ConsoleRenderer("%airdate", "%Y", io)
		then = today - timedelta(2)
		self.episode.airdate = then
		expect = "\033[30;0m%s\033[30;0m\n" % then.strftime("%Y")
		renderer.render([self.episode], True)
		self.assertEqual(expect, io.getvalue())

		# Yesterday -> red
		io = StringIO()
		renderer = ConsoleRenderer("%airdate", "%Y", io)
		then = today - timedelta(1)
		self.episode.airdate = then
		expect = "\033[31;1m%s\033[30;0m\n" % then.strftime("%Y")
		renderer.render([self.episode], True)
		self.assertEqual(expect, io.getvalue())

		# Today -> yellow
		io = StringIO()
		renderer = ConsoleRenderer("%airdate", "%Y", io)
		then = today
		self.episode.airdate = then
		expect = "\033[33;1m%s\033[30;0m\n" % then.strftime("%Y")
		renderer.render([self.episode], True)
		self.assertEqual(expect, io.getvalue())

		# Tomorrow -> green
		io = StringIO()
		renderer = ConsoleRenderer("%airdate", "%Y", io)
		then = today + timedelta(1)
		self.episode.airdate = then
		expect = "\033[32;1m%s\033[30;0m\n" % then.strftime("%Y")
		renderer.render([self.episode], True)
		self.assertEqual(expect, io.getvalue())

		# The future -> cyan
		io = StringIO()
		renderer = ConsoleRenderer("%airdate", "%Y", io)
		then = today + timedelta(2)
		self.episode.airdate = then
		expect = "\033[36;1m%s\033[30;0m\n" % then.strftime("%Y")
		renderer.render([self.episode], True)
		self.assertEqual(expect, io.getvalue())


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(OutputTest))
	return suite
