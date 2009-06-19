# episoder, http://episoder.sourceforge.net/
#
# Copyright (C) 2004-2009 Stefan Ott. All rights reserved.
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
import logging
import urllib2
import tempfile
import datetime

from BeautifulSoup import BeautifulSoup
from episoder import Show, Episode

def all():
	return {
		'parsing': [ EpguidesParser(), TVComParser(), 
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

class EpguidesParser(object):
	def __init__(self):
		self.logger = logging.getLogger('EpguidesParser')
		self.awkfile = os.path.join(sys.prefix, "share", "episoder",
				"episoder_helper_epguides.awk")
		self.awk = '/usr/bin/awk'

	def __str__(self):
		return 'epguides.com parser'

	def accept(self, url):
		return url.startswith('http://www.epguides.com/')

	def parse(self, source, store):
		url = source['url']

		if 'name' in source:
			name = source['name']
		else:
			name = None

		webdata = self._fetchPage(url)
		self.parseFile(webdata, store, name)
		os.unlink(webdata)

	def parseFile(self, file, store, name=None):
		self.store = store
		yamlfile = self._runAwk(file)
		data = self._readYaml(yamlfile, name)
		self.store.commit()
		os.unlink(yamlfile)

	def _fetchPage(self, url):
		self.logger.info('Fetching ' + url)
		headers = { 'User-Agent': 'foo' }
		request = urllib2.Request(url, None, headers)
		result = urllib2.urlopen(request)
		(fd, name) = tempfile.mkstemp()
		file = os.fdopen(fd, 'w')
		file.write(result.read())
		file.close()
		self.logger.debug("Stored in %s" % name)
		return name

	def _runAwk(self, webdata):
		self.logger.info('Parsing data')
		self.logger.debug('Calling AWK')
		yamlfile = tempfile.mktemp()
		logfile = tempfile.mktemp()
		cmd = '%s -f %s output=%s %s >%s 2>&1' % (self.awk,
			self.awkfile, yamlfile, webdata, logfile)
		if os.system(cmd) != 0:
			raise "Error running %s" % cmd

		file = open(logfile)
		self.logger.debug(file.read().strip())
		file.close()

		os.unlink(logfile)
		return yamlfile

	def _readYaml(self, yamlfile, override_name=None):
		self.logger.debug('Reading YAML')
		file = open(yamlfile)
		data = yaml.load(file.read())
		file.close()

		show = data[0]

		if not 'title' in show or not show['title']:
			self.logger.warning('Show has no title, aborting')
			self.store.rollback()
			return

		if override_name:
			self.logger.debug('Overriding show name with %s',
					override_name)
			title = override_name
		else:
			title = show['title']

		self.logger.debug('Got show "%s"', title)
		show_id = self.store.addShow(title)
		self.logger.debug('Added with id %d', show_id)

		if not 'episodes' in show or not show['episodes']:
			self.logger.warning('Show has no episodes, aborting')
			self.store.rollback()
			return

		episodes = show['episodes']

		for episode in episodes:
			self.logger.debug('Found episode %s' % episode['title'])
			self.store.addEpisode(show_id, Episode(Show(show_id),
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
		logging.error("The url %s needs to be updated" % source['url'])

class TVComParser(object):
	def __init__(self):
		self.logger = logging.getLogger('TVComParser')

	def __str__(self):
		return 'tv.com parser'

	def accept(self, url):
		return re.match('http://(www.)?tv.com/\w+/show/\d+/?', url)

	def _fetchPage(self, url):
		self.logger.info('Fetching ' + url)
		headers = { 'User-Agent': 'foo' }
		request = urllib2.Request(url, None, headers)
		result = urllib2.urlopen(request)
		(fd, name) = tempfile.mkstemp()
		file = os.fdopen(fd, 'w')
		file.write(result.read())
		file.close()
		self.logger.debug("Stored in %s" % name)
		return name

	def parse(self, source, store):
		self.store = store
		self.episodes = {}
		self.show = None

		url = source['url']

		guidepage = self._fetchPage(url +
				'episode.html?season=All&shv=guide')
		listpage = self._fetchPage(url +
				'episode.html?season=All&shv=list')

		if 'name' in source:
			name = source['name']
		else:
			name = None

		file = open(listpage)
		self.parseListViewPage(BeautifulSoup(file.read().decode(
			'ISO-8859-1')))
		file.close()

		file = open(guidepage)
		self.parseGuideViewPage(BeautifulSoup(file.read().decode(
			'ISO-8859-1')))
		file.close()

		os.unlink(guidepage)
		os.unlink(listpage)

		show_id = self.store.addShow(self.show)
		for key in self.episodes:
			self.store.addEpisode(show_id, self.episodes[key])

		self.store.commit()

	def parseFile(self, filename, store, name=None):
		self.store = store
		self.episodes = {}
		self.show = None

		file = open(filename)
		data = file.read()
		soup = BeautifulSoup(data.decode('ISO-8859-1'))
		file.close()

		elements = soup.findAll('li',
				{ 'class': re.compile('episode.*')})

		switch = soup.find('a', { 'class': 'switch_to_guide'})

		if (switch):
			self.logger.debug('This is a list view page')
			self.parseListViewPage(soup)
		else:
			self.logger.debug('This is a guide view page')
			self.parseGuideViewPage(soup)

		show_id = self.store.addShow(self.show)
		for key in self.episodes:
			self.store.addEpisode(show_id, self.episodes[key])

		self.store.commit()

	def parseListViewPage(self, soup):
		h1 = soup.find('h1')
		show_name = h1.contents[0]
		self.show = show_name
		self.logger.debug('Got show "%s"' % show_name)

		elements = soup.findAll('tr', { 'class': 'episode' })

		for element in elements:
			tr = element.find('td', { 'class': 'number' })
			totalepnum = int(tr.contents[0].strip())

			tr = element.find('td', { 'class': 'prod_no' })
			if len(tr.contents) > 0:
				prodnum = tr.contents[0].strip()
			else:
				prodnum = ''

			reviews = element.find('td', { 'class': 'reviews' })
			link = reviews.contents[0]
			url = link['href']
			parts = url.split('/')
			id = int(parts[-2])

			self.logger.debug("Found episode %d (%d)" %
					(totalepnum, id))

			if not id in self.episodes:
				self.episodes[id] = Episode(Show(self.show),
					None, 0, 0, datetime.date.today(),
					None, 0)

			self.episodes[id].prodnum = prodnum
			self.episodes[id].total = totalepnum

	def parseGuideViewPage(self, soup):
		h1 = soup.find('h1')
		show_name = h1.contents[0]
		self.show = show_name
		self.logger.debug('Got show "%s"' % show_name)

		elements = soup.findAll('li',
				{ 'class': re.compile('episode.*')})

		for element in elements:
			meta = element.find('div', { 'class': 'meta' })
			data = meta.contents[0].strip()

			result = re.search('Season ([0-9]+).*Episode ([0-9]+)',
					data)
			season = result.group(1)
			episode_num = result.group(2)

			result = re.search('Aired: (.*)$', data)
			airdate = datetime.datetime.strptime(
				result.group(1), "%m/%d/%Y").date()

			h3 = element.find('h3')
			link = h3.find('a')
			title = link.contents[0]
			url = link['href']
			parts = url.split('/')
			id = int(parts[-2])

			if not id in self.episodes:
				self.episodes[id] = Episode(None, None, 0,
					0, datetime.date.today(), None, 0)

			self.episodes[id].season = season
			self.episodes[id].episode = episode_num
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
		print ("%s%s%s" % (color, string, ConsoleRenderer.DEFAULT))

	def render(self, store, options, config):
		self.config = config
		today = datetime.date.today()
		yesterday = today - datetime.timedelta(1)
		tomorrow = today + datetime.timedelta(1)

		if options['nodate']:
			startdate = datetime.date(1873, 1, 1)
			n_days = 109500 # should be fine until late 21xx :)
		else:
			startdate = options['date']
			n_days = options['days']

		if options['search']:
			episodes = store.search(options)
		else:
			episodes = store.getEpisodes(startdate, n_days)

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
