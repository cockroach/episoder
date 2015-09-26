# episoder, https://github.com/cockroach/episoder
#
# Copyright (C) 2004-2015 Stefan Ott. All rights reserved.
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

from __future__ import absolute_import

import re
import os
import yaml
import pyepisoder
import time
import logging

try:
    import urllib.request as urllib2
except:
    import urllib2
import tempfile

from datetime import date, datetime, timedelta
from tvdb_api import BaseUI, Tvdb, tvdb_shownotfound

from .episode import Episode


def parser_for(url):

	parsers = [ TVDB, EpguidesParser, TVComDummyParser ]

	for parser in parsers:
		if parser.accept(url):
			return parser()

	return None


class TVDB(object):

	def __init__(self):
		self.logger = logging.getLogger('TVDB')
		self.latest = 0

	def __str__(self):
		return 'TheTVDB.com parser'

	@staticmethod
	def accept(url):
		return url.isdigit()

	def parse(self, show, store, args):

		self.show = show
		self.store = store

		if show.url.isdigit():
			id = int(show.url)
		else:
			self.logger.error('%s is not a valid TVDB show id'
					% show.url)
			return

		tv = Tvdb(apikey=args.tvdb_key)

		try:
			data = tv[id]
		except tvdb_shownotfound:
			self.logger.error('Show %s not found' % id)
			return

		self.show.name = data.data.get('seriesname')
		self.show.updated = datetime.now()

		for (idx, season) in data.items():
			for (epidx, episode) in season.items():
				self.__addEpisode(episode)

		now = int(time.time())
		age = now - self.latest

		# 31536000 seconds -> 1 year
		# 2419200 seconds -> 4 weeks
		if age > 31536000:
			self.show.setEnded()
		elif age > 2419200:
			self.show.setSuspended()
		else:
			self.show.setRunning()

		self.store.commit()

	def __addEpisode(self, episode):
		name = episode.get('episodename')
		season = episode.get('seasonnumber', 0)
		num = episode.get('episodenumber', 0)

		airdate = episode.get('firstaired')

		if not airdate:
			self.logger.debug('Throwing away episode %s' % num)
			return

		airdate = time.strptime(airdate, '%Y-%m-%d')
		airdate = datetime(airdate.tm_year, airdate.tm_mon,
						airdate.tm_mday).date()

		self.latest = max(self.latest, int(airdate.strftime('%s')))

		prodcode = episode.get('productioncode')
		abs_number = episode.get('absolute_number', 0)

		# can be None which is bad
		if not abs_number:
			abs_number = 0

		self.logger.debug('Found episode %s' % name)

		e = Episode(self.show, name, season, num, airdate, prodcode,
			abs_number)

		self.store.addEpisode(e)

	@staticmethod
	def lookup(text):
		result = []

		class search(BaseUI):
			def selectSeries(self, allSeries):
				result.extend(allSeries)
				return BaseUI.selectSeries(self, allSeries)

		db = Tvdb(custom_ui=search)
		db[text]

		return result


