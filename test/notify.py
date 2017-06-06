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

import sys

from datetime import date
from unittest import TestCase, TestSuite, TestLoader

try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO

from pyepisoder.database import Show, Episode
from pyepisoder.output import EmailNotifier, NewEpisodesNotification


class MockSMTPInstance(object):

	instance = None

	def __init__(self, server, port):

		self.server = server
		self.port = port
		self.reset()

	def reset(self):

		self.count = 0
		self.data = {}
		self.tls = 0
		self.user = None
		self.password = None

	def sendmail(self, from_addr, to_addr, msg):

		self.data["from"] = from_addr
		self.data["to"] = to_addr
		self.data["msg"] = msg

	def quit(self):

		self.from_addr = self.data.get("from")
		self.to_addr = self.data.get("to")
		self.msg = self.data.get("msg")
		self.count += 1

	def starttls(self):

		self.tls = 1

	def login(self, user, password):

		self.user = user
		self.password = password


class MockSMTP(object):

	instance = None

	def __init__(self, server, port):

		if not MockSMTP.instance:
			MockSMTP.instance = MockSMTPInstance(server, port)

	def __str__(self):

		return "MockSMTP"

	def sendmail(self, from_addr, to_addr, msg):

		self.instance.sendmail(from_addr, to_addr, msg)

	def quit(self):

		self.instance.quit()

	def _get_count(self):

		return MockSMTP.instance.count

	def _set_count(self, num):

		MockSMTP.instance.count = num

	def _get_from(self):

		return MockSMTP.instance.from_addr

	def _get_to(self):

		return MockSMTP.instance.to_addr

	def _get_msg(self):

		return MockSMTP.instance.msg

	def _get_tls(self):

		return MockSMTP.instance.tls

	def _get_user(self):

		return MockSMTP.instance.user

	def _get_password(self):

		return MockSMTP.instance.password

	def starttls(self):

		MockSMTP.instance.starttls()

	def login(self, user, password):

		MockSMTP.instance.login(user, password)

	def reset(self):

		MockSMTP.instance.reset()

	count = property(_get_count, _set_count)
	from_addr = property(_get_from)
	to_addr = property(_get_to)
	msg = property(_get_msg)
	tls = property(_get_tls)
	user = property(_get_user)
	password = property(_get_password)


