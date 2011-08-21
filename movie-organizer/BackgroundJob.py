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

from threading import Thread
import wx
import wx.lib.newevent

DoneBackgroundJob, EVT_DONE_BACKGROUND_JOB = wx.lib.newevent.NewEvent()

class BackgroundJob(Thread):
	def __init__(self, parent):
		self.parent = parent
		
		Thread.__init__(self)
		
		
	def run(self):
		#Processing here
		print "Something to be done here"
		self.donejob(self)
		
	
	def donejob(self, **args):
		wx.PostEvent(self.parent, DoneBackgroundJob(**args))
		
		