class EpguidesParser(object):

	def __init__(self):
		self.logger = logging.getLogger('EpguidesParser')

		dirname = os.path.dirname(pyepisoder.__file__)
		prefix = os.path.join(dirname, '..')

		self.awkfile = os.path.join(prefix, 'extras',
				'episoder_helper_epguides.awk')
		self.awk = '/usr/bin/awk'
		self.user_agent = None
		self.url = ''

	def __str__(self):
		return 'epguides.com parser'

	@staticmethod
	def accept(url):
		exp = 'http://(www.)?epguides.com/.*'
		return re.match(exp, url)

	def parse(self, show, store, _):
		self.show = show

		try:
			webdata = self._fetchPage(self.show.url)
		except Exception as e:
			self.logger.error("Error fetching %s: %s" %
					(self.show.url, e))
			return

		self.parseFile(webdata, store)
		os.unlink(webdata)

	def parseFile(self, file, store):
		self.store = store
		yamlfile = self._runAwk(file)
		data = self._readYaml(yamlfile)
		self.store.commit()
		os.unlink(yamlfile)

	def _fetchPage(self, url):
		self.logger.info('Fetching ' + url)
		headers = {}

		if (self.user_agent):
			headers['User-Agent'] = self.user_agent

		request = urllib2.Request(url, None, headers)
		result = urllib2.urlopen(request)
		(fd, name) = tempfile.mkstemp()
		file = os.fdopen(fd, 'w')
		file.write(result.read())
		file.close()
		self.logger.debug("Stored in %s" % name)
		return name

	def _runAwk(self, webdata):
		yamlfile = tempfile.mktemp()
		logfile = tempfile.mktemp()
		cleanwebdata = tempfile.mktemp()
		self.logger.info('Parsing data')

		self.logger.debug('Calling iconv')
		cmd = 'iconv -c -f utf8 -t iso-8859-1 %s >%s' % (webdata,
				cleanwebdata)
		if os.system(cmd) != 0:
			self.logger.debug('iconv failed, ignoring')

		self.logger.debug('Calling AWK')
		cmd = 'LC_CTYPE=UTF-8 %s -f %s output=%s %s >%s 2>&1' % (
				self.awk, self.awkfile, yamlfile,
				cleanwebdata, logfile)
		if os.system(cmd) != 0:
			raise Exception("Error running %s" % cmd)

		file = open(logfile)
		self.logger.debug(file.read().strip())
		file.close()

		os.unlink(cleanwebdata)
		os.unlink(logfile)
		return yamlfile

	def _readYaml(self, yamlfile):
		self.logger.debug('Reading YAML')
		file = open(yamlfile)
		data = yaml.load(file.read().decode('iso8859-1'))
		file.close()

		show_data = data[0]

		if not 'title' in show_data or not show_data['title']:
			self.logger.warning('Show has no title, aborting')
			self.store.rollback()
			return

		title = show_data['title']
		self.show.name = title

		if show_data['running']:
			self.show.setRunning()
		else:
			self.show.setEnded()

		self.show.updated = datetime.now()

		self.logger.debug('Got show "%s"', title)

		if not 'episodes' in show_data or not show_data['episodes']:
			self.logger.warning('Show has no episodes, aborting')
			self.store.rollback()
			return

		episodes = show_data['episodes']

		for episode in episodes:
			self.logger.debug('Found episode %s' % episode['title'])
			self.store.addEpisode(Episode(self.show,
					episode['title'],
					episode['season'],
					episode['episode'],
					episode['airdate'],
					episode['prodnum'],
					episode['totalepnum']
				))


class TVComDummyParser(object):

	def __str__(self):
		return 'dummy tv.com parser to detect old urls (DO NOT USE)'

	@staticmethod
	def accept(url):
		exp = 'http://(www.)?tv.com/.*'
		return re.match(exp, url)

	def parse(self, source, _, __):
		logging.error("The url %s is no longer supported" % source.url)


class ConsoleRenderer(object):

	def __init__(self, format, dateformat):
		self.logger = logging.getLogger('ConsoleRenderer')
		self.format = format
		self.dateformat = dateformat


	def _render(self, episode, color, endColor):

		string = self.format
		airdate = episode.airdate.strftime(self.dateformat)
		string = string.replace('%airdate', airdate)
		string = string.replace('%show', episode.show.name)
		string = string.replace('%season', str(episode.season))
		string = string.replace('%epnum', "%02d" % episode.episode)
		string = string.replace('%eptitle', unicode(episode.title))
		string = string.replace('%totalep', str(episode.total))
		string = string.replace('%prodnum', unicode(episode.prodnum))
		print ("%s%s%s" % (color, string.encode('utf8'), endColor))


	def render(self, episodes, color=True):

		today = date.today()
		yesterday = today - timedelta(1)
		tomorrow = today + timedelta(1)

		if color:
			red = '\033[31;1m'
			cyan = '\033[36;1m'
			grey = '\033[30;0m'
			green = '\033[32;1m'
			yellow = '\033[33;1m'
		else:
			red = ''
			cyan = ''
			grey = ''
			green = ''
			yellow = ''

		for episode in episodes:
			if episode.airdate == yesterday:
				color = red
			elif episode.airdate == today:
				color = yellow
			elif episode.airdate == tomorrow:
				color = green
			elif episode.airdate > tomorrow:
				color = cyan
			else:
				color = grey

			self._render(episode, color, grey)
