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

import sqlite3
import urllib

import os

dirName = os.path.dirname(os.path.abspath(__file__))
dirName, fileName = os.path.split(dirName)
fallBackCatchPath = os.path.join(dirName, 'catch')


def get(url, catchPath=fallBackCatchPath):
	if not os.path.isdir(catchPath):
		os.mkdir(catchPath)
		
	dataDir = os.path.join(catchPath, 'data')
	if not os.path.isdir(dataDir):
		os.mkdir(dataDir)
		
	cathDbPath = os.path.join(catchPath, 'catch.db')
	
	conn = sqlite3.connect(cathDbPath)
	
	conn.execute('CREATE TABLE IF NOT EXISTS catch(url TEXT)')
	conn.commit()
	
	row = conn.execute('SELECT ROWID FROM catch WHERE url==?', (url,)).fetchone()
	
	if row != None:
		catchid = row[0]
		
		filename = os.path.join(dataDir, str(catchid))
		#filename = "catch/data/{0}".format(catchid)
		
		try:
			f = open(filename, 'rb')
			data = f.read()
			f.close()
			
			conn.close()
			
			return data
		except IOError:
			pass
			#conn.execute('DELETE FROM catch WHERE url=?', url)
	
	catchid = None
	
	try:
		data = urllib.urlopen(url).read()
		
		result = conn.execute('INSERT INTO catch VALUES (?)',(url,))
		catchid = result.lastrowid
		
		conn.commit()
		
		#filename = "catch/data/{0}".format(catchid)
		filename = os.path.join(dataDir, str(catchid))
		
		f = open(filename, 'wb')
		f.write(data)
		f.close()
		
		conn.close()
		
		return data
	except IOError:
		#if catchid != None:
		#	conn.execute('DELETE FROM catch WHERE url=?', url)
		return ''
		
		
	
