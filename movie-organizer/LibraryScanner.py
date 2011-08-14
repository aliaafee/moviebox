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
	along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import os.path
import wx
import DbInterface
import MovieDataEditor

class LibraryScanner(wx.Dialog):
	def __init__(self, parent, libraryLocation, metadatadb, postersPath, title='Scan Library'):
		self.libraryLocation = libraryLocation
		self.postersPath = postersPath
		
		self.validFileTypes = ['.avi', '.mkv', '.mp4', '.m4v', '.vob', '.divx', '.mpg', '.dat']
		
		self.db = metadatadb
		
		self.title = title
		
		self._init_ctrls(parent)
		
		
	def _init_ctrls(self, parent):
		wx.Dialog.__init__(self, name='MovieEditor', parent=parent,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
			title=self.title, size=wx.Size(-1,-1))
			
		vbox = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(vbox)
		
		self.btnScan = wx.Button(self, label='Scan')
		self.btnScan.Bind(wx.EVT_BUTTON, self.OnScan)
		vbox.Add(self.btnScan, 0, wx.EXPAND)
		
		self.fileList = wx.ListCtrl(self, style=wx.LC_REPORT)
		self.fileList.InsertColumn(0,'Files', width=300)
		vbox.Add(self.fileList, 1, wx.EXPAND, 10)
		
		self.btnAddNew = wx.Button(self, label='Add Selection to New Movie')
		self.btnAddNew.Bind(wx.EVT_BUTTON, self.OnAddNew)
		vbox.Add(self.btnAddNew, 0, wx.EXPAND)
		
		self.btnAddExisting = wx.Button(self, label='Add Selection to Existing Movie')
		self.btnAddExisting.Bind(wx.EVT_BUTTON, self.OnAddExisting)
		vbox.Add(self.btnAddExisting, 0, wx.EXPAND)
		
		self.btnAddAll = wx.Button(self, label='Add All to New Movies')
		self.btnAddAll.Bind(wx.EVT_BUTTON, self.OnAddAll)
		vbox.Add(self.btnAddAll, 0, wx.EXPAND)
		

	def _is_valid_file_type(self, file_name):
		file_name = file_name.lower()
		(shortname, extension) = os.path.splitext(file_name)

		if extension in self.validFileTypes:
			return True
		else:
			return False
		

	def _get_files(self, dir_name, short_dir_name):
		files = []
		fs = os.listdir(dir_name)
		for f in fs:
			fileName = os.path.join(dir_name, f)
			if os.path.isdir(fileName):
				if f != 'metadata':
					shortFileName = os.path.join(short_dir_name, f)
					f2s = self._get_files(fileName, shortFileName)
					for f2 in f2s:
						files.append(f2)
			else:
				if self._is_valid_file_type(f):
					shortFileName = os.path.join(short_dir_name, f)
					fileid = self.db.getFileId(shortFileName)
					if fileid == None:
						files.append(shortFileName)
					else:
						print u"file: '{0}' exists in library".format(shortFileName)
						if not self.db.fileIsLinked(fileid):
							print "      and is not linked to a movie, so added"
							files.append(shortFileName)
						else:
							print "      and is linked to a movie, so ignored" 
							
		return files
		
		
	def _get_selection(self):
		selection = []
		
		if self.fileList.GetSelectedItemCount() == 0:
			return selection
			
		selectedItem = self.fileList.GetNextSelected(-1)
		while selectedItem != -1:
			selection.append(self.fileList.GetItemText(selectedItem))
			selectedItem = self.fileList.GetNextSelected(selectedItem)
			
		return selection
		
		
	def _delete_selection(self):
		if self.fileList.GetSelectedItemCount() == 0:
			return
			
		selectedItem = self.fileList.GetNextSelected(-1)
		while selectedItem != -1:
			self.fileList.DeleteItem(selectedItem)
			selectedItem = self.fileList.GetNextSelected(-1)
		
	
	def _get_selection_for_moviedataeditor(self):
		selection = self._get_selection()
		result = []
		for item in selection:
			result.append((0, item))
		return result
			
			
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
		
		
	def OnScan(self, event):
		fs = self._get_files(self.libraryLocation,'')
		self.fileList.DeleteAllItems()
		for f in fs:
			self.fileList.Append((f,))
		
		
	def OnAddNew(self, event):
		selectedFiles = self._get_selection_for_moviedataeditor()
		if len(selectedFiles) > 0:
			dlg = MovieDataEditor.MovieDataEditor(self, self.postersPath, 'Add Movie to Library')
			data = {}
			
			title, year = self._get_title_and_year_from_filename(selectedFiles[0][1])
			
			data['title'] = title
			data['sort'] = ''
			data['image'] = ''
			data['released'] = year
			data['runtime'] = ''
			data['rated'] = ''
			data['summary'] = ''
			data['genres'] = []
			data['actors'] = []
			data['directors'] = []
			data['files'] = selectedFiles
			
			dlg.SetData(data)
			
			result = dlg.ShowModal()
			if result == wx.ID_OK:
				data = dlg.GetData()
				if data['title'] != '':
					movieid = self.db.addMovie(data['title'],
						data['sort'],data['image'],data['released'],
						data['runtime'],data['rated'],data['summary'],
						data['genres'], data['actors'], data['directors'],
						data['files'])
				
					print "movie added"
					
					self._delete_selection()
				else:
					msg = wx.MessageDialog(self, 
						'No title set so movie not added', 
						'Error Adding Movie to Library', wx.OK|wx.ICON_INFORMATION)
					msg.ShowModal()
					msg.Destroy()
		
			dlg.Destroy()
			
			
	def OnAddExisting(self, event):
		pass
		
	
	def OnAddAll(self, event):
		for index in range(0,self.fileList.GetItemCount()):
			filename = self.fileList.GetItemText(index)
			data = {}
			
			title, year = self._get_title_and_year_from_filename(filename)
			
			data['title'] = title
			data['sort'] = ''
			data['image'] = ''
			data['released'] = year
			data['runtime'] = ''
			data['rated'] = ''
			data['summary'] = ''
			data['genres'] = []
			data['actors'] = []
			data['directors'] = []
			data['files'] = [(0,filename,'normal')]
			
			movieid = self.db.addMovie(
				data['title'],
				released=data['released'],
				files=data['files'])
			
		
	
