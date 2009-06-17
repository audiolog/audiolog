#! /usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Search for a track by title (and optionally by artist name).
#
# Usage:
#	python findtrack.py 'track name' ['artist name']
#
# $Id: findtrack.py 201 2006-03-27 14:43:13Z matt $
#
import sys
import logging
import musicbrainz2.webservice as ws

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
	

if len(sys.argv) < 2:
	print "Usage: findtrack.py 'track name' ['artist name']"
	sys.exit(1)

if len(sys.argv) > 2:
	artistName = sys.argv[2]
else:
	artistName = None

q = ws.Query()

try:
	f = ws.TrackFilter(puid=sys.argv[1], artistName=artistName)
	results = q.getTracks(f)
except WebServiceError, e:
	print 'Error:', e
	sys.exit(1)


for result in results:
	track = result.track
	print "Score     :", result.score
	print "Id        :", track.id
	print "Title     :", track.title
	print "Artist    :", track.artist.name
	print "Duration  :", track.duration
	
	for release in track.releases:
		print "Album     :", release.title
		print "Track     :", release.tracksOffset + 1 # Offset 0 means track 1
	
	#track = q.getTrackById(track.id, ws.TrackIncludes(artist=True, releases=True, releaseRelations=True, trackRelations=True))
	#print vars(track)
	#for release in track.releases:
		#print vars(release)
	
	print

# EOF
