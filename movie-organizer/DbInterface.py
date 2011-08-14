"""
	portable-movie-organizer
	------------------------
	
	Copyright (C) 2010 Ali Aafee
	
	This file is part of portable-movie-organizer.

	portable-movie-organizer is free software: you can redistribute it 
	and/or modify it under the terms of the GNU General Public License 
	as published by the Free Software Foundation, either version 3 of 
	the License, or (at your option) any later version.

	Foobar is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with portable-movie-organizer.  
	If not, see <http://www.gnu.org/licenses/>.
"""

import sqlite3
import os.path


class DbInterface:
	def __init__(self, dbfile):
		try:
			self.conn = sqlite3.connect(dbfile)
		
			self._create_tables()
			
			self.connected = True
		except sqlite3.OperationalError, e:
			self.connected = False
			
			print u"Failed to open database: {0}".format(dbfile)
		
		
	def isConnected(self):
		return self.connected
		
		
	def _create_tables(self):
		self.conn.executescript(
			"""
			CREATE TABLE IF NOT EXISTS movies (
				id INTEGER PRIMARY KEY,
				title TEXT,
				sort TEXT,
				timestamp TEXT,
				image TEXT,
				released TEXT,
				runtime TEXT,
				rated TEXT,
				summary TEXT
			);

			CREATE TABLE IF NOT EXISTS files (
				id INTEGER PRIMARY KEY,
				name TEXT
			);
			
			CREATE TABLE IF NOT EXISTS movie_files_link (
				id INTEGER PRIMARY KEY,
				movie INTEGER,
				file INTEGER
			);
			
			CREATE TABLE IF NOT EXISTS genres (
				id INTEGER PRIMARY KEY,
				name TEXT
			);

			CREATE TABLE IF NOT EXISTS movie_genres_link (
				id INTEGER PRIMARY KEY,
				movie INTEGER,
				genre INTEGER
			);

			CREATE TABLE IF NOT EXISTS actors (
				id INTEGER PRIMARY KEY,
				name TEXT
			);

			CREATE TABLE IF NOT EXISTS movie_actors_link (
				id INTEGER PRIMARY KEY,
				movie INTEGER,
				actor INTEGER
			);
			
			CREATE TABLE IF NOT EXISTS directors (
				id INTEGER PRIMARY KEY,
				name TEXT
			);

			CREATE TABLE IF NOT EXISTS movie_directors_link (
				id INTEGER PRIMARY KEY,
				movie INTEGER,
				director INTEGER
			);
			

			CREATE TABLE IF NOT EXISTS tags (
				id INTEGER PRIMARY KEY,
				name TEXT
			);

			CREATE TABLE IF NOT EXISTS movie_tags_link (
				id INTEGER PRIMARY KEY,
				movie INTEGER,
				tag INTEGER
			);
			"""
			)
			
		self.conn.commit()
		
		
	def _add_unique(self, table, field, value):
		count, = self.conn.execute(
			"SELECT COUNT() FROM {0} WHERE {1}=?".format(table, field),
			(value,)).fetchone()
			
		if count == 0:
			result = self.conn.execute(
				"INSERT INTO {0} (id, {1}) VALUES(NULL,?)"
					.format(table, field),
				(value,))
			self.conn.commit()
			return result.lastrowid
		else:
			id, = self.conn.execute(
				"SELECT id FROM {0} WHERE {1}=?".format(table, field),
				(value,)).fetchone()
			return id
		
		
	def addGenre(self,name):
		return self._add_unique('genres', 'name', name)
			
			
	def addActor(self,name):
		return self._add_unique('actors', 'name', name)
		
		
	def addDirector(self,name):
		return self._add_unique('directors', 'name', name)
		
		
	def addTag(self,name):
		return self._add_unique('tags', 'name', name)
		
		
	def addFile(self, filename):

		if os.path.sep == '\\':
			filename = filename.replace('\\', '/')
			
		return self._add_unique('files', 'name', filename)
		
	
	def _add_unique_link(self, table, oneField, manyField, 
											oneValue, manyValue):
		count, = self.conn.execute(
			"SELECT COUNT() FROM {0} WHERE {1}=? AND {2}=?"
				.format(table, oneField, manyField),
			(oneValue, manyValue)).fetchone()
			
		if count == 0:
			result = self.conn.execute(
				"INSERT INTO {0} (id,{1},{2}) VALUES(NULL,?,?)"
					.format(table, oneField, manyField),
				(oneValue, manyValue))
			self.conn.commit()
			return result.lastrowid
		else:
			id, = self.conn.execute(
				"SELECT id FROM {0} WHERE {1}=? AND {2}=?"
					.format(table, oneField, manyField),
				(oneValue, manyValue)).fetchone()
			return id
			
	
	def addGenreNameToMovie(self, movieid, name):
		genreid = self.addGenre(name)
		return self._add_unique_link('movie_genres_link', 
			'movie', 'genre', movieid, genreid)
	
		
	def addActorNameToMovie(self, movieid, name):
		actorid = self.addActor(name)
		return self._add_unique_link('movie_actors_link', 
			'movie', 'actor', movieid, actorid)
			
			
	def addDirectorNameToMovie(self, movieid, name):
		directorid = self.addDirector(name)
		return self._add_unique_link('movie_directors_link', 
			'movie', 'director', movieid, directorid)
			
		
	def addTagIdToMovie(self, movieid, tagid):
		return self._add_unique_link('movie_tags_link',
			'movie', 'tag', movieid, tagid)
			
			
	def addTagNameToMovie(self, movieid, name):
		tagid = self.addTag(name)
		return self.addTagIdToMovie(movieid, tagid)
		
		
	def removeTagIdFromMovie(self, movieid, tagid):
		#delete link from field to movie
		result = self.conn.execute(
			'''
			DELETE FROM movie_tags_link
			WHERE movie=? AND tag=?
			''',(movieid, tagid))
		self.conn.commit()
		return result
		
			
	def editTagName(self, tagid, newName):
		#change the name of a tag
		result = self.conn.execute(
			'''
			UPDATE tags
			SET
				name=?
			WHERE
				id=?
			''',(newName, tagid))
		self.conn.commit()
		return result
		
		
	def addFileIdToMovie(self, movieid, fileid):
		return self._add_unique_link('movie_files_link',
			'movie', 'file', movieid, fileid)
		
		
	def _get_movie_count_for(self, field):
		result = self.conn.execute(
			'''
			SELECT	{0}s.id, {0}s.name, COUNT() 
			FROM	{0}s, movie_{0}s_link 
			WHERE	{0}s.id=movie_{0}s_link.{0} GROUP BY {0}s.id 
			ORDER BY {0}s.name
			'''.format(field))
		return result
		
	
	def getMovieCountForGenres(self):
		return self._get_movie_count_for('genre')
	
		
	def getMovieCountForActors(self):
		return self._get_movie_count_for('actor')
		
		
	def getMovieCountForDirectors(self):
		return self._get_movie_count_for('director')
		
		
	def getMovieCountForTags(self):
		return self._get_movie_count_for('tag')
		
		
	def getAllMovies(self, titleSearch):
		titleSearch = '%{0}%'.format(titleSearch)
		
		result = self.conn.execute(
			'''
			SELECT
				id,
				title,
				sort,
				timestamp,
				image,
				released,
				runtime,
				rated,
				summary
			FROM movies
			WHERE title LIKE ?
			ORDER BY title
			''',(titleSearch,))
		
		return result
		
		
	def _get_movies_by(self, filterField, filterValue, titleSearch):
		titleSearch = '%{0}%'.format(titleSearch)
		
		result = self.conn.execute(
			'''
			SELECT
				movies.id,
				movies.title,
				movies.sort,
				movies.timestamp,
				movies.image,
				movies.released,
				movies.runtime,
				movies.rated,
				movies.summary
			FROM movies, movie_{0}s_link
			WHERE
				movies.id = movie_{0}s_link.movie
				AND
				movie_{0}s_link.{0} = ?
				AND
				movies.title LIKE ?
			'''.format(filterField), (filterValue, titleSearch))
		
		return result
		
		
	def getMoviesByGenreId(self, genreId, titleSearch):
		return self._get_movies_by('genre', genreId,titleSearch)
		
		
	def getMoviesByActorId(self, actorId, titleSearch):
		return self._get_movies_by('actor', actorId,titleSearch)
		
		
	def getMoviesByDirectorId(self, directorId, titleSearch):
		return self._get_movies_by('director', directorId,titleSearch)
		
		
	def getMoviesByTagId(self, tagId, titleSearch):
		return self._get_movies_by('tag', tagId,titleSearch)
		
		
	def _get_by_movieid(self, field, movieid):
		result = self.conn.execute(
			'''
			SELECT 
				{0}s.id,
				{0}s.name
			FROM
				{0}s, movie_{0}s_link
			WHERE
				{0}s.id = movie_{0}s_link.{0}
				AND
				movie_{0}s_link.movie = ?
			'''.format(field), (movieid,))
		
		resultList = []
		
		for row in result:
			rowid, value = row
			resultList.append((rowid, value))
			
		return resultList
		
		
	def getGenresByMovieId(self,movieid):
		return self._get_by_movieid('genre', movieid)	
		
		
	def getActorsByMovieId(self,movieid):
		return self._get_by_movieid('actor', movieid)
		
		
	def getDirectorsByMovieId(self,movieid):
		return self._get_by_movieid('director', movieid)
		
		
	def getTagsByMovieId(self,movieid):
		return self._get_by_movieid('tag', movieid)
		
		
	def getFilesByMovieId(self,movieid):
		rows = self._get_by_movieid('file', movieid)
		if os.path.sep == '\\':
			result = []
			for row in rows:
				fileid, filename = row
				filename = filename.replace('/', '\\')
				result.append((fileid, filename))
			return result
		else:
			return rows
		
		
	def getFileId(self, filename):
		
		if os.path.sep == '\\':
			filename = filename.replace('\\', '/')
			
		result = self.conn.execute(
			'''
			SELECT id
			FROM files
			WHERE name=?
			''',(filename,))
		row = result.fetchone()
		if row != None:
			fileid, = row
			return fileid
		else:
			return None
			
	def fileIsLinked(self, fileid):
		result = self.conn.execute(
			'''
			SELECT id
			FROM movie_files_link
			WHERE file=?
			''',(fileid,))
		row = result.fetchone()
		if row == None:
			return False
		else:
			return True
		
		
	def removeTagFromMovie(self, movieid, tagid):
		result = self.conn.execute(
			'''
			DELETE FROM movie_tags_link
			WHERE movie=? AND tag=?
			''',(movieid, tagid))
			
		self.conn.commit()
		
		
	def getAllTagNames(self):
		result = self.conn.execute(
			'''
			SELECT
				name
			FROM tags
			''')
		tagNames = []
		for row in result:
			tagName, = row
			tagNames.append(tagName)
		
		return tagNames
		
		
	def getMovie(self, movieid):
		result = self.conn.execute(
			'''
			SELECT
				id,
				title,
				sort,
				timestamp,
				image,
				released,
				runtime,
				rated,
				summary
			FROM movies
			WHERE id=?
			''',(movieid,))
		return result.fetchone()
		
		
	def _update_linked_fileds(self, movieid, field, values):
		try:
			for value in values:
				rowid, name, state = value
				if rowid == 0:
					#Add new field add it to db
					index = self._add_unique('{0}s'.format(field), 'name', name)
					self._add_unique_link('movie_{0}s_link'.format(field), 
						'movie', field, movieid, index)
				else:
					if state == 'delete':
						#delete link from field to movie
						result = self.conn.execute(
							'''
							DELETE FROM movie_{0}s_link
							WHERE movie=? AND {0}=?
							'''.format(field),(movieid, rowid))
					else:
						#update field name
						result = self.conn.execute(
							'''
							UPDATE {0}s
							SET
								name=?
							WHERE
								id=?
							'''.format(field),(name, rowid))
			return True
		except sqlite3.OperationalError:
			return None
			
			
	def updateMovieFilesLink(self, movieid, files):
		#little routine to fix file seperators for other windows support
		#in the database files are stored with the '/' seperator
		if os.path.sep == '\\':
			result = []
			for row in files:
				rowid, filename, state = row
				filename = filename.replace('\\','/')
				result.append((rowid, filename, state))
			result = self._update_linked_fileds(movieid, 'file', result)
			
			return result
		else:	
			result = self._update_linked_fileds(movieid, 'file', files)
			
			return result
			
		
	def updateMovie(self, movieid, title, sort, image, released, runtime, rated, 
						summary, genres, actors, directors, files):
		try:
			result = self.conn.execute(
				'''
				UPDATE movies
				SET
					title=?,
					sort=?,
					image=?,
					released=?,
					runtime=?,
					rated=?,
					summary=?
				WHERE id=?
				''',(title, sort, image, released, runtime, rated, summary, movieid))
		except sqlite3.OperationalError:
			return None
		
		result = self._update_linked_fileds(movieid, 'genre', genres)
		if result == None:
			return None
			
		result = self._update_linked_fileds(movieid, 'actor', actors)
		if result == None:
			return None
		
		result = self._update_linked_fileds(movieid, 'director', directors)
		if result == None:
			return None
		
		result = self.updateMovieFilesLink(movieid, files)
		if result == None:
			return None
			
		self.conn.commit()
		
		return movieid
		
		
	def _add_movie_base(self,title, sort, timestamp, image, released, 
							runtime, rated, summary):
		try:
			result = self.conn.execute(
				'''
				INSERT INTO 
				movies (id, title, sort, timestamp, image, released, runtime, rated, summary)
				VALUES (NULL,?,?,?,?,?,?,?,?)
				''',
				(title, sort, timestamp, image, released, runtime, rated, summary))
		
			self.conn.commit()
		
			movieid = result.lastrowid
		
			return movieid
		except sqlite3.OperationalError:
			return None
		
		
	def addMovie(self, title, sort='', image='', released='', runtime='', rated='', 
					summary='', genres=[], actors=[], directors=[], files=[], timestamp=None):
		
		if timestamp == None:
			timestamp = 'timenow'
	
		movieid = self._add_movie_base(title, sort, timestamp, image, released, 
			runtime, rated, summary)
		
		if movieid == None:
			return None
		
		result = self._update_linked_fileds(movieid, 'genre', genres)
		if result == None:
			return None
			
		result = self._update_linked_fileds(movieid, 'actor', actors)
		if result == None:
			return None
		
		result = self._update_linked_fileds(movieid, 'director', directors)
		if result == None:
			return None
		
		result = self.updateMovieFilesLink(movieid, files)
		if result == None:
			return None
			
		self.conn.commit()
			
		return movieid
		
		
	def _delete_link(self, movieid, link):
		result = self.conn.execute(
			'DELETE FROM movie_{0}s_link WHERE movie=?'.format(link), (movieid,))
		return result
		
		
	def deleteMovie(self, movieid):
		self._delete_link(movieid, 'genre')
		self._delete_link(movieid, 'actor')
		self._delete_link(movieid, 'tag')
		self._delete_link(movieid, 'file')
		
		result = self.conn.execute(
			'''
			DELETE FROM movies
			WHERE id=?
			''', (movieid,))
			
		self.conn.commit()
			
		return result
		
		
