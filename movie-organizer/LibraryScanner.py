"""
	portable-movie-organizer
	------------------------
	
	Copyright (C) 2010 Ali Aafee
	
	This file is part of portable-movie-organizer.

	portable-movie-organizer is free software: you can redistribute it 
	and/or modify it under the terms of the GNU General Public License 
	as published by the Free Software Foundation, either version 3 of 
	the License, or (at your option) any later version.

	Foobar is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with portable-movie-organizer.  
	If not, see <http://www.gnu.org/licenses/>.
"""

import os
import os.path
import wx
import DbInterface
import MovieDataEditor
import ImdbAPI
import time
import thread


class LibraryScanner(wx.Dialog):
	def __init__(self, parent, libraryLocation, metadatadb, postersPath, title='Scan Library'):
		self.libraryLocation = libraryLocation
		self.postersPath = postersPath
		
		self.validFileTypes = ['.avi', '.mkv', '.mp4', '.m4v', '.vob', '.divx', '.mpg', '.dat']
		
		self.db = metadatadb
		
		self.title = title
		self._scanning = False
		self._added = 0 
		self._unrecognized = 0
		self._ignored = 0
		
		self._unrecognizedFiles = []
		
		self._closed = False
		
		self._init_ctrls(parent)
		
		
	def _init_ctrls(self, parent):
		wx.Dialog.__init__(self, name='MovieEditor', parent=parent,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
			title=self.title, size=wx.Size(-1,-1))
			
		self.Bind(wx.EVT_CLOSE, self.OnClose)
			
		self.lblStatus = wx.StaticText(self, label='Click Start to scan the library')
		
		self.lblDir = wx.StaticText(self, label='')
		
		self.lblFile = wx.StaticText(self, label='')
		
		self.lblCount = wx.StaticText(self, label='')
		
		self.lstAdded = wx.ListBox(self)
		
		self.btnStartStop = wx.Button(self, label='Start')
		self.btnStartStop.Bind(wx.EVT_BUTTON, self.OnStartStop)
		
		self.btnClose = wx.Button(self, label="Close")
		self.btnClose.Bind(wx.EVT_BUTTON, self.OnClose)
		
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.btnStartStop, 0, 5)
		hbox.Add(self.btnClose, 0, 5)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.lblStatus, 0, wx.ALL, 5)
		vbox.Add(self.lblDir, 0, wx.ALL, 5)
		vbox.Add(self.lblFile, 0, wx.ALL, 5)
		vbox.Add(self.lblCount, 0, wx.ALL, 5)
		vbox.Add(self.lstAdded, 1, wx.ALL|wx.EXPAND, 10)
		vbox.Add(hbox, 0, wx.ALIGN_CENTER, 5)
		
		self.SetSizer(vbox)
		self.Layout()
		
		
	def _start_scan(self):
		try:
			db = DbInterface.DbInterface(self.db._dbfile)
			
			self.db2 = db
			
			self._scan(self.libraryLocation, '')
			
			db.close()
			
			wx.CallAfter(self._done_scan)
			
		except wx._core.PyDeadObjectError, e:
			db.close()
			
			print "Window destroyed uncleanly"
			print e
		
		
	def _scan(self, dir_name, short_dir_name):
		files = []
		fs = os.listdir(dir_name)
		for f in fs:
			fileName = os.path.join(dir_name, f)
			if os.path.isdir(fileName):
				if f != 'metadata':
					shortFileName = os.path.join(short_dir_name, f)
					f2s = self._scan(fileName, shortFileName)
					for f2 in f2s:
						files.append(f2)
			else:
				self._status(
					dirname=short_dir_name + os.path.sep,
					filename=f)

				if self._is_valid_file_type(f):
					shortFileName = os.path.join(short_dir_name, f)
					fileid = self.db2.getFileId(shortFileName)
					if fileid == None:
						self._add_movie(shortFileName)
						files.append(shortFileName)
					else:
						print u"file: '{0}' exists in library".format(shortFileName)
						if not self.db2.fileIsLinked(fileid):
							print "      and is not linked to a movie, so added"
							self._add_movie(shortFileName)
							files.append(shortFileName)
						else:
							print "      and is linked to a movie, so ignored"
							self._count(ignored=1)
							
			if self._scanning == False:
				return [] 
							
		return files
		
		
	def _add_movie(self, shortFileName):
		title, year = self._get_title_and_year_from_filename(shortFileName)
		
		if title != '':
			metadata = ImdbAPI.GetMetadata(title, year, self.postersPath)
		
			if metadata != None:
				if metadata['title'] != '':
					movieid = self.db2.addMovie(
						metadata['title'],
						'',
						metadata['image'],
						metadata['released'],
						metadata['runtime'],
						metadata['rated'],
						metadata['summary'],
						self._todblist(metadata['genres']), 
						self._todblist(metadata['actors']), 
						self._todblist(metadata['directors']),
						self._todblist([shortFileName,]))
					
					print "Added movie {0} - '{1}'".format(movieid, metadata['title'])
					
					text = u'{0}({1})'.format(metadata['title'], metadata['released'])
					
					self._count(added=1)
					wx.CallAfter(self.lstAdded.Insert, text, 0)
					
					time.sleep(1)
				else:
					print "Cannot get metadata. Skipping"
					self._count(unrecognized=1)
					self._unrecognizedFiles.append(shortFileName)
			else:
				print "Cannot get metadata. Skipping"
				self._count(unrecognized=1)
				self._unrecognizedFiles.append(shortFileName)
		else:
			print "Cannot extract title from filename"
			self._count(unrecognized=1)
			self._unrecognizedFiles.append(shortFileName)
		
		
	def _status(self, filename='', dirname=''):
		if dirname != '':
			wx.CallAfter(self.lblDir.SetLabel, dirname)
		if filename != '':
			wx.CallAfter(self.lblFile.SetLabel, filename)
		
		
	def _count(self, added=0, unrecognized=0, ignored=0):
		self._added += added
		self._unrecognized += unrecognized
		self._ignored += ignored
		
		wx.CallAfter(self.lblCount.SetLabel,
			'{0} Added, {1} Unrecognized, {2} Ignored'.format(
				self._added,
				self._unrecognized,
				self._ignored))
		
		
	def _done_scan(self):
		self._scanning = False
		self.btnStartStop.SetLabel("Start")
		self.btnStartStop.Enable(True)
		self.lblStatus.SetLabel("Finished scanning the library")
		self.lblDir.SetLabel('')
		self.lblFile.SetLabel('')
		
		if self._closed == True:
			self.EndModal(wx.OK)
		
		
	def OnStartStop(self, events):
		if self._scanning == False:
			self._scanning = True
			self.btnStartStop.SetLabel("Stop")
			self.lblStatus.SetLabel("Scanning...")
			self.lstAdded.Clear()
			self._unrecognizedFiles = []
			thread.start_new_thread(self._start_scan, ())
		else:
			self._scanning = False
			#self.btnStartStop.SetLabel("Stopping...")
			self.lblStatus.SetLabel("Stopping...")
			self.btnStartStop.Enable(False)
			
			
	def OnClose(self, event):
		if self._closed == False:
			if self._scanning == False:
				print "A"
				self.EndModal(wx.OK)
			else:
				print "B"
				self._scanning = False
				self._closed = True
				#self.btnStartStop.SetLabel("Stopping...")
				self.lblStatus.SetLabel("Closing...")
				self.btnStartStop.Enable(False)
			
			
	def GetUnrecognizedFiles():
		return self._unrecognizedFiles


	def _is_valid_file_type(self, file_name):
		file_name = file_name.lower()
		(shortname, extension) = os.path.splitext(file_name)

		if extension in self.validFileTypes:
			return True
		else:
			return False
				
			
	def _get_bracketed(self, text, bracketO, bracketC):
		values = text.split(bracketO)
		result = []
		if len(values)>0:
			del(values[0])
			for value in values:
				value = value.partition(bracketC)[0]
				result.append(value)
		
		return result
		
		
	def _is_valid_year(self, year):
		if len(year) == 4:
				try:
					year = int(year)
					if year > 1000 and year < 9999:
						return True
				except ValueError:
					pass
	
			
	def _get_year_from_title(self, title):
		results = []
		if '[' in title:
			lst = self._get_bracketed(title,'[',']')
			for item in lst:
				if self._is_valid_year(item):
					return (item, u'[{0}]'.format(item))
		if '(' in title:
			lst = self._get_bracketed(title,'(',')')
			for item in lst:
				if self._is_valid_year(item):
					return (item, u'({0})'.format(item))
		if '{' in title:
			lst = self._get_bracketed(title,'{','}')
			for item in lst:
				if self._is_valid_year(item):
					return (item, u'{'+item+u'}')
			
		return ('','')
		
		
	def _get_last_four_digit_num(self, string):
		for i in xrange(len(string)-4,0,-1):
			year = string[i:i+4]
			if self._is_valid_year(year):
				return year
		return ''
		
	
	def _clean_up_moviename(self, moviename):
		cut = 'DvDrip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'DVDRIP'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'DVDrip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'DvDRip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'DVDRip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = '[DVDRip]'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'DvDrip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		cut = 'BRRip'
		if cut in moviename:
			moviename = moviename.partition(cut)[0]
			
		return moviename
		
		
	def _get_title_and_year_from_filename(self, filename):
		filepath, filename = os.path.split(filename)
		shortname, extension = os.path.splitext(filename)
		moviename = shortname.replace("."," ")
		year, torem = self._get_year_from_title(moviename)
		if year == '':
			year = self._get_last_four_digit_num(moviename)
			torem = year	
		if torem != '':
			moviename = moviename.replace(torem,' ')
		moviename = moviename.strip()
		moviename = self._clean_up_moviename(moviename)
		return (moviename, year)
		
	
	def _todblist(self, values):
		result = []
		for value in values:
			rowid = 0
			state = 'normal'
			result.append((rowid, value, state))
		return result
	
