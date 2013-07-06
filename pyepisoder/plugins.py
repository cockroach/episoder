# episoder, http://episoder.googlecode.com/
#
# Copyright (C) 2004-2012 Stefan Ott. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import re
import os
import sys
import yaml
import time
import logging
import urllib2
import tempfile
import datetime
import tvdb_api

from tvdb_api import BaseUI, Tvdb, tvdb_shownotfound

from BeautifulSoup import BeautifulSoup
from episode import Episode

def all():
	return {
		'parsing': [ EpguidesParser(), TVComParser(), TVDB(),
			TVComDummyParser() ],
		'output': [ ConsoleRenderer() ]
	}

def parser_for(url):
	parsers = all()['parsing']

	for parser in parsers:
		if parser.accept(url):
			return parser

	return None

def parser_named(name):
	parsers = all()['parsing']

	for parser in parsers:
		if parser.__class__.__name__ == name:
			return parser

	raise Exception('Parser %s not found\n' % name)

class DummyParser(object):
	def __init__(self):
		self.logger = logging.getLogger('DummyParser')

	def __str__(self):
		return 'dummy parser'

	def accept(self, url):
		return False

class TVDB(object):
	def __init__(self):
		self.logger = logging.getLogger('TVDB')

	def __str__(self):
		return 'TheTVDB.com parser'

	def accept(self, url):
		return url.isdigit()

	def parse(self, show, store):
		self.show = show
		self.store = store

		if show.url.isdigit():
			id = int(show.url)
		else:
			self.logger.error('%s is not a valid TVDB show id'
					% show.url)
			return

		tv = tvdb_api.Tvdb()

		try:
			data = tv[id]
		except tvdb_shownotfound:
			self.logger.error('Show %s not found' % id)
			return

		self.show.name = data.data.get('seriesname')
		self.show.updated = datetime.datetime.now()

		for (idx, season) in data.items():
			for (epidx, episode) in season.items():
				self.__addEpisode(episode)

		self.store.commit()

	def __addEpisode(self, episode):
		name = episode.get('episodename')
		season = episode.get('seasonnumber', 0)
		num = episode.get('episodenumber', 0)

		date = episode.get('firstaired')

		if not date:
			self.logger.debug('Throwing away episode %s' % num)
			return

		date = time.strptime(date, '%Y-%m-%d')
		date = datetime.datetime(date.tm_year, date.tm_mon,
						date.tm_mday).date()

		prodcode = episode.get('productioncode')
		abs_number = episode.get('absolute_number', 0)

		# can be None which is bad
		if not abs_number:
			abs_number = 0

		self.logger.debug('Found episode %s' % name)

		e = Episode(self.show, name, season, num, date, prodcode,
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
		self.awkfile = os.path.join(sys.prefix, "share", "episoder",
				"episoder_helper_epguides.awk")
		self.awk = '/usr/bin/awk'
		self.user_agent = None
		self.url = ''

	def __str__(self):
		return 'epguides.com parser'

	def accept(self, url):
		return url.startswith('http://www.epguides.com/')

	def parse(self, show, store):
		self.show = show

		BeautifulSoup.CDATA_CONTENT_ELEMENTS = ()

		try:
			webdata = self._fetchPage(self.show.url)
		except Exception, e:
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

		self.show.updated = datetime.datetime.now()

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

	def accept(self, url):
		return url.startswith('http://www.tv.com')

	def parse(self, source, _):
		logging.error("The url %s needs to be updated" % source.url)

class TVComParser(object):
	def __init__(self):
		self.logger = logging.getLogger('TVComParser')

	def __str__(self):
		return 'tv.com parser'

	def accept(self, url):
		exp = 'http://(www.)?tv.com/[-a-z0-9_!+%]+/show/\d+/?'
		return re.match(exp, url)

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

	def parse(self, show, store):
		self.store = store
		self.show = show
		self.episodes = {}

		try:
			guidepage = self._fetchPage(self.show.url +
				'episode.html?season=All&shv=guide')
			listpage = self._fetchPage(self.show.url +
				'episode.html?season=All&shv=list')
		except Exception, e:
			self.logger.error("Error fetching %s: %s" %
					(self.show.url, e))
			return

		file = open(listpage)
		data = file.read()
		file.close()

		cleanData = re.sub('<script.*?</script>', '',
				data.replace('\n', ' '))
		self.parseListViewPage(BeautifulSoup(cleanData.decode(
			'ISO-8859-1')))

		file = open(guidepage)
		data = file.read()
		file.close()
		cleanData = re.sub('<script.*?</script>', '',
				data.replace('\n', ' '))

		self.parseGuideViewPage(BeautifulSoup(cleanData.decode(
			'ISO-8859-1')))

		os.unlink(guidepage)
		os.unlink(listpage)

		self.show.updated = datetime.datetime.now()

		for key in self.episodes:
			episode = self.episodes[key]
			self.store.addEpisode(episode)

		self.store.commit()

	def parseFile(self, filename, store):
		self.store = store
		self.episodes = {}

		file = open(filename)
		data = file.read()
		file.close()

		cleanData = re.sub('<script.*?</script>', '',
				data.replace('\n', ' '))
		soup = BeautifulSoup(cleanData.decode('ISO-8859-1'))

		elements = soup.findAll('li',
				{ 'class': re.compile('episode.*')})

		switch = soup.find('a', { 'class': 'switch_to_guide'})

		if (switch):
			self.logger.debug('This is a list view page')
			self.parseListViewPage(soup)
		else:
			self.logger.debug('This is a guide view page')
			self.parseGuideViewPage(soup)

		for key in self.episodes:
			self.store.addEpisode(self.episodes[key])

		self.store.commit()

	def parseListViewPage(self, soup):
		div = soup.find('div', { 'class': 'title'})
		show_name = div.a.contents[0]
		self.show.name = show_name
		self.logger.debug('Got show "%s" (list)' % show_name)

		elements = soup.findAll('tr', { 'class': 'episode' })

		for element in elements:
			tr = element.find('td', { 'class': 'number' })
			totalepnum = int(tr.contents[0].strip())

			tr = element.find('td', { 'class': 'prod_no' })
			if len(tr.contents) > 0:
				prodnum = tr.contents[0].strip()
			else:
				prodnum = ''

			td = element.find('td', { 'class': 'title' })
			url = td.a['href']
			parts = url.split('/')
			id = int(parts[-2])

			self.logger.debug("Found episode %d (%d)" %
					(totalepnum, id))

			if not id in self.episodes:
				self.episodes[id] = Episode(self.show,
					None, 0, 0, datetime.date.today(),
					None, 0)

			self.episodes[id].prodnum = prodnum
			self.episodes[id].total = totalepnum

	def parseGuideViewPage(self, soup):
		div = soup.find('div', { 'class': 'title'})
		show_name = div.a.contents[0]
		self.show.name = show_name
		self.logger.debug('Got show "%s" (guide)' % show_name)

		span = soup.find('span', { 'class': 'tagline' })
		tagline = span.contents[0]

		if tagline.find('Ended') > -1:
			self.show.setEnded()

		elements = soup.findAll('li',
				{ 'class': re.compile('episode.*')})

		for element in elements:
			meta = element.find('div', { 'class': 'meta' })
			data = meta.contents[0].strip()

			result = re.search('Season ([0-9]+)', data)
			if result:
				season = result.group(1)
			else:
				season = 0

			result = re.search('Episode ([0-9]+)', data)
			if result:
				episode_num = result.group(1)
			else:
				episode_num = 0

			result = re.search('Air(s|ed): (.*)$', data)

			if result:
				airtime = time.strptime(
					result.group(2), "%m/%d/%Y")
				airdate = datetime.datetime(
					airtime.tm_year, airtime.tm_mon,
					airtime.tm_mday).date()
			else:
				airdate = datetime.date(1900, 1, 1)

			h3 = element.find('h3')
			link = h3.find('a')
			title = link.contents[0]
			url = link['href']
			parts = url.split('/')
			id = int(parts[-2])

			if not id in self.episodes:
				self.episodes[id] = Episode(self.show,
					None, 0, 0, datetime.date.today(),
					None, 0)

			self.episodes[id].season = int(season)
			self.episodes[id].episode = int(episode_num)
			self.episodes[id].airdate = airdate
			self.episodes[id].title = title

			self.logger.debug('Found episode %s (%d)' % (title, id))

class ConsoleRenderer(object):
	DEFAULT='\033[30;0m'
	RED='\033[31;1m'
	YELLOW='\033[33;1m'
	GREEN='\033[32;1m'
	LIGHTBLUE='\033[36;1m'
	GRAY=DEFAULT

	def __init__(self):
		self.logger = logging.getLogger('ConsoleRenderer')

	def _renderEpisode(self, episode, color):
		string = self.config['format']
		date = episode.airdate.strftime(self.config['dateformat'])
		string = string.replace('%airdate', date)
		string = string.replace('%show', episode.show.name)
		string = string.replace('%season', str(episode.season))
		string = string.replace('%epnum', "%02d" % episode.episode)
		string = string.replace('%eptitle', episode.title)
		string = string.replace('%totalep', str(episode.total))
		string = string.replace('%prodnum', str(episode.prodnum))
		print ("%s%s%s" % (color, string.encode('utf8'),
			ConsoleRenderer.DEFAULT))

	def render(self, store, options, config):
		self.config = config
		today = datetime.date.today()
		yesterday = today - datetime.timedelta(1)
		tomorrow = today + datetime.timedelta(1)

		if options['nodate']:
			startdate = datetime.date(1900, 1, 1)
			n_days = 109500 # should be fine until late 21xx :)
		else:
			startdate = options['date']
			n_days = options['days']

		if options['search']:
			episodes = store.search(options)
		else:
			episodes = store.getEpisodes(startdate, n_days)

		if not options['colors']:
			ConsoleRenderer.DEFAULT = ''
			ConsoleRenderer.RED = ''
			ConsoleRenderer.YELLOW = ''
			ConsoleRenderer.GREEN = ''
			ConsoleRenderer.LIGHTBLUE = ''

		for episode in episodes:
			if episode.airdate == yesterday:
				self._renderEpisode(episode,
						ConsoleRenderer.RED)
			elif episode.airdate == today:
				self._renderEpisode(episode,
						ConsoleRenderer.YELLOW)
			elif episode.airdate == tomorrow:
				self._renderEpisode(episode,
						ConsoleRenderer.GREEN)
			elif episode.airdate > tomorrow:
				self._renderEpisode(episode,
						ConsoleRenderer.LIGHTBLUE)
			else:
				self._renderEpisode(episode,
						ConsoleRenderer.DEFAULT)
