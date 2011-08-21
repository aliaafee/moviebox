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
import wx.lib.mixins.listctrl  as  listmix

VALUE_NORMAL = 'normal'
VALUE_DELETED = 'delete'




class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin):
	def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
			size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.TextEditMixin.__init__(self)




class FieldDataList(wx.Panel):
	def __init__(self, parent, size=wx.Size(-1,-1)):
		self._init_ctrls(parent, size)
		
		self._value_data_list = {}
		self._counter = 0
		
	def _init_ctrls(self, parent, size):
		wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER, 
			size=size)
		
		sizer = wx.GridBagSizer(0, 0)
		sizer.AddGrowableCol(1)
		
		self.valueList = EditableListCtrl(self, style=wx.LC_SINGLE_SEL | wx.LC_REPORT)
		self.valueList.InsertColumn(0,'', width=200)
		sizer.Add(self.valueList, pos=(0,1), span=(2,1), flag=wx.EXPAND)
		
		self.SetBackgroundColour(self.valueList.GetBackgroundColour())
		
		self.btnAdd = wx.Button(self, label='+', size=(20,20))
		self.btnAdd.Bind(wx.EVT_BUTTON, self.OnAddNew)
		sizer.Add(self.btnAdd, pos=(0,0))
		
		self.btnDel = wx.Button(self, label='-', size=(20,20))
		self.btnDel.Bind(wx.EVT_BUTTON, self.OnDel)
		sizer.Add(self.btnDel, pos=(1,0))
		
		self.SetSizer(sizer)
		
		
	def AddValue(self, rowid=0, value='', state=VALUE_NORMAL):
		data = (rowid,state)
		self._counter += 1
		dataid = self._counter
		
		self._value_data_list[dataid] = data
		
		index = self.valueList.Append((value,))
		self.valueList.SetItemData(index, dataid)
		
		return index
		
		
	def AddValues(self, values):
		for data in values:
			rowid, value = data
			self.AddValue(rowid,value)
			
	def AddValuesSimple(self, values):
		for value in values:
			self.AddValue(0,value)
			
			
	def DeleteAllItems(self):
		index = 0
		while index < self.valueList.GetItemCount():
			dataid = self.valueList.GetItemData(index)
			rowid, state = self._value_data_list[dataid]
			if rowid == 0:
				self.valueList.DeleteItem(index)
				del(self._value_data_list[dataid])
			else:
				if state == VALUE_NORMAL:
					value = self.valueList.GetItemText(index)
					value = u'{0} <deleted>'.format(value)
					self.valueList.SetItemText(index, value)
					self.valueList.SetItemTextColour(index, wx.Color(255,0,0))
					self._value_data_list[dataid] = (rowid, VALUE_DELETED)
				index += 1
				
		
	def DeleteItem(self, index):
		if index > -1:
			dataid = self.valueList.GetItemData(index)
			rowid, state = self._value_data_list[dataid]
			if rowid == 0:
				self.valueList.DeleteItem(index)
				del(self._value_data_list[dataid])
			else:
				if state == VALUE_NORMAL:
					value = self.valueList.GetItemText(index)
					value = u'{0} <deleted>'.format(value)
					self.valueList.SetItemText(index, value)
					self.valueList.SetItemTextColour(index, wx.Color(255,0,0))
					self._value_data_list[dataid] = (rowid, VALUE_DELETED)
		
		
	def GetValues(self):
		result = []
		
		if self.valueList.GetItemCount() == 0:
			return result
		
		for index in range(0,self.valueList.GetItemCount()):
			value = self.valueList.GetItemText(index)
			dataid = self.valueList.GetItemData(index)
			rowid, state = self._value_data_list[dataid]
			
			if value != '<new>' and value != '':
				result.append((rowid, value, state))

		return result
		
		
	def OnAddNew(self, event):
		index = self.AddValue(0,'<new>')
		self.valueList.Select(index)
		
	
	def OnDel(self, event):
		index = self.valueList.GetNextSelected(-1)
		if index != -1:
			self.DeleteItem(index)
					
