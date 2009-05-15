import os
import yaml
import logging
import urllib2
import tempfile
import datetime

def all():
	return {
		'parsing': [ EpguidesParser(), DummyParser() ],
		'output': [ ConsoleRenderer() ]
	}

def parser_for(url):
	parsers = all()['parsing']

	for parser in parsers:
		if parser.accept(url):
			return parser

	return None

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
		self.awkfile = '/home/stefan/projects/episoder/trunk/episoder/plugins/episoder_helper_epguides.awk'
		self.awk = '/usr/bin/awk'

	def __str__(self):
		return 'epguides.com parser'

	def accept(self, url):
		return url.startswith('http://www.epguides.com/')

	def parse(self, source, store):
		self.store = store
		url = source['url']

		if 'name' in source:
			name = source['name']
		else:
			name = None

		webdata = self._fetchPage(url)
		yamlfile = self._runAwk(webdata)
		data = self._readYaml(yamlfile, name)
		self.store.commit()
		os.unlink(webdata)
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
		return name

	def _runAwk(self, webdata):
		self.logger.info('Parsing data')
		self.logger.debug('Calling AWK')
		yamlfile = tempfile.mktemp()
		logfile = tempfile.mktemp()
		cmd = '%s -f %s output=%s %s >%s 2>&1' % (self.awk,
			self.awkfile, yamlfile, webdata, logfile)
		os.system(cmd)

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
			self.store.addEpisode(show_id, episode)

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



	"""

	if [ ! -z "$NODATE" ] && [ ! -z "$SEARCH_TEXT" ]; then
		echo -ne ${color_gray}
		grep -i "$SEARCH_TEXT" $EPISODER_DATAFILE | while read line; do
			DATE=${line:0:10}
			output=`echo $line | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/\`date +\"$DATE_FORMAT\" -d $DATE\`/" | sed -e "s/$SEARCH_TEXT/\\\\\E${color_green}\0\\\\\E${color_gray}/ig"`
			echo -e $output
		done
	else
		YESTERDAY=`get_date_by_offset -1`
		TODAY=`get_date_by_offset 0`
		TOMORROW=`get_date_by_offset 1`

		echo -ne ${color_red}
		grep "^$YESTERDAY" $EPISODER_DATAFILE | grep -i "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $YESTERDAY`/"

		echo -ne ${color_yellow}
		grep "^$TODAY" $EPISODER_DATAFILE | grep -i "$SEARCH_TEXT" | sed 's/.*/>\0</' | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $TODAY`/"

		echo -ne ${color_green}	
		grep "^$TOMORROW" $EPISODER_DATAFILE | grep -i "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $TOMORROW`/"

		echo -ne ${color_lightblue}
		for ((day=2; day <= $NUM_DAYS; day++)); do
			DATE=`get_date_by_offset $day`
			grep "^$DATE" $EPISODER_DATAFILE | grep -i "$SEARCH_TEXT" | sed s/^/\ / | sed -r "s/([0-9]{4}-[0-9]{2}-[0-9]{2})/`date +"$DATE_FORMAT" -d $DATE`/"
		done

	fi
	echo -ne ${color_default}"""
