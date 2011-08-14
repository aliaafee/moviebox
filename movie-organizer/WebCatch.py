import sqlite3
import urllib

import os

dirName = os.path.dirname(os.path.abspath(__file__))
dirName, fileName = os.path.split(dirName)
catchDir = os.path.join(dirName, 'catch')


def get(url):
	if not os.path.isdir(catchDir):
		os.mkdir(catchDir)
		
	dataDir = os.path.join(catchDir, 'data')
	if not os.path.isdir(dataDir):
		os.mkdir(dataDir)
		
	cathDbPath = os.path.join(catchDir, 'catch.db')
	
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
		
		
	
