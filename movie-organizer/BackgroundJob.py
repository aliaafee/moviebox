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
		
		
