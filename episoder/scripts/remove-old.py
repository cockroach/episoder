#!/usr/bin/env python

# episoder old episode remover, http://episoder.sourceforge.net/
#
# Copyright (c) 2004-2008 Stefan Ott. All rights reserved.
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
#
# $Id$

import sys
import yaml
import datetime
import shutil
from tempfile import mkstemp
from os import fdopen

class Show(object):
	def __init__(self, title):
		self.title = title
		self.episodes = []

	def addEpisode(self, episode):
		self.episodes.append(episode)

	def removeEpisodesBefore(self, then):
		newEpisodes = []

		for episode in self.episodes:
			if episode.airdate >= then:
				newEpisodes.append(episode)

		self.episodes = newEpisodes

	def accept(self, visitor):
		visitor.visit(self)

	def __str__(self):
		return "%s (%d episodes)" % (self.title, len(self.episodes))

class Episode(object):
	def __init__(self, title, season, episode, airdate, prodnum, total):
		self.title = title
		self.season = season
		self.episode = episode
		self.airdate = airdate
		self.prodnum = prodnum or ''
		self.total = total

	def __str__(self):
		return "%sx%s: %s" % (self.season, self.episode, self.title)

class EpisoderData(object):
	def __init__(self, datafile):
		self.datafile = datafile
		self.shows = []

	def load(self):
		file = open(self.datafile)
		data = yaml.load(file.read())
		file.close()
		if not data['Shows']:
			return 1
		for showData in data['Shows']:
			title = showData['title']
			show = Show(title)
			for episodeData in showData['episodes']:
				episodeNum = episodeData['episode']
				airDate = episodeData['airdate']
				season = episodeData['season']
				title = episodeData['title']
				totalEpNum = episodeData['totalepnum']
				prodnum = episodeData['prodnum']
				episode = Episode(title, season, episodeNum,
					airDate, prodnum, totalEpNum)
				show.addEpisode(episode)
			self.shows.append(show)

	def removeBefore(self, baseDate, numDays):
		difference = datetime.timedelta(days=numDays)
		then = baseDate - difference
		for show in self.shows:
			show.removeEpisodesBefore(then)

	def save(self):
		data = {}
		data['Shows'] = []

		for show in self.shows:
			showData = {}
			showData['title'] = show.title
			showData['episodes'] = []
			for episode in show.episodes:
				episodeData = {}
				episodeData['episode'] = episode.episode
				episodeData['airdate'] = episode.airdate
				episodeData['season'] = episode.season
				episodeData['title'] = episode.title
				episodeData['totalepnum'] = episode.total
				episodeData['prodnum'] = episode.prodnum
				showData['episodes'].append(episodeData)
			data['Shows'].append(showData)

		try:
			(fd, name) = mkstemp()
			file = fdopen(fd, 'w')
			file.write(yaml.safe_dump(data))
			file.close()
			shutil.move(name, self.datafile)
		except IOError:
			print "Could not write data"

def usage():
	print "Usage: %s <datafile> <days-in-past> [base-date]" % sys.argv[0]
	print "base-date can be specified as YYYY-MM-DD"

def main(argv=sys.argv):
	if len(argv) < 3:
		usage()
		return 1

	try:
		dbfile=argv[1]
		daysInPast=int(argv[2])
	except ValueError:
		usage()
		print "\nInvalid value for days-in-past"
		return 2

	if (len(argv) == 4):
		baseDateData = argv[3].split('-')
		if len(baseDateData) != 3:
			usage()
			return 4
		baseDate = datetime.date(int(baseDateData[0]),
			int(baseDateData[1]), int(baseDateData[2]))
		try:
			baseDate = datetime.date(int(baseDateData[0]),
				int(baseDateData[1]), int(baseDateData[2]))
		except TypeError:
			usage()
			print "\nInvalid value for base-date"
			return 5
	else:
		baseDate = datetime.date.today()

	data = EpisoderData(dbfile)
	try:
		data.load()
		data.removeBefore(baseDate, daysInPast)
		data.save()
	except IOError:
		print "Could not open %s" % dbfile
		return 3

if __name__ == "__main__":
	sys.exit(main())
