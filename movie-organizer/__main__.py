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

import MainFrame
import os
import sys
import getopt
import time
import MediaServer

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
		
		
def license():
	print "Portable Movie Organizer"
	print "------------------------"
	print "Copyright (C) 2010 Ali Aafee"
	print "This program comes with ABSOLUTELY NO WARRANTY"
	print "This is free software, and you are welcome to redistribute it"
	print "under certain conditions. See license.txt for details"
		
		
def usage():
	license()
	print " "
	print "Usage:"
	print "    -h, --help"
	print "       Displays this help"
	print " "
	print "    -l, --library"
	print "       Set the location of the library"
	print "       If not given a dialog will appear reqeseting it"
	print " "
	print "    -p, --player"
	print "         The player to use (optional)"
	print " "
	print "    -x, --headless"
	print "         Run with web interface. (optional) "
	print "         Arguments are interface & port (xxx.xxx.xxx:0000)"
	print " "
	
	
def runheadless(address, library):
	license()
	print " "
	print "Running with web interface."
	print "Warning: This feature is experimental"
	print ""
	
	if address == '' or library == '':
		print "The address and/or library path are invalid"
		sys.exit(2)
	
	address = address.partition(':')
	ip = address[0]
	try:
		port = int(address[2])
	except ValueError:
		print "Bad port '{0}'".format(address[2])
		sys.exit(2)
	
	server = MediaServer.MediaServer((ip, port), library)
	server.start()
	
	print "Server started at {0}:{1}. Ctrl-C to stop".format(ip, port)
	print ""
	
	try:
		while not server._stopped:
			time.sleep(1)
	except KeyboardInterrupt:
		print ""
		server.stop()

	sys.exit(2)
		
		
def main(argv):
	library = ''
	
	try:
		opts, args = getopt.getopt(argv, "hl:p:x:", ["help", "library=","player=","headless="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
		
	library = ''
	player = ''
	headless = False
	address = ''
		
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-l", "--library"):
			library = arg
		elif opt in ("-p", "--player"):
			player = arg
		elif opt in ("-x", "--headless"):
			address = arg
			headless = True
			
	if headless:
		runheadless(address, library)
	else:
		app = MovieOrganizer(0, library, player)
		app.MainLoop()
	
	
if __name__ == '__main__':
	main(sys.argv[1:])
