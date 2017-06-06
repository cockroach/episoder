# episoder, https://github.com/cockroach/episoder
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

from sys import stdout
from datetime import date, timedelta
from smtplib import SMTP


class FormattingRenderer(object):

	def __init__(self, fmt, dateformat):

		self._format = fmt
		self._dateformat = dateformat

	def format(self, episode):

		string = self._format

		airdate = episode.airdate.strftime(self._dateformat)
		string = string.replace("%airdate", airdate)
		string = string.replace("%show", episode.show.name)
		string = string.replace("%season", str(episode.season))
		string = string.replace("%epnum", "%02d" % episode.episode)
		string = string.replace("%eptitle", episode.title)
		string = string.replace("%totalep", str(episode.totalnum))
		string = string.replace("%prodnum", episode.prodnum)

		return string


class ConsoleRenderer(FormattingRenderer):

	RED = "\033[31;1m"
	CYAN = "\033[36;1m"
	GREY = "\033[30;0m"
	GREEN = "\033[32;1m"
	YELLOW = "\033[33;1m"

	def __init__(self, fmt, dateformat, dest=stdout):

		super(ConsoleRenderer, self).__init__(fmt, dateformat)
		self._dest = dest

	def __str__(self):

		return "ConsoleRenderer"

	def __repr__(self):

		return 'ConsoleRenderer("%s", "%s", <..>)' % (self._format,
							self._dateformat)

	def _render_color(self, text, col):

		self._dest.write("%s%s%s\n" % (col, text, ConsoleRenderer.GREY))

	def _render_no_color(self, string, _):

		self._dest.write("%s\n" % (string))

	def _render(self, episode, render, color):

		render(self.format(episode), color)

	def render(self, episodes, use_colors=True):

		today = date.today()
		yesterday = today - timedelta(1)
		tomorrow = today + timedelta(1)

		if use_colors:
			render = self._render_color
		else:
			render = self._render_no_color

		for episode in episodes:

			if episode.airdate == yesterday:
				color = ConsoleRenderer.RED
			elif episode.airdate == today:
				color = ConsoleRenderer.YELLOW
			elif episode.airdate == tomorrow:
				color = ConsoleRenderer.GREEN
			elif episode.airdate > tomorrow:
				color = ConsoleRenderer.CYAN
			else:
				color = ConsoleRenderer.GREY

			self._render(episode, render, color)


class NewEpisodesNotification(FormattingRenderer):

	def __init__(self, episodes, fmt, datefmt):

		super(NewEpisodesNotification, self).__init__(fmt, datefmt)
		self._episodes = episodes

	def __str__(self):

		return "Notification: %s new episode(s)" % len(self._episodes)

	def __repr__(self):

		eps = "<(%d x Episode)" % len(self._episodes)
		fmt = 'NewEpisodesNotification(%s, "%s", "%s")'
		return fmt % (eps, self._format, self._dateformat)

	def get(self):

		return "".join("%s\n" % self.format(e) for e in self._episodes)

	def send(self, notifier, to, pretend=False):

		body = "Your upcoming episodes:\n\n"

		for episode in self._episodes:
			body += "%s\n" % self.format(episode)

			if not pretend:
				episode.notified = date.today()

		notifier.send(body, to, pretend)


class EmailNotifier(object):

	def __init__(self, server, port, smtp=SMTP):

		self._server = server
		self._port = port
		self._smtp = smtp
		self._user = None
		self._password = None

		self.use_tls = False

	def __str__(self):

		return "EmailNotifier"

	def __repr__(self):

		fmt = 'EmailNotifier("%s", %d, %s)'
		return fmt % (self._server, self._port, str(self._smtp))

	def _get_header(self, to, subject):

		return "From: %s\nTo: %s\nSubject: %s" % (to, to, subject)

	def login(self, user, password):

		self._user = user
		self._password = password

	def send(self, body, to, pretend=False):

		header = self._get_header(to, "Upcoming TV episodes")
		message = "%s\n%s" % (header, body)

		if pretend:
			print(message)
			return

		server = self._smtp(self._server, self._port)

		if self.use_tls:
			server.starttls()
		if self._user:
			server.login(self._user, self._password)

		server.sendmail(to, to, message)
		server.quit()
