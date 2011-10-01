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

import wx
import wx.grid
import wx.html

import os
import os.path
import subprocess
import sys
import thread
import time

import vlc

from DbInterface import *
import MovieDataEditor
import LibraryScanner

dirName = os.path.dirname(os.path.abspath(__file__))
dirName, fileName = os.path.split(dirName)
resDir = os.path.join(dirName, 'res')
licensePath = os.path.join(dirName, 'license.txt')


def create(parent, library, player=''):
    return MainFrame(parent, library, player)
    

class MainFrame(wx.Frame):
	def __init__(self, parent, library, player=''):
		self.libraryPath = library
		self.VlcPlayer = player
		
		self.selectedMovie = None
		
		self.filterName = None
		self.filterValue = None
		
		self.rightClickedMovie = None
		
		f = open(os.path.join(resDir,'template.html'))
		self.detailHtmlTemplate = unicode(f.read())
		f.close()
		
		self.movieTitleSearch = ''
				
		
		self._init_ctrls(parent)
		
		
	def _init_db(self):
		if self.libraryPath == '':
			print "No library path set"
			return False
			
		try:
			if os.path.isdir(self.libraryPath):
				self.metadataPath = os.path.join(self.libraryPath,'metadata')
				if not os.path.isdir(self.metadataPath):
					os.mkdir(self.metadataPath)
				
				self.postersPath = os.path.join(self.metadataPath, 'posters')
				if not os.path.isdir(self.postersPath):
					os.mkdir(self.postersPath)
					
				self.catchPath = os.path.join(self.metadataPath, 'catch')
				if not os.path.isdir(self.catchPath):
					os.mkdir(self.catchPath)
				
				self.db = DbInterface(os.path.join(self.metadataPath,'metadata.db'))
				
				if not self.db.isConnected():
					print "Cannot connect to the metadata database"
					return False

				print "Library Opened"
				return True
				
			else:
				print "Library path is invalid"
				return False
				
		except OSError, e:
			print "Cannot access the library"
			return False

			
	def _init_ctrls(self, parent):
		wx.Frame.__init__(self, name='MovieOrganizer', parent=parent,
			style=wx.DEFAULT_FRAME_STYLE,
			title='Movie Organizer')
		self.SetClientSize(wx.Size(640,480))
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		
		self._init_menus()
		
		self.statusBar = self.CreateStatusBar()
		
		#the main splitter window
		self.splitBase = wx.SplitterWindow(self, style=wx.SP_NOBORDER)
		
		#Create the treectrl for the filters
		self.filterPanel = wx.Panel(self.splitBase)
		self.movieFilter = wx.TreeCtrl(self.filterPanel, style=wx.TR_DEFAULT_STYLE | wx.SUNKEN_BORDER)
		self._init_filter()
		self.movieFilter.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnMovieFilterSelChanged)
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.movieFilter, 1, wx.EXPAND | wx.ALL, 1)
		self.filterPanel.SetSizer(vbox)
		self.filterPanel.Layout()
		
		#the right hand window of the main splitter
		self.splitRight = wx.SplitterWindow(self.splitBase, style=wx.SP_NOBORDER)
		
		self.splitBase.SplitVertically(self.filterPanel, self.splitRight)
		self.splitBase.SetSashPosition(160)
		
		#panel to hold the movielist and its toolbar
		self.movieListPanel = wx.Panel(self.splitRight)
		
		self.searchBox = wx.SearchCtrl(self.movieListPanel, size=(200,-1), style=wx.TE_PROCESS_ENTER)
		self.searchBox.ShowSearchButton(False)
		self.Bind(wx.EVT_TEXT, self.OnMovieListTbSearch, self.searchBox)
		
		#the list of movies
		self.movieList = wx.ListView(self.movieListPanel, size=wx.Size(210,-1), style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		self.movieList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnMovieListSelected)
		self.movieList.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnMovieListRightClick)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.searchBox, 0, wx.ALL | wx.EXPAND, 1)
		vbox.Add(self.movieList, 1, wx.EXPAND | wx.ALL, 1)
		self.movieListPanel.SetSizer(vbox)
		self.movieListPanel.Layout()
		
		#panel to display movie details
		self.movieDetail = wx.Panel(self.splitRight)
		
		self.movieDetailTb = self._create_movie_detail_tb(self.movieDetail)
		
		#htmlwindow showing movie details
		self.movieDetailHtml = wx.html.HtmlWindow(self.movieDetail, style=wx.SUNKEN_BORDER)
		
		#the player window
		self.player = wx.Panel(self.movieDetail)
		
		self.videopanel = wx.Panel(self.player)
		self.videopanel.SetBackgroundColour(wx.BLACK)
		
		#self.playerctrlpanel = wx.Panel(self.player, -1 )
		
		#self.btnPlay = wx.Button(self.playerctrlpanel, label="Play")
		#self.btnPause = wx.Button(self.playerctrlpanel, label="Pause")
		#self.btnStop = wx.Button(self.playerctrlpanel, label="Stop")
		
		#hbox = wx.BoxSizer(wx.HORIZONTAL)
		#hbox.Add(self.btnPlay, flag=wx.RIGHT, border=5)
		#hbox.Add(self.btnPause)
		#hbox.Add(self.btnStop)
		#self.playerctrlpanel.SetSizer(hbox)
		
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.videopanel, 1, wx.EXPAND | wx.ALL, 1)
		#vbox.Add(self.playerctrlpanel, 0, wx.EXPAND | wx.ALL, 0)
		self.player.SetSizer(vbox)
		
		self.player.Show(False)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.movieDetailTb, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 0 )
		vbox.Add(self.movieDetailHtml, 1, wx.EXPAND | wx.ALL, 1)
		vbox.Add(self.player, 1, wx.EXPAND | wx.ALL, 1)
		
		self.movieDetail.SetSizer(vbox)
		self.movieDetail.Layout()
		
		self.splitRight.SplitVertically(self.movieListPanel, self.movieDetail)
		self.splitRight.SetSashPosition(210)
		
		self._init_vlc()
		self._init_movielist()
		self._display_details()
		
		
	def _init_vlc(self):
		self.Instance = vlc.Instance()
		self.VlcPlayer = self.Instance.media_player_new()
		
		
	def _init_menus(self):
		menuBar = wx.MenuBar()
		
		menu = wx.Menu()
		
		m_add = wx.NewId()
		menu.Append(
			kind=wx.ITEM_NORMAL, 
			text="Add Movie", 
			help="Add a new movie to the library",
			id=m_add)
		self.Bind(wx.EVT_MENU, self.OnAddMovie, id=m_add)
		
		m_scan = wx.NewId()
		menu.Append(
			kind=wx.ITEM_NORMAL, 
			text="Scan Library", 
			help="Scan library for new files",
			id=m_scan)
		self.Bind(wx.EVT_MENU, self.OnScanLibrary, id=m_scan)
		
		menu.AppendSeparator()
		
		m_exit = wx.NewId()
		menu.Append(
			kind=wx.ID_EXIT, 
			text="E&xit\tAlt-X", 
			help="Exit Movie Organizer",
			id=m_exit)
		self.Bind(wx.EVT_MENU, self.OnClose, id=m_exit)
		
		menuBar.Append(menu, "&File")
		
		menu = wx.Menu()
		
		m_about = wx.NewId()
		menu.Append(
			kind=wx.ITEM_NORMAL, 
			text="About", 
			help="About movie organizer",
			id=m_about)
		self.Bind(wx.EVT_MENU, self.OnAbout, id=m_about)
		
		menuBar.Append(menu, "&Help")
		
		self.SetMenuBar(menuBar)
		
		
	def _create_movie_detail_tb(self, parent):
		tb = wx.ToolBar(parent, style=wx.TB_TEXT|wx.TB_NODIVIDER|wx.TB_HORIZONTAL|wx.TB_FLAT)
		tb.SetToolBitmapSize((21, 21))
		
		tb_add = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'add.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_NEW),
			bmpDisabled=wx.NullBitmap, 
			id=tb_add,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Add a new movie to the library')
		self.Bind(wx.EVT_TOOL, self.OnAddMovie,
			id=tb_add)
			
		tb_scan = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'scan.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN),
			bmpDisabled=wx.NullBitmap, 
			id=tb_scan,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Scan library for new files')
		self.Bind(wx.EVT_TOOL, self.OnScanLibrary,
			id=tb_scan)	
		
		tb.AddSeparator()
		
		tb_edit = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'edit.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW),
			bmpDisabled=wx.NullBitmap, 
			id=tb_edit,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Edit Movie Metadata')
		self.Bind(wx.EVT_TOOL, self.OnEditMetadata,
			id=tb_edit)
			
		tb.AddSeparator()
			
		tb_add_tag = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'tag_add.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK),
			bmpDisabled=wx.NullBitmap, 
			id=tb_add_tag,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Add a Tag to the Movie')
		self.Bind(wx.EVT_TOOL, self.OnAddTag,
			id=tb_add_tag)
			
		tb_remove_tag = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'tag_remove.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_DEL_BOOKMARK),
			bmpDisabled=wx.NullBitmap, 
			id=tb_remove_tag,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Remove tag from movie')
		self.Bind(wx.EVT_TOOL, self.OnRemoveTag,
			id=tb_remove_tag)
			
		if self.VlcPlayer != '':
			tb.AddSeparator()
			
			tb_play = wx.NewId()
			tb.DoAddTool(
				bitmap=wx.Bitmap(os.path.join(resDir,'play.png'), wx.BITMAP_TYPE_PNG),
		                    #bitmap=wx.ArtProvider.GetBitmap(wx.ART_DEL_BOOKMARK),
				bmpDisabled=wx.NullBitmap, 
				id=tb_play,
				kind=wx.ITEM_NORMAL, 
				label='', 
				longHelp='', 
				shortHelp='Play movie using default external player')
			self.Bind(wx.EVT_TOOL, self.OnPlayMovie,
				id=tb_play)
		else:
			tb.AddSeparator()
			
			tb_play = wx.NewId()
			tb.DoAddTool(
				bitmap=wx.Bitmap(os.path.join(resDir,'play.png'), wx.BITMAP_TYPE_PNG),
		                    #bitmap=wx.ArtProvider.GetBitmap(wx.ART_DEL_BOOKMARK),
				bmpDisabled=wx.NullBitmap, 
				id=tb_play,
				kind=wx.ITEM_NORMAL, 
				label='', 
				longHelp='', 
				shortHelp='Play movie with inbuilt player')
			self.Bind(wx.EVT_TOOL, self.OnPlayMovieInbuilt,
				id=tb_play)
				
		tb.Realize()
		
		return tb
		
		
	def _add_filter_group(self,root, groupname, rows):
		filterGroup = self.movieFilter.AppendItem(root, groupname)
		for row in rows:
			rowid, name, count = row
			itemText = name + u" ({0})".format(count)
			self.movieFilter.AppendItem(filterGroup, itemText,
				data=wx.TreeItemData((groupname, rowid)))
		return filterGroup
		
		
	def _add_items_to_filter_group(self, filterGroup, rows):
		groupname = self.movieFilter.GetItemText(filterGroup)
		for row in rows:
			rowid, name, count = row
			itemText = name + u" ({0})".format(count)
			self.movieFilter.AppendItem(filterGroup, itemText,
				data=wx.TreeItemData((groupname, rowid)))
			
		
	def _init_filter(self):
		self.movieFilter.DeleteAllItems()
		
		self.rootFilters = self.movieFilter.AddRoot('My Movie Collection')
		
		self.filterAll = self.movieFilter.AppendItem(self.rootFilters,'All Movies')
		
		self.filterGenres = self.movieFilter.AppendItem(self.rootFilters, 'Genres')
		self.filterActors = self.movieFilter.AppendItem(self.rootFilters, 'Actors')
		self.filterDirectors = self.movieFilter.AppendItem(self.rootFilters, 'Directors')
		self.filterTags = self.movieFilter.AppendItem(self.rootFilters, 'Tags')
		
		self.movieFilter.Expand(self.rootFilters)
		self.movieFilter.SelectItem(self.filterAll)
		
		
	def _init_movielist(self):
		self.movieList.InsertColumn(0, '#', width=0)
		self.movieList.InsertColumn(1, 'Title', width=130)
		self.movieList.InsertColumn(2, 'Year', width=50)
		
	
	def _populate_filter(self):
		self.movieFilter.DeleteChildren(self.filterGenres)
		self._add_items_to_filter_group(
			self.filterGenres, self.db.getMovieCountForGenres())
			
		self.movieFilter.DeleteChildren(self.filterActors)
		self._add_items_to_filter_group(
			self.filterActors, self.db.getMovieCountForActors())
			
		self.movieFilter.DeleteChildren(self.filterDirectors)
		self._add_items_to_filter_group(
			self.filterDirectors, self.db.getMovieCountForDirectors())
			
		self.movieFilter.DeleteChildren(self.filterTags)
		self._add_items_to_filter_group(
			self.filterTags, self.db.getMovieCountForTags())
			
		#TODO persistant selected category after refresh
		'''
		if self.filterName == 'Genres':
			pass
		elif self.filterName == 'Actors':
			pass
		elif self.filterName == 'Directors':
			pass
		elif self.filterName == 'Tags':
			pass
		'''
			
		
	def _populate_movielist(self):
		print "Pop MovieList"
		if self.filterName == None:
			rows = self.db.getAllMovies(self.movieTitleSearch)
		else:
			if self.filterName == 'Genres':
				rows = self.db.getMoviesByGenreId(self.filterValue, 
					self.movieTitleSearch)
			elif self.filterName == 'Actors':
				rows = self.db.getMoviesByActorId(self.filterValue, 
					self.movieTitleSearch)
			elif self.filterName == 'Directors':
				rows = self.db.getMoviesByDirectorId(self.filterValue, 
					self.movieTitleSearch)
			elif self.filterName == 'Tags':
				rows = self.db.getMoviesByTagId(self.filterValue, 
					self.movieTitleSearch)
			else:
				rows = self.db.getAllMovies(self.movieTitleSearch)
			
		index = self.movieList.GetFirstSelected()
		count = self.movieList.GetItemCount()
		
		self.movieList.DeleteAllItems()
		for row in rows:
			#rowid,title,sort,timestamp,image,released,runtime,rated,summary,actors,directors,tags = row
			self.movieList.Append((row[0], row[1], row[5]))
			
		if count == self.movieList.GetItemCount():
			if index != -1:
				 self.movieList.Select(index)
				 self.movieList.Focus(index)
				 self.movieList.EnsureVisible(index)
				 

	def _list_to_str(self,value_list, seperator):
		result = []
		for row in value_list:
			rowid, value = row
			result.append(value)
		return seperator.join(result)
		
		
	def _display_details(self):
		if self.selectedMovie == None:
			return
		
		movie = self.db.getMovie(self.selectedMovie)
		
		if movie == None:
			return
			
		(movieid, title, sort, timestamp, 
		image, released, runtime, rated, summary) = movie
		
		image = os.path.join(self.postersPath,movie[4])
		
		html = self.detailHtmlTemplate.format(	
			title = title, 
			image = image, 
			released = released, 
			runtime = runtime,
			rated = rated, 
			summary = summary,
			genres = self._list_to_str(self.db.getGenresByMovieId(self.selectedMovie),u', '),
			actors = self._list_to_str(self.db.getActorsByMovieId(self.selectedMovie),u'<br>'),
			directors = self._list_to_str(self.db.getDirectorsByMovieId(self.selectedMovie),u'<br>'),
			tags = self._list_to_str(self.db.getTagsByMovieId(self.selectedMovie),u', '),
			files = "<ul><li>{0}</li></ul>".format(
				self._list_to_str(self.db.getFilesByMovieId(self.selectedMovie),u'</li><li>'))
			)
		
		self.movieDetailHtml.SetPage(html)
			
			
	def UpdateDisplay(self):
		self._populate_filter()
		self._populate_movielist()
		self._display_details()
		
		
	def Show(self):
		wx.Frame.Show(self)
		
		while self._init_db() == False:
			dlg = wx.DirDialog(self, 
				"Select the folder where the library is located at", 
				defaultPath='', 
				style=wx.DD_DIR_MUST_EXIST)
				
			result = dlg.ShowModal()
			path = dlg.GetPath()
			
			dlg.Destroy()
			
			if result == wx.ID_OK:
				self.libraryPath = path
			else:
				self.Destroy()
				sys.exit(2)
		
		self.UpdateDisplay()
		
		
		#self._populate_filter()
		#self.movieFilter.SelectItem(self.filterAll)
		#self._display_details()
		
		
	def OnClose(self, event):
		self.Destroy()
		'''
		dlg = wx.MessageDialog(self,
			"Do you really want to close this application?",
			"Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_OK:
			self.Destroy()
		'''
		
		
	def OnAddMovie(self, event):
		dlg = MovieDataEditor.MovieDataEditor(self, self.postersPath, self.catchPath, 'Add Movie to Library')
		result = dlg.ShowModal()
		if result == wx.ID_OK:
			data = dlg.GetData()
			if data['title'] != '':
				movieid = self.db.addMovie(data['title'],
					data['sort'],data['image'],data['released'],
					data['runtime'],data['rated'],data['summary'],
					data['genres'], data['actors'], data['directors'],
					data['files'])
				
				if movieid != None:
					print u"Movie '{0}' Added".format(data['title'])
				
					self.selectedMovie = movieid
			
					self.UpdateDisplay()
				else:
					msg = wx.MessageDialog(self, 
						'An error occurred while adding the movie', 
						'Error Adding Movie Metadata', wx.OK|wx.ICON_INFORMATION)
					msg.ShowModal()
					msg.Destroy()
			else:
				msg = wx.MessageDialog(self, 
					'Not title set so movie not added', 
					'Error Adding Movie to Library', wx.OK|wx.ICON_INFORMATION)
				msg.ShowModal()
				msg.Destroy()
		
		dlg.Destroy()
			
			
	def OnScanLibrary(self, event):
		'''
		dlg = wx.MessageDialog(self,
			"Scan Results",
			"Scan Results", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_OK:
			print "Added a scanned movie"
		'''
		dlg = LibraryScanner.LibraryScanner(self, self.libraryPath ,self.db, self.postersPath, self.catchPath)
		dlg.ShowModal()
		dlg.Destroy()
		self.UpdateDisplay()
		
			
	def OnEditMetadata(self, event):
		if self.selectedMovie != None:
			data = {}
			movieData = self.db.getMovie(self.selectedMovie)
			
			data['title'] = str(movieData[1])
			data['sort'] = str(movieData[2])
			data['image'] = str(movieData[4])
			data['released'] = str(movieData[5])
			data['runtime'] = str(movieData[6])
			data['rated'] = str(movieData[7])
			data['summary'] = str(movieData[8])
			data['genres'] = self.db.getGenresByMovieId(self.selectedMovie)
			data['actors'] = self.db.getActorsByMovieId(self.selectedMovie)
			data['directors'] = self.db.getDirectorsByMovieId(self.selectedMovie)
			data['files'] = self.db.getFilesByMovieId(self.selectedMovie)
		
			dlg = MovieDataEditor.MovieDataEditor(self, self.postersPath, self.catchPath,
					u'Edit Metadata: {0}'.format(data['title']))
			dlg.SetData(data)
			result = dlg.ShowModal()
			if result == wx.ID_OK:
				data = dlg.GetData()
				if data['title'] != '':
					movieid = self.db.updateMovie(self.selectedMovie,data['title'],
						data['sort'],data['image'],data['released'],
						data['runtime'],data['rated'],data['summary'],
						data['genres'], data['actors'], data['directors'],
						data['files'])
					
					if movieid != None:
						print u"Movie '{0}' Updated".format(data['title'])
						self.UpdateDisplay()
					else:
						print u"Cannot Update Movie '{0}'. An Error Occurred".format(data['title'])
						msg = wx.MessageDialog(self, 
							u"Cannot Update Movie '{0}'. An Error Occurred".format(data['title']), 
							'Error Editing Movie Metadata', wx.OK|wx.ICON_INFORMATION)
						msg.ShowModal()
						msg.Destroy()
				else:
					msg = wx.MessageDialog(self, 
						'Not title set so movie metadata not changed', 
						'Error Editing Movie Metadata', wx.OK|wx.ICON_INFORMATION)
					msg.ShowModal()
					msg.Destroy()
				
			dlg.Destroy()
			
			
	def OnAddTag(self, event):
		if self.selectedMovie != None:
			tags = self.db.getAllTagNames()
			dlg = wx.SingleChoiceDialog(self, 
				'To create a new tag click cancel. The available tags are:', 
				'Add a Tag', 
				tags, 
				wx.CHOICEDLG_STYLE)
			
			result = dlg.ShowModal()
			
			if result == wx.ID_OK:
				self.db.addTagNameToMovie(self.selectedMovie, dlg.GetStringSelection())
				
				self.UpdateDisplay()
			elif result == wx.ID_CANCEL:
				textEntry = wx.TextEntryDialog(self, 
					'Enter a name for the new tag','Create a Tag')
				textEntry.SetValue("")
				if textEntry.ShowModal() == wx.ID_OK:
					tagName = textEntry.GetValue()
					if tagName != '':
						self.db.addTagNameToMovie(self.selectedMovie,tagName)
						
						self.UpdateDisplay()
		
			dlg.Destroy()
			
	def OnRemoveTag(self, event):
		if self.selectedMovie != None:
			tagsList = self.db.getTagsByMovieId(self.selectedMovie)
			tags = []
			for rowid, tag in tagsList:
				tags.append(tag)
				
			dlg = wx.SingleChoiceDialog(self, 
				'Tags:', 
				'Remove a Tag', 
				tags, 
				wx.CHOICEDLG_STYLE)
				
			if dlg.ShowModal() == wx.ID_OK:
				index = dlg.GetSelection()
				tagid = tagsList[index][0]
				self.db.removeTagFromMovie(self.selectedMovie, tagid)
				
				self.UpdateDisplay()
		
			dlg.Destroy()
			
	
	def OnPlayMovie(self, event):
		if self.VlcPlayer == '':
			return
			
		if self.selectedMovie != None:
			dbFiles = self.db.getFilesByMovieId(self.selectedMovie)
			command = [self.VlcPlayer]
			for row in dbFiles:
				fileid, filename = row
				filename = os.path.join(self.libraryPath, filename)
				command.append(filename)
				
			if len(command) > 1:
				pid = subprocess.Popen(command).pid
			else:
				print "No files to play"
		else:
			print "No movie selected"
			
			
	def OnPlayMovieInbuilt(self, event):
		files = self.db.getFilesByMovieId(self.selectedMovie)
			
		absfiles = []
		
		for row in files:
			fileid, filename = row
			absfilename = os.path.join(self.libraryPath, filename)
			print absfilename
			if os.path.isfile(absfilename):
				absfiles.append('file://' + absfilename)
				
		if len(absfiles) > 0:
			self.player.Show(True)
			self.movieDetailHtml.Show(False)
			self.movieDetail.Layout()
			
			self.Media = self.Instance.media_new(absfiles[0])
			self.VlcPlayer.set_media(self.Media)
			self.VlcPlayer.set_xwindow(self.videopanel.GetHandle())
 
			if self.VlcPlayer.play() == -1:
				print "cant play"
		
			
	def OnMovieListTbSearch(self, event):
		self.movieTitleSearch = self.searchBox.GetValue()
		self._populate_movielist()
		
		
	def OnMovieFilterSelChanged(self, event):
		selection = self.movieFilter.GetSelection()
		selectionData = self.movieFilter.GetItemData(selection).GetData()
		
		if selection == self.filterAll:
			self.filterName = None
			self.filterValue = None
			self._populate_movielist()
		elif selectionData != None:
			self.filterName, self.filterValue = selectionData
			self._populate_movielist()
			
			
	def OnMovieListSelected(self, event):
		count = self.movieList.GetSelectedItemCount()
		if count == 1:
			self.VlcPlayer.stop()
			self.player.Show(False)
			self.movieDetailHtml.Show(True)
			self.movieDetail.Layout()
			
			index = event.GetIndex()
			self.selectedMovie = int(self.movieList.GetItemText(index))
			self._display_details()
			
			
	def OnMovieListRightClick(self, event):
		index = event.GetIndex()
		self.rightClickedMovie = self.movieList.GetItemText(index)
		
		menu = wx.Menu()
		
		m_del = wx.NewId()
		menu.Append(
			kind=wx.ITEM_NORMAL, 
			text="Delete Movie", 
			help="Delete this movie from the library(id={0})".format(self.rightClickedMovie),
			id=m_del)
		self.Bind(wx.EVT_MENU, self.OnDeleteMovie, id=m_del)
		
		self.movieList.PopupMenu( menu, event.GetPoint())
		
		menu.Destroy()
		
		
	def OnDeleteMovie(self, event):
		if self.rightClickedMovie != None:
			movie = self.db.getMovie(self.rightClickedMovie)
			if movie != None:
				title = movie[1]
				print "delete movie " + title
				dlg = wx.MessageDialog(self,
					"Delete '{0}' from the library? The actual movie files will not be removed".format(title), 
					"Delete Movie From Library",
					wx.YES|wx.NO|wx.ICON_QUESTION)
				result = dlg.ShowModal()
				dlg.Destroy()
				if result == wx.ID_YES:
					self.db.deleteMovie(self.rightClickedMovie)
					
					self.selectedMovie = None
					index = self.movieList.GetFirstSelected()
					self.movieList.DeleteItem(index)
					self._populate_filter()
					#self._populate_movielist()
					self._display_details()
					
					
	def OnAbout(self, event):
		f = open(licensePath)
		license = unicode(f.read())
		f.close()
		
		aboutInfo = wx.AboutDialogInfo()
		aboutInfo.SetName("Portable Movie Organizer")
		aboutInfo.SetCopyright("Copyright (C) 2011 Ali Aafee")
		aboutInfo.SetDescription("Manage your movie library directly from your portable drive")
		aboutInfo.AddDeveloper("Ali Aafee")
		aboutInfo.SetLicense(license)
		wx.AboutBox(aboutInfo)
		print "About"
