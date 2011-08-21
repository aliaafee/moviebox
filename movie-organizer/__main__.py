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
	print "Portable Movie Organizer"
	print "------------------------"
	print "Copyright (C) 2010 Ali Aafee"
	print "This program comes with ABSOLUTELY NO WARRANTY"
	print "This is free software, and you are welcome to redistribute it"
	print "under certain conditions. See license.txt for details"
	print " "
	print "Usage:"
	print "    -h, --help"
	print "       Displays this help"
	print " "
	print "    -l, --library"
	print "       Set the location of the library"
	print "       If not given a dialog will appear requseting it"
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
