"""
	portable-movie-organizer
	------------------------
	
	Copyright (C) 2010 Ali Aafee
	
	This file is part of portable-movie-organizer.

	portable-movie-organizer is free software: you can redistribute it 
	and/or modify it under the terms of the GNU General Public License 
	as published by the Free Software Foundation, either version 3 of 
	the License, or (at your option) any later version.

	portable-movie-organizer is distributed in the hope that it will 
	be useful, but WITHOUT ANY WARRANTY; without even the implied 
	warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
	See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with portable-movie-organizer.  
	If not, see <http://www.gnu.org/licenses/>.
"""

import WebCatch
import urllib
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
import os.path
from threading import Thread
import wx
import BackgroundJob


EVT_DONE_GETMETADATA = BackgroundJob.EVT_DONE_BACKGROUND_JOB


class MetaDataGetter(BackgroundJob.BackgroundJob):
	def __init__(self, parent, title, year, postersPath):	
		BackgroundJob.BackgroundJob.__init__(self, parent)
		self.title = title
		self.year = year
		self.postersPath = postersPath
		self.metadata = None
		
	def run(self):
		self.metadata = GetMetadata(self.title, self.year, self.postersPath)
		self.donejob(metadata=self.metadata)


def _comma_to_list(valuesString):
	values = []
	split = valuesString.split(",")
	
	for value in split:
		values.append(value.strip())
		
	return values
	
	
def _get_unique_filename(dirname, shortname, extension):
	filename = shortname + extension
	result = os.path.join(dirname, filename)
	
	i = 0
	while os.path.isfile(result):
		i += 1
		filename = u"{0}({1}){2}".format(shortname, i, extension)
		result = os.path.join(dirname, filename)
		
	return filename
	
	
def _fix_poster_name(name):
	name = name.replace(u':','')
	name = name.replace(u'\\','')
	name = name.replace(u'/','')
	name = name.replace(u'*','')
	name = name.replace(u'"','')
	name = name.replace(u'<','')
	name = name.replace(u'>','')
	name = name.replace(u'?','')
	name = name.replace(u'&','')
	name = name.replace(u'.','')
	
	return name
	
	
def _download_poster(poster, posterName, postersPath):
	if poster != '':
		poster = WebCatch.get(poster)
		
		posterName = _get_unique_filename(postersPath, _fix_poster_name(posterName), '.jpg')
		
		filename = os.path.join(postersPath, posterName)
			
		f = open(filename, 'wb')
		f.write(poster)
		f.close()
		
		return posterName
	else:
		return ''


def GetMetadata(title, year, postersPath):
	options = {
		't': title,
		'y': year,
		'r': 'XML',
		'plot': 'short'
	}
	
	url = u'http://www.imdbapi.com/?{0}'.format(urllib.urlencode(options))
	
	print(url)
	
	xmlString = WebCatch.get(url)
	print 'got xml'
	
	if xmlString == '':
		print u'ImdbApi: got no data from internet'
		return None
	
	try:
		dom = parseString(xmlString)
	except ExpatError, e:
		print u'ImdbApi: xml parse error: {0}'.format(e)
		return None
	
	movies = dom.getElementsByTagName("movie")
	
	if len(movies) > 0:
		movie = movies[0]
		
		result = {}
		
		result['title'] = ''
		result['image'] = ''
		result['released'] = ''
		result['runtime'] = ''
		result['rated'] = ''
		result['summary'] = ''
		result['genres'] = []
		result['actors'] = []
		result['directors'] = []
		
		
		for key in movie.attributes.keys():
		
			value = movie.attributes[key].value
			
			if key == u'title':
				result['title'] = value
				
			if key == u'poster':
				result['image'] = value
				
			elif key == u'year':
				result['released'] = value
				
			elif key == u'runtime':
				result['runtime'] = value
			
			elif key == u'rated':
				result['rated'] = value	
			
			elif key == u'plot':
				result['summary'] = value
			
			elif key == u'genre':
				result['genres'] = _comma_to_list(value)
				
			elif key == u'actors':
				result['actors'] = _comma_to_list(value)
				
			elif key == u'director':
				result['directors'] = _comma_to_list(value)
				
		result['image'] = _download_poster(result['image'], result['title'], postersPath)
		print 'got poster'
		
		return result
	else:
		return None
				
				
	
	
	
def main():
	metadata = GetMetadata('2012')
	for key, value in metadata.iteritems():
		print u"{0} = {1}".format(key, value)
		print " "
	
	


if __name__ == '__main__' :
	main()
