import DbInterface
import threading
import os
import os.path
import urlparse
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import urllib
import time
from distutils.version import StrictVersion
import vlc


dirName = os.path.dirname(os.path.abspath(__file__))
dirName, fileName = os.path.split(dirName)
resDir = os.path.join(dirName, 'res')


class MediaServer(threading.Thread):
	def __init__(self, address, libraryPath, vlc="vlc"):
		self.libraryPath = libraryPath
		self._address = address
		self._started = False
		self._stopped = False
		self._vlc_instance = None
		self._vlc_player = None
		self._httpd = None
		
		self.categories = ['genre', 'actor', 'director', 'tag']
		
		threading.Thread.__init__(self)
		
		
	def _init_db(self):
		try:
			if os.path.isdir(self.libraryPath):
				self.metadataPath = os.path.join(self.libraryPath,'metadata')
			
				if not os.path.isdir(self.metadataPath):
					print "Cannot connect to the metadata database"
					return False
				
				self.postersPath = os.path.join(self.metadataPath, 'posters')
			
				if not os.path.isdir(self.postersPath):
						os.mkdir(self.postersPath)
						
				self.streamCatchPath = os.path.join(self.metadataPath, 'streamcatch')
				
				if not os.path.isdir(self.streamCatchPath):
					os.mkdir(self.streamCatchPath)
					
				self.db = DbInterface.DbInterface(
					os.path.join(self.metadataPath,'metadata.db'))
			
				if not self.db.isConnected():
					print "Cannot connect to the metadata database"
					return False
					
				return True
					
			else:
				print "Library path is invalid"
				return False
				
		except OSError, e:
			print "Cannot access the library"
			return False
			
			
	def _is_valid_vlc(self):
		version = vlc.libvlc_get_version()
		version = version.partition(' ')[0]
		version = version.partition('-')[0]
		
		try:
			version_number = StrictVersion(version)
		except ValueError:
			return False
			
		req_version_number = StrictVersion('1.2.0')
		
		if version_number >= req_version_number:
			return True
		else:
			print False
		

	def run(self):
		if not self._init_db():
			print "Stopping server..."
			self._stopped = True
			return
			
		self._vlc_instance = vlc.Instance()
		
		
		def getTemplate(name):
			try:
				f = open(os.path.join(resDir,"{0}.html".format(name)))
				template = f.read()
				f.close()
				
				return unicode(template)
			except IOError:
				return 'templates are missing'
				
		
		def getHomeList():
			page = getTemplate('web-list')
			
			
			catlinks = []
			
			for category in self.categories:
				catlinks.append(
					'<li><a href="/browse/{0}">{0}</a></li>'.format(category))
				
			return page.format(
				categorylist = '<ul>{0}</ul>'.format(''.join(catlinks)))
				
				
		def getCatList(cat):
			catlist = []
			if cat in self.categories:
				rows = self.db._get_movie_count_for(cat)
				for row in rows:
					catid, name, count = row
					
					name_enc = name.encode('ascii', 'xmlcharrefreplace')
					
					catlist.append(
						'<li><a href="/browse/{0}:{1}">{2} ({3})</a></li>'.format(
							cat, catid, name_enc, count))
			return catlist
				
		
		def getMovieList(cat, value):
			movielist = []
			if cat in self.categories:
				rows = self.db._get_movies_by(cat, value, '')
				
				for row in rows:
					movieid = row[0]
					moviename = row[1].encode('ascii', 'xmlcharrefreplace')
					year = row[5]
					
					movielist.append(
						'''<li><a href="/detail/{0}">{1} ({2})</a> 
							[<a href="/stream/{0}">play</a>]</li>'''.format(
														movieid, moviename, year))
				
			return movielist
				
				
		def getBrowse(url):
			"/browse/geners:horror"
			
			url = urlparse.urlparse(url)
			
			path = url.path
			
			path = path.partition('/')[2]
			
			category = (path.partition('/')[2]).partition(':')
			catname = category[0]
			catvalue = category[2]
			
			if catvalue == '':
				page = getTemplate('web-list')
				catlist = getCatList(catname)
				
				return page.format(
					categorylist = '<ul>{0}</ul>'.format(''.join(catlist)))
			else:
				page = getTemplate('web-list')
				movielist = getMovieList(catname, catvalue)
				
				return page.format(
					categorylist = '<ul>{0}</ul>'.format(''.join(movielist)))
					
					
		def _list_to_str(value_list, seperator):
			result = []
			for row in value_list:
				rowid, value = row
				result.append(value.encode('ascii', 'xmlcharrefreplace'))
			return seperator.join(result)
					
			
		def getDetail(url):
			url = urlparse.urlparse(url)
			
			path = url.path
			
			movieid = path.partition('/detail/')[2]
			
			if movieid != '':
				movie = self.db.getMovie(movieid)
				
				if movie == None:
					return 'No Movie'
					
				(movieid, title, sort, timestamp, 
				image, released, runtime, rated, summary) = movie
					
				page = getTemplate('template')
				
				return page.format(
					title = title.encode('ascii', 'xmlcharrefreplace'), 
					image = '/posters/{0}'.format(image), 
					released = released, 
					runtime = runtime,
					rated = rated, 
					summary = summary.encode('ascii', 'xmlcharrefreplace'),
					genres = _list_to_str(self.db.getGenresByMovieId(movieid),u', '),
					actors = _list_to_str(self.db.getActorsByMovieId(movieid),u'<br>'),
					directors = _list_to_str(self.db.getDirectorsByMovieId(movieid),u'<br>'),
					tags = _list_to_str(self.db.getTagsByMovieId(movieid),u', '),
					files = "<ul><li>{0}</li></ul>".format(
						_list_to_str(self.db.getFilesByMovieId(movieid),u'</li><li>'))
					)
					
					
		def getPoster(url):
			url = urlparse.urlparse(url)
			
			path = url.path
			
			posterName = urllib.unquote(path.partition('/posters/')[2])
			
			try:
				f = open(os.path.join(self.postersPath, posterName), 'rb')
				poster = f.read()
				return poster
			except IOError:
				return ''
				
				
		def _generate_sout_string(index, index_url, dst):
			return (
			"sout="+
			"#transcode{"+
				"threads=2," +
				"fps=25," +
				"vcodec=h264," +
				"vb=256," +
				"width=400," +
				"venc=x264{" +
					"aud," +
					"profile=baseline," +
					"level=30," +
					"keyint=30," +
					"bframes=0," +
					"ref=1," +
					"nocabac"
				"},"
				"acodec=mp3,"
				"ab=96,"
				"audio-sync"
			"}" +
			":std{" +
				"access=livehttp{" +
					"seglen=10," +
					"index=" + index + ","
					"index-url=" + index_url + ","
				"}" +
				"mux=ts{use-key-frames}," +
				"dst=\"" + dst + "\"" +
			"}"
			)
				
				
		def startStream(url):
			if not self._is_valid_vlc():
				return "VLC version is too old, need at least VLC 1.2.0"
			
			url = urlparse.urlparse(url)
			
			path = url.path
			print path
			
			movieid = path.partition('/stream/')[2]
			
			print movieid
			
			files = self.db.getFilesByMovieId(movieid)
			
			absfiles = []
			
			for row in files:
				fileid, filename = row
				absfilename = os.path.join(self.libraryPath, filename)
				print absfilename
				if os.path.isfile(absfilename):
					absfiles.append(absfilename)
					
			if len(absfiles) == 0:
				return "Movie has no files"
				
			streamDir = os.path.join(self.streamCatchPath, movieid)
			
			try:
				if not os.path.isdir(streamDir):
					os.mkdir(streamDir)
			except OSError:
				return "Cannot access the stream catch location"
				
			sout = _generate_sout_string(
				index     = os.path.join(streamDir, 'stream.m3u8'),
				index_url = '/streamfiles/{0}/stream-########.ts'.format(movieid),
				dst       = os.path.join(streamDir, 'stream-########.ts'))
											
			self.media = self._vlc_instance.media_new('file://'+absfiles[0], sout)
			
			if self._vlc_player != None:
				self._vlc_player.stop()
				self._vlc_player.release()
				
			self._vlc_player = self._vlc_instance.media_player_new()
				
			self._vlc_player.set_media(self.media)
			
			self._vlc_player.play()
			
			page = getTemplate('web-player')
			
			movie = self.db.getMovie(movieid)
			(movieid, title, sort, timestamp, 
			image, released, runtime, rated, summary) = movie
			
			return page.format(
				movietitle=title,
				moviestream="/streamfiles/{0}/stream.m3u8".format(movieid)
				)
			
			
		def getStreamFile(url):
			url = urlparse.urlparse(url)
			
			path = url.path
			
			path = urllib.unquote(path.partition('/streamfiles/')[2])
			
			path = path.partition('/')
			
			movieid = path[0]
			filename = path[2]
			
			filepath = os.path.join(self.streamCatchPath, movieid)
			filepath = os.path.join(filepath, filename)
			
			try:
				f = open(filepath, 'rb')
				data = f.read()
				return data
			except IOError:
				return ''
			

			
		class MediaServerReqHandler(BaseHTTPRequestHandler):
			def _sendHtmlHead(self):
				self.send_response(200)
				self.send_header('Content-type','text/html')
				self.end_headers()
				
			def _sendDefaultHead(self):
				self.send_response(200)
				self.end_headers()
				
			def do_GET(self):
				if self.path == '/':
					self._sendHtmlHead()
					self.wfile.write(getHomeList())
					
				elif self.path.startswith('/browse/'):
					self._sendHtmlHead()
					self.wfile.write(getBrowse(self.path))

				elif self.path.startswith('/detail/'):
					self._sendHtmlHead()
					self.wfile.write(getDetail(self.path))
					
				elif self.path.startswith('/posters/'):
					poster = getPoster(self.path)
					if poster != '':
						self._sendDefaultHead()
						self.wfile.write(poster)
					else:
						self.send_error(404,'Poster Not Found: {0}'.format(self.path))
						
				elif self.path.startswith('/stream/'):
					streamPage = startStream(self.path)
					if streamPage != '':
						self._sendHtmlHead()
						self.wfile.write(streamPage)
					else:
						self.send_error(404,'Poster Not Found: {0}'.format(self.path))
						
				elif self.path.startswith('/streamfiles/'):
					filedata = ''
					count = 0
					while True:
						filedata = getStreamFile(self.path)
						if filedata == '':
							time.sleep(0.2)
							count += 1
						else:
							break
						if count == 10:
							break
							
					if filedata != '':
						self._sendDefaultHead()
						self.wfile.write(filedata)
					else:
						self._sendHtmlHead()
						self.send_error(404,'Stream not ready yet. hit refresh')
			
				else:
					self.send_error(404,'File Not Found: {0}'.format(self.path))
		
		self._httpd = HTTPServer(self._address, MediaServerReqHandler)
		
		print "Started"
		
		self._httpd.serve_forever()
		
		print "Stopping server..."
		
		self._httpd.socket.close()
		self.db.close()
		
		if self._vlc_player != None:
			self._vlc_player.stop()
			self._vlc_player.release()
			
		self._vlc_instance.release()
		
		self._stopped = True
		
		print "Stopped Cleanly"
		
		
	def start(self):
		self._started = True
		threading.Thread.start(self)
		
		
	def stop(self):
		if self._started == True:
			while self._httpd == None:
				time.sleep(0.1)
				
			self._httpd.shutdown()