class NotificationTest(TestCase):

	def setUp(self):

		self.show = Show(u"Test show 36")
		self.show.show_id = 36

		then = date(2008, 1, 1)
		self.episode = Episode(u"Episode 41", 2, 5, then, u"NX01", 3)
		self.episode.show = self.show

		self.smtp = MockSMTP(None, None)
		self.smtp.reset()

	def test_str_and_repr(self):

		notify = EmailNotifier("localhost", 25, MockSMTP)
		self.assertEqual(str(notify), "EmailNotifier")
		self.assertEqual(repr(notify), 'EmailNotifier("localhost", 25, '
			'<class \'test.notify.MockSMTP\'>)')

		message = NewEpisodesNotification([], "", "")
		self.assertEqual(str(message), "Notification: 0 new episode(s)")
		message = NewEpisodesNotification([None], "", "")
		self.assertEqual(str(message), "Notification: 1 new episode(s)")
		message = NewEpisodesNotification([None, None], "", "")
		self.assertEqual(str(message), "Notification: 2 new episode(s)")

		message = NewEpisodesNotification([None, None], "fmt", "Ymd")
		expect = 'NewEpisodesNotification(<(2 x Episode), "fmt", "Ymd")'
		self.assertEqual(repr(message), expect)

	def test_send_mail_pretend(self):

		show1 = Show(u"Columbo", u"")
		ep1 = Episode(u"Episode 1", 1, 1, date(2014, 8, 10), u"x", 1)
		ep2 = Episode(u"Episode 2", 1, 2, date(2014, 12, 1), u"x", 2)

		ep1.show = show1
		ep2.show = show1

		stdout = sys.stdout
		sys.stdout = StringIO()

		message = NewEpisodesNotification([ep1, ep2],
			"[%airdate] %show %seasonx%epnum - %eptitle","%Y-%m-%d")
		notifier = EmailNotifier("localhost", 97, MockSMTP)
		message.send(notifier, "xy@example.org", pretend=True)

		self.assertEqual(self.smtp.count, 0)
		output = sys.stdout.getvalue()

		sys.stdout = stdout

		# StringIO adds an extra \n
		self.assertEqual(output,
			"From: xy@example.org\n"
			"To: xy@example.org\n"
			"Subject: Upcoming TV episodes\n"
			"Your upcoming episodes:\n\n"
			"[2014-08-10] Columbo 1x01 - Episode 1\n"
			"[2014-12-01] Columbo 1x02 - Episode 2\n\n")

	def test_send_mail(self):

		show1 = Show(u"Columbo", u"")
		ep1 = Episode(u"Episode 1", 1, 1, date(2014, 8, 10), u"x", 1)
		ep2 = Episode(u"Episode 2", 1, 2, date(2014, 12, 1), u"x", 2)

		ep1.show = show1
		ep2.show = show1

		self.assertIsNone(ep1.notified)
		self.assertIsNone(ep2.notified)

		notifier = EmailNotifier("localhost", 97, MockSMTP)
		message = NewEpisodesNotification([ep1, ep2],
			"[%airdate] %show %seasonx%epnum - %eptitle","%Y-%m-%d")
		message.send(notifier, "person@example.org")

		self.assertEqual(self.smtp.count, 1)
		self.assertEqual(self.smtp.tls, 0)
		self.assertEqual(self.smtp.user, None)
		self.assertEqual(self.smtp.password, None)
		self.assertEqual(self.smtp.from_addr, "person@example.org")
		self.assertEqual(self.smtp.to_addr, "person@example.org")
		self.assertEqual(self.smtp.msg,
			"From: person@example.org\n"
			"To: person@example.org\n"
			"Subject: Upcoming TV episodes\n"
			"Your upcoming episodes:\n\n"
			"[2014-08-10] Columbo 1x01 - Episode 1\n"
			"[2014-12-01] Columbo 1x02 - Episode 2\n")

		self.assertIsNotNone(ep1.notified)
		self.assertIsNotNone(ep2.notified)

	def test_send_mail_tls(self):

		show1 = Show(u"Columbo", u"")
		ep1 = Episode(u"Episode 1", 1, 1, date(2014, 8, 10), u"x", 1)
		ep2 = Episode(u"Episode 2", 1, 2, date(2014, 12, 1), u"x", 2)

		ep1.show = show1
		ep2.show = show1

		message = NewEpisodesNotification([ep1, ep2],
			"[%airdate] %show %seasonx%epnum - %eptitle","%Y-%m-%d")

		notifier = EmailNotifier("localhost", 97, MockSMTP)
		notifier.use_tls = True
		message.send(notifier, "xy@example.org")

		self.assertEqual(self.smtp.count, 1)
		self.assertEqual(self.smtp.tls, 1)
		self.assertEqual(self.smtp.user, None)
		self.assertEqual(self.smtp.password, None)
		self.assertEqual(self.smtp.from_addr, "xy@example.org")
		self.assertEqual(self.smtp.to_addr, "xy@example.org")
		self.assertEqual(self.smtp.msg,
			"From: xy@example.org\n"
			"To: xy@example.org\n"
			"Subject: Upcoming TV episodes\n"
			"Your upcoming episodes:\n\n"
			"[2014-08-10] Columbo 1x01 - Episode 1\n"
			"[2014-12-01] Columbo 1x02 - Episode 2\n")

	def test_send_mail_auth(self):

		message = NewEpisodesNotification([], "", "")

		notifier = EmailNotifier("localhost", 97, MockSMTP)
		notifier.login("someuser", "somepass")
		message.send(notifier, "xy@example.org")

		self.assertEqual(self.smtp.count, 1)
		self.assertEqual(self.smtp.tls, 0)
		self.assertEqual(self.smtp.user, "someuser")
		self.assertEqual(self.smtp.password, "somepass")
		self.assertEqual(self.smtp.from_addr, "xy@example.org")
		self.assertEqual(self.smtp.to_addr, "xy@example.org")
		self.assertEqual(self.smtp.msg,
			"From: xy@example.org\n"
			"To: xy@example.org\n"
			"Subject: Upcoming TV episodes\n"
			"Your upcoming episodes:\n\n")


def test_suite():

	suite = TestSuite()
	loader = TestLoader()
	suite.addTests(loader.loadTestsFromTestCase(NotificationTest))
	return suite