def main():
	'''
		debug stuff
	'''
	library = 'library/'
	db = DbInterface(library + 'metadata.db')
	
	file1 = db.addFile('horror/clearday/disk1.avi')
	file2 = db.addFile('horror/clearday/disk2.avi')
	
	print db.addFileIdToMovie(1, file1)
	print db.addFileIdToMovie(1, file2)
	
	
	print db.addGenreNameToMovie(4, "Sci-Fi")
	print db.addGenreNameToMovie(5, "Sci-Fi")
	print db.addGenreNameToMovie(1, "Horror")
	print db.addGenreNameToMovie(2, "Horror")
	print db.addGenreNameToMovie(3, "Horror")
	
	print db.addActorNameToMovie(1, "Ali Aafee")
	print db.addActorNameToMovie(2, "Ali Aafee")
	print db.addActorNameToMovie(3, "Ali Aafee")
	print db.addActorNameToMovie(4, "Shooga Moosa")
	print db.addActorNameToMovie(5, "Shooga Moosa")
	print db.addActorNameToMovie(1, "Shooga Moosa")
	print db.addActorNameToMovie(2, "Shooga Moosa")
	
	print db.addDirectorNameToMovie(1, "Ali AafeeD")
	print db.addDirectorNameToMovie(2, "Ali AafeeD")
	print db.addDirectorNameToMovie(3, "Ali AafeeD")
	print db.addDirectorNameToMovie(4, "Shooga MoosaD")
	print db.addDirectorNameToMovie(5, "Shooga MoosaD")
	
	print db.addTagNameToMovie(1, "to delete")
	print db.addTagNameToMovie(2, "to delete")
	print db.addTagNameToMovie(3, "to watch")
	print db.addTagNameToMovie(4, "to watch")
	
	#------------------------------------------------------
	print db.addGenreNameToMovie(6, "psycological thriller")
	
	print db.addActorNameToMovie(6, "Guy Pearce")
	print db.addActorNameToMovie(6, "Carrie-Anne Moss")
	print db.addActorNameToMovie(6, "Joe Pantoliano")
	
	print db.addDirectorNameToMovie(6, "Christopher Nolan")
	
	print db.addTagNameToMovie(6, "like")
	#------------------------------------------------------
	
	print "for movie 1"
	
	print db.getMovie(1)
	
	print "genres"
	print db.getGenresByMovieId(1)
		
	print "actors"
	print db.getActorsByMovieId(1)
		
	print "directors"
	print db.getDirectorsByMovieId(1)
		
	print "tags"
	print db.getTagsByMovieId(1)
	
	print "files"
	print db.getFilesByMovieId(1)
	
	print "alltags"
	print db.getAllTagNames()
	
if __name__ == '__main__' :
	main()
		
