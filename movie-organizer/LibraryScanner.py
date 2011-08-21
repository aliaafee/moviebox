#
#	portable-movie-organizer
#	
#	Copyright (c) 2010 Ali Aafee
#	
#	This file is part of portable-movie-organizer.
#
#	portable-movie-organizer is free software: you can redistribute it 
#	and/or modify it under the terms of the GNU General Public License 
#	as published by the Free Software Foundation, either version 3 of 
#	the License, or (at your option) any later version.
#
#	portable-movie-organizer is distributed in the hope that it will 
#	be useful, but WITHOUT ANY WARRANTY; without even the implied 
#	warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
#	See the GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with portable-movie-organizer.  
#	If not, see <http://www.gnu.org/licenses/>.

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
		
		self._autoAdd = True
		
		self._scanning = False
		
		self._found = 0
		self._new = 0
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
		
		self.chkAutoAdd = wx.CheckBox(self, label="Auto Add Files to library")
		self.chkAutoAdd.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.OnToggleAutoAdd, self.chkAutoAdd)
			
		self.lblStatus = wx.StaticText(self, label='Click "Scan" to scan the library')
		
		self.lblDir = wx.StaticText(self, label='')
		self.lblDir.Show(False)
		
		self.lblFile = wx.StaticText(self, label='')
		self.lblFile.Show(False)
		
		self.lblCount = wx.StaticText(self, label='')
		
		#this displayed when autoadd is enabled
		self.autoAddDisp = wx.Notebook(self, style=wx.BK_DEFAULT)
		
		self.lstAdded = wx.ListBox(self.autoAddDisp)
		
		self.autoAddDisp.AddPage(self.lstAdded, "Added")
		
		self.pnlUnrecognized = wx.Panel(self.autoAddDisp)
		
		self.lstUnrecognized = wx.ListCtrl(self.pnlUnrecognized, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.lstUnrecognized.InsertColumn(0,'Files', width=300)
		
		self.addUnrecognizedNew = wx.Button(self.pnlUnrecognized, 
			label="Add to new movie")
		self.addUnrecognizedNew.Bind(wx.EVT_BUTTON, self.OnAddUnrecNew)
		
		self.addUnrecognizedExisting = wx.Button(self.pnlUnrecognized,
			label="Add to existing movie")
		self.addUnrecognizedExisting.Bind(wx.EVT_BUTTON, self.OnAddUnrecExist)
		self.addUnrecognizedExisting.Show(False) #this hidden for now
		
		ubox = wx.BoxSizer(wx.VERTICAL)
		ubox.Add(self.lstUnrecognized, 1, wx.ALL|wx.EXPAND, 3)
		ubox.Add(self.addUnrecognizedNew, 0, wx.ALL, 3)
		ubox.Add(self.addUnrecognizedExisting, 0, wx.ALL, 3)
		self.pnlUnrecognized.SetSizer(ubox)
		self.pnlUnrecognized.Layout()
		
		self.autoAddDisp.AddPage(self.pnlUnrecognized, "Unrecognized")
		
		#this displayed when autoadd is disabled
		self.noAutoDisp = wx.Panel(self, style=wx.RAISED_BORDER)
		
		self.lstFound = wx.ListCtrl(self.noAutoDisp, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.lstFound.InsertColumn(0,'Files', width=300)
		
		self.addNew = wx.Button(self.noAutoDisp, 
			label="Add to new movie")
		self.addNew.Bind(wx.EVT_BUTTON, self.OnAddNew)
		
		self.addExisting = wx.Button(self.noAutoDisp,
			label="Add to existing movie")
		self.addExisting.Bind(wx.EVT_BUTTON, self.OnAddExisting)
		self.addExisting.Show(False) #this hidden for now
		
		nbox = wx.BoxSizer(wx.VERTICAL)
		nbox.Add(self.lstFound, 1, wx.ALL|wx.EXPAND, 3)
		nbox.Add(self.addNew, 0, wx.ALL, 3)
		nbox.Add(self.addExisting, 0, wx.ALL, 3)
		self.noAutoDisp.SetSizer(nbox)
		self.noAutoDisp.Layout()
		
		self.noAutoDisp.Show(False)
		
		#start/stop and close
		self.btnStartStop = wx.Button(self, label='Scan')
		self.btnStartStop.Bind(wx.EVT_BUTTON, self.OnStartStop)
		
		self.btnClose = wx.Button(self, label="Close")
		self.btnClose.Bind(wx.EVT_BUTTON, self.OnClose)
		
		#layout
		sbox = wx.BoxSizer(wx.VERTICAL)
		sbox.Add(self.lblStatus, 0, wx.ALL, 3)
		sbox.Add(self.lblCount, 0, wx.ALL, 3)
		sbox.Add(self.lblDir, 0, wx.ALL, 3)
		sbox.Add(self.lblFile, 0, wx.ALL, 3)
		
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.btnStartStop, 0, 5)
		hbox.Add(self.btnClose, 0, 5)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.chkAutoAdd,0, wx.ALL, 5)
		vbox.Add(sbox, 0, wx.ALL, 5)
		vbox.Add(self.autoAddDisp, 1, wx.ALL|wx.EXPAND, 10)
		vbox.Add(self.noAutoDisp, 1, wx.ALL|wx.EXPAND, 10)
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
					self._count(found=1)
					if fileid == None:
						self._add_movie(shortFileName)
						files.append(shortFileName)
					else:
						#print u"file: '{0}' exists in library".format(shortFileName)
						if not self.db2.fileIsLinked(fileid):
							#print "      and is not linked to a movie, so added"
							self._add_movie(shortFileName)
							files.append(shortFileName)
						else:
							#print "      and is linked to a movie, so ignored"
							self._count(ignored=1)
							
			if self._scanning == False:
				return [] 
							
		return files
		
		
	def _add_movie(self, shortFileName):
		self._count(new=1)
		
		if not self._autoAdd:
			wx.CallAfter(self.lstFound.Append, (shortFileName,))
			return
			
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
					self._add_unrecognized(shortFileName)
			else:
				print "Cannot get metadata. Skipping"
				self._add_unrecognized(shortFileName)
		else:
			print "Cannot extract title from filename"
			self._add_unrecognized(shortFileName)
			
			
	def _add_unrecognized(self, shortFileName):
		self._count(unrecognized=1)
		
		self._unrecognizedFiles.append(shortFileName)
		
		wx.CallAfter(self.lstUnrecognized.Append, (shortFileName,))
		
		
	def _status(self, filename='', dirname=''):
		if dirname != '':
			wx.CallAfter(self.lblDir.SetLabel, dirname)
		if filename != '':
			wx.CallAfter(self.lblFile.SetLabel, filename)
		
		
	def _count_reset(self):
		self._found = 0
		self._new = 0
		self._added = 0
		self._unrecognized = 0
		self._ignored = 0
		
		
	def _count(self, found=0, new=0, added=0, unrecognized=0, ignored=0):
		self._found += found
		self._new += new
		self._added += added
		self._unrecognized += unrecognized
		self._ignored += ignored
		
		status = []
		
		status.append('{0} Found'.format(self._found))
		status.append('{0} New'.format(self._new))
		
		if self._added > 0:
			status.append('{0} Added'.format(self._added))
		if self._unrecognized > 0:
			status.append('{0} Unrecognized'.format(self._unrecognized))
		if self._ignored > 0:
			status.append('{0} Ignored'.format(self._ignored))
			
		
		wx.CallAfter(self.lblCount.SetLabel, ", ".join(status))
		
		
	def _done_scan(self):
		self._scanning = False
		self.btnStartStop.SetLabel("Start")
		self.btnStartStop.Enable(True)
		self.chkAutoAdd.Enable(True)
		self.addNew.Enable(True)
		self.addExisting.Enable(True)
		self.addUnrecognizedNew.Enable(True)
		self.addUnrecognizedExisting.Enable(True)
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
			self.lblDir.SetLabel('')
			self.lblFile.SetLabel('')
			self.lblCount.SetLabel('')
			self.chkAutoAdd.Enable(False)
			self.addNew.Enable(False)
			self.addExisting.Enable(False)
			self.addUnrecognizedNew.Enable(False)
			self.addUnrecognizedExisting.Enable(False)
			self._count_reset()
			self.lstAdded.Clear()
			self.lstUnrecognized.DeleteAllItems()
			self.lstFound.DeleteAllItems()
			self._unrecognizedFiles = []
			thread.start_new_thread(self._start_scan, ())
		else:
			self._scanning = False
			#self.btnStartStop.SetLabel("Stopping...")
			self.lblStatus.SetLabel("Stopping...")
			self.btnStartStop.Enable(False)


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
					nowyear = time.localtime(time.time())[0]
					if year > 1900 and year <= nowyear:
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
		
	
	def _trunkate_after(self, haystack, needle):
		upper = haystack.upper()
		index = upper.find(needle.upper())
	
		if index == -1:
			return haystack
		else:
			return haystack[0:index]
		
	
	def _clean_up_moviename(self, moviename):
		moviename = self._trunkate_after(moviename,'[eng]')
		moviename = self._trunkate_after(moviename,'(dvdrip)')
		moviename = self._trunkate_after(moviename,'[dvdrip]')
		moviename = self._trunkate_after(moviename,'dvdrip')
		moviename = self._trunkate_after(moviename,'brrip')
		moviename = self._trunkate_after(moviename,'ts-scr')
		moviename = self._trunkate_after(moviename,'x264')
		moviename = moviename.replace("."," ")
		moviename = moviename.replace("_"," ")
		
		return moviename.strip()
		
		
	def _get_title_and_year_from_filename(self, filename):
		filepath, filename = os.path.split(filename)
		shortname, extension = os.path.splitext(filename)
		moviename = shortname
		year, torem = self._get_year_from_title(moviename)
		if year == '':
			year = self._get_last_four_digit_num(moviename)
			torem = year	
		if torem != '':
			moviename = self._trunkate_after(moviename, torem)#moviename.replace(torem,' ')
		moviename = self._clean_up_moviename(moviename)
		return (moviename, year)
		
	
	def _todblist(self, values):
		result = []
		for value in values:
			rowid = 0
			state = 'normal'
			result.append((rowid, value, state))
		return result
		
		
	def OnToggleAutoAdd(self, event):
		self._autoAdd = event.IsChecked()
		if self._autoAdd:
			self.autoAddDisp.Show(True)
			self.noAutoDisp.Show(False)
			self.Layout()
		else:
			self.autoAddDisp.Show(False)
			self.noAutoDisp.Show(True)
			self.Layout()
			
			
	def _get_selection(self, fileList):
		selection = []
		
		if fileList.GetSelectedItemCount() == 0:
			return selection
			
		selectedItem = fileList.GetFirstSelected()
		while selectedItem != -1:
			selection.append((0, fileList.GetItemText(selectedItem)))
			selectedItem = fileList.GetNextSelected(selectedItem)
			
		return selection
		
		
	def _delete_selection(self, fileList):
		if fileList.GetSelectedItemCount() == 0:
			return
			
		selectedItem = fileList.GetFirstSelected()
		while selectedItem != -1:
			fileList.DeleteItem(selectedItem)
			selectedItem = fileList.GetNextSelected(-1)
			
			
	def _add_selected(self, fileList):
		selectedFiles = self._get_selection(fileList)
		
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
					
					self._delete_selection(fileList)
				else:
					msg = wx.MessageDialog(self, 
						'No title set so movie not added', 
						'Error Adding Movie to Library', wx.OK|wx.ICON_INFORMATION)
					msg.ShowModal()
					msg.Destroy()
		
			dlg.Destroy()
			
			
	def _add_to_existing(self, fileList):
		selectedFiles = self._get_selection(fileList)
		
		if len(selectedFiles) > 0:
			dlg = wx.MessageDialog(self, 
				'Feature not implemented yet', 
				'Sorry', wx.OK|wx.ICON_INFORMATION)
			
			dlg.ShowModal()
			
			dlg.Destroy()
			
			
	def OnAddUnrecNew(self, event):
		self._add_selected(self.lstUnrecognized)
		
	
	def OnAddUnrecExist(self, event):
		self._add_to_existing(self.lstUnrecognized)
		
		
	def OnAddNew(self, event):
		self._add_selected(self.lstFound)
	
	def OnAddExisting(self, event):
		self._add_to_existing(self.lstFound)
		
			
	def OnClose(self, event):
		if self._closed == False:
			if self._scanning == False:
				self.EndModal(wx.OK)
			else:
				self._scanning = False
				self._closed = True
				#self.btnStartStop.SetLabel("Stopping...")
				self.lblStatus.SetLabel("Closing...")
				self.btnStartStop.Enable(False)
	
