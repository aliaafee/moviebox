import wx

import MainFrame
import os
import sys
import getopt

class MovieOrganizer(wx.App):
	def __init__(self, parent, library, player=''):
		self.libraryPath = library
		self.player = player
		wx.App.__init__(self, parent)
		
	def OnInit(self):
		self.main = MainFrame.create(None, self.libraryPath, self.player)
		self.main.Show()
		self.SetTopWindow(self.main)
		return True
		
		
def usage():
	print "Movie Organizer"
	print "==============="
	print "Usage:"
	print "    -h, --help"
	print "         Displays this help"
	print " "
	print "    -l, --library"
	print "         Set the location of the library"
	print "         This option is required"
	print " "
	print "    -p, --player"
	print "         The player to use (optional)"
	print " "
		
		
def main(argv):
	library = ''
	
	try:
		opts, args = getopt.getopt(argv, "hl:p:", ["help", "library=","player="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
		
	library = ''
	player = ''
		
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-l", "--library"):
			library = arg
		elif opt in ("-p", "--player"):
			player = arg
			
	#if library == '':
	#	usage()
	#	sys.exit(2)
	
	app = MovieOrganizer(0, library, player)
	app.MainLoop()
	
	
if __name__ == '__main__':
	main(sys.argv[1:])
