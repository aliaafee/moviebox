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
import FieldDataList
import ImdbAPI
import os.path
import thread


dirName = os.path.dirname(os.path.abspath(__file__))
dirName, fileName = os.path.split(dirName)
resDir = os.path.join(dirName, 'res')

class MovieDataEditor(wx.Dialog):
	def __init__(self, parent, postersPath, catchPath, title='Edit Movie Metadata'):
		self.title = title
		self.postersPath = postersPath
		self.catchPath = catchPath
		
		self._init_ctrls(parent)
		
		
	
	def _init_ctrls(self, parent):
		wx.Dialog.__init__(self, name='MovieEditor', parent=parent,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
			title=self.title, size=wx.Size(640,480))
			
		self.fieldWindow = wx.ScrolledWindow(self, size=wx.Size(200,200), style=wx.HSCROLL)
		self.fieldWindow.SetScrollbars(0,10,0,65)
		
		gridSizer = wx.FlexGridSizer(7,4,10,10)
		gridSizer.AddGrowableCol(1,1)
		gridSizer.AddGrowableCol(3,1)
		
		labelWidth = -1
		
		gridSizer.AddSpacer(5)
		gridSizer.AddSpacer(5)
		gridSizer.AddSpacer(5)
		gridSizer.AddSpacer(5)
		
		self.lblTitle = wx.StaticText(self.fieldWindow, label='Title', size=wx.Size(labelWidth,-1))
		self.txtTitle = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblTitle, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtTitle, 1, wx.EXPAND)
		
		self.lblSort = wx.StaticText(self.fieldWindow, label='Sort', size=wx.Size(labelWidth,-1))
		self.txtSort = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblSort, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtSort, 1, wx.EXPAND)
		
		self.lblImage = wx.StaticText(self.fieldWindow, label='Poster', size=wx.Size(labelWidth,-1))
		self.txtImage = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblImage, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtImage, 1, wx.EXPAND)
			
		self.lblReleased = wx.StaticText(self.fieldWindow, label='Released', size=wx.Size(labelWidth,-1))
		self.txtReleased = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblReleased, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtReleased, 1, wx.EXPAND)
		
		self.lblRuntime = wx.StaticText(self.fieldWindow, label='Runtime', size=wx.Size(labelWidth,-1))
		self.txtRuntime = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblRuntime, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtRuntime, 1, wx.EXPAND)
		
		self.lblRated = wx.StaticText(self.fieldWindow, label='Rated', size=wx.Size(labelWidth,-1))
		self.txtRated = wx.TextCtrl(self.fieldWindow)
		gridSizer.Add(self.lblRated, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtRated, 1, wx.EXPAND)
		
		self.lblSummary = wx.StaticText(self.fieldWindow, label='Summary', size=wx.Size(labelWidth,-1))
		self.txtSummary = wx.TextCtrl(self.fieldWindow, style=wx.TE_MULTILINE, size=wx.Size(-1,80))
		gridSizer.Add(self.lblSummary, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.txtSummary, 1, wx.EXPAND)
		
		self.lblGenres = wx.StaticText(self.fieldWindow, label='Genres', size=wx.Size(labelWidth,-1))
		self.lstGenres = FieldDataList.FieldDataList(self.fieldWindow, size=wx.Size(-1,100))
		gridSizer.Add(self.lblGenres, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.lstGenres, 1, wx.EXPAND)
		
		self.lblActors = wx.StaticText(self.fieldWindow, label='Actors', size=wx.Size(labelWidth,-1))
		self.lstActors = FieldDataList.FieldDataList(self.fieldWindow, size=wx.Size(-1,100))
		gridSizer.Add(self.lblActors, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.lstActors, 1, wx.EXPAND)
		
		self.lblDirectors = wx.StaticText(self.fieldWindow, label='Directors', size=wx.Size(labelWidth,-1))
		self.lstDirectors = FieldDataList.FieldDataList(self.fieldWindow)
		gridSizer.Add(self.lblDirectors, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.lstDirectors, 1, wx.EXPAND)
		
		self.lblFiles = wx.StaticText(self.fieldWindow, label='Files', size=wx.Size(labelWidth,-1))
		self.lstFiles = FieldDataList.FieldDataList(self.fieldWindow)
		gridSizer.Add(self.lblFiles, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		gridSizer.Add(self.lstFiles, 1, wx.EXPAND)
		
		gridSizer.Add(wx.StaticText(self.fieldWindow, label=''))
		
		self.fieldWindow.SetSizer(gridSizer)
		self.fieldWindow.Layout()
		
		self.btnSizer = self.CreateButtonSizer(wx.CANCEL)
		
		self.btnSave = wx.Button(self, label="Save")
		self.btnSave.Bind(wx.EVT_BUTTON, self.OnSave)
		self.btnSizer.Add(self.btnSave)
		
		self.mainTb = self._create_main_tb(self)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.mainTb, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 0 )
		vbox.Add(self.fieldWindow, 1, wx.EXPAND)
		vbox.Add(wx.StaticText(self,label=""))
		vbox.Add(self.btnSizer, 0, wx.ALIGN_CENTER)
		
		self.SetSizer(vbox)
		self.Layout()
	
		
	def _create_main_tb(self, parent):
		tb = wx.ToolBar(parent, style=wx.TB_TEXT|wx.TB_NODIVIDER|wx.TB_HORIZONTAL|wx.TB_FLAT)
		tb.SetToolBitmapSize((21, 21))
		
		self.tb_search = wx.NewId()
		tb.DoAddTool(
			bitmap=wx.Bitmap(os.path.join(resDir,'web.png'), wx.BITMAP_TYPE_PNG),
			#bitmap=wx.ArtProvider.GetBitmap(wx.ART_FIND),
			bmpDisabled=wx.NullBitmap, 
			id=self.tb_search,
			kind=wx.ITEM_NORMAL, 
			label='', 
			longHelp='', 
			shortHelp='Get Metadata from IMDB')
		self.Bind(wx.EVT_TOOL, self.OnGetMetadata,
			id=self.tb_search)
			
		self.statusText = wx.StaticText(tb, label="")
		
		tb.AddControl(self.statusText)

		tb.Realize()
		
		return tb
		
		
	def SetData(self, data):
		self.txtTitle.SetValue(data['title'])
		self.txtSort.SetValue(data['sort'])
		self.txtImage.SetValue(data['image'])
		self.txtReleased.SetValue(data['released'])
		self.txtRuntime.SetValue(data['runtime'])
		self.txtRated.SetValue(data['rated'])
		self.txtSummary.SetValue(data['summary'])

		self.lstGenres.DeleteAllItems()
		self.lstGenres.AddValues(data['genres'])

		self.lstActors.DeleteAllItems()
		self.lstActors.AddValues(data['actors'])

		self.lstDirectors.DeleteAllItems()
		self.lstDirectors.AddValues(data['directors'])

		self.lstFiles.DeleteAllItems()
		self.lstFiles.AddValues(data['files'])
		 
		
		
	def GetData(self):
		data = {}
		data['title'] = self.txtTitle.GetValue()
		data['sort'] = self.txtSort.GetValue()
		data['image'] = self.txtImage.GetValue()
		data['released'] = self.txtReleased.GetValue()
		data['runtime'] = self.txtRuntime.GetValue()
		data['rated'] = self.txtRated.GetValue()
		data['summary'] = self.txtSummary.GetValue()
		
		data['genres'] = self.lstGenres.GetValues()
		data['actors'] = self.lstActors.GetValues()
		data['directors'] = self.lstDirectors.GetValues()
		data['files'] = self.lstFiles.GetValues()
		
		return data
		
		
	def OnSave(self, event):
		if self.txtTitle.GetValue() == '':
			msg = wx.MessageDialog(self, 
				'Movie metadata cannot be saved without a Title. Cannot continue', 
				'Movie Title Missing', wx.OK|wx.ICON_INFORMATION)
			msg.ShowModal()
			msg.Destroy()
		else:
			self.EndModal(wx.ID_OK)
		
		
	def OnGetMetadata(self, event):
		title = self.txtTitle.GetValue()
		year = self.txtReleased.GetValue()
		
		if title=='':
			dlg = wx.MessageDialog(self,
				"Enter the title of the movie. Optionally enter the year(approximate).", 
				"Get metadata from IMDB",
				wx.OK|wx.ICON_INFORMATION)
			result = dlg.ShowModal()
			dlg.Destroy()
			return
		
		self.mainTb.EnableTool(self.tb_search, False)
		
		self.statusText.SetLabel("Getting metadata from IMDB...")
		
		thread.start_new_thread(self._get_metadata, (title, year, self.postersPath, self.catchPath))
		
	
	def _get_metadata(self, title, year, postersPath, catchPath):
		try:
			metadata = ImdbAPI.GetMetadata(title, year, postersPath, catchPath)
		
			wx.CallAfter(self._done_get_metadata, metadata)
		except wx._core.PyDeadObjectError, e:
			print "dialog closed before thread could complete"
		
	
	def _done_get_metadata(self, metadata):
		self.statusText.SetLabel("")
		
		if metadata != None:
			print "Success"
			
			self.txtTitle.SetValue(metadata['title'])
			self.txtImage.SetValue(metadata['image'])
			self.txtReleased.SetValue(metadata['released'])
			self.txtRuntime.SetValue(metadata['runtime'])
			self.txtRated.SetValue(metadata['rated'])
			self.txtSummary.SetValue(metadata['summary'])
		
			print "Genres"
			self.lstGenres.DeleteAllItems()
			self.lstGenres.AddValuesSimple(metadata['genres'])

			print "Actors"
			self.lstActors.DeleteAllItems()
			self.lstActors.AddValuesSimple(metadata['actors'])

			print "Directors"
			self.lstDirectors.DeleteAllItems()
			self.lstDirectors.AddValuesSimple(metadata['directors'])
		else:
			dlg = wx.MessageDialog(self,
				"No results were found for the given title and year. (this may be due to a network error)", 
				"Get metadata from IMDB",
				wx.OK|wx.ICON_INFORMATION)
			result = dlg.ShowModal()
			dlg.Destroy()
		
		self.mainTb.EnableTool(self.tb_search, True)
		
		
