"""Tests for subclasses of IIncludes."""
import unittest
from musicbrainz2.model import Release
from musicbrainz2.webservice import (
	ArtistIncludes, ReleaseIncludes, TrackIncludes, LabelIncludes)


class ArtistIncludesTest(unittest.TestCase):
	def testReleases(self):
		inc1 = ArtistIncludes(aliases=True, releaseRelations=True)
		tags1 = inc1.createIncludeTags()
		tags1.sort()
		self.assertEqual(tags1, ['aliases', 'release-rels'])

		inc2 = ArtistIncludes(releaseRelations=True)
		tags2 = inc2.createIncludeTags()
		tags2.sort()
		self.assertNotEqual(tags2, ['aliases', 'release-rels'])

		inc3 = ArtistIncludes(aliases=True,
			releases=(Release.TYPE_ALBUM, Release.TYPE_OFFICIAL))
		tags3 = inc3.createIncludeTags()
		tags3.sort()
		self.assertEqual(tags3, ['aliases', 'sa-Album', 'sa-Official'])

		inc4 = ArtistIncludes(aliases=True, vaReleases=('Bootleg',))
		tags4 = inc4.createIncludeTags()
		tags4.sort()
		self.assertEqual(tags4, ['aliases', 'va-Bootleg'])

		inc5 = ArtistIncludes(aliases=True,
			vaReleases=(Release.TYPE_BOOTLEG,))
		tags5 = inc5.createIncludeTags()
		tags5.sort()
		self.assertEqual(tags5, ['aliases', 'va-Bootleg'])

	def testTags(self):
		def check(includes_class):
			inc1 = includes_class(tags=True)
			tags1 = inc1.createIncludeTags()
			tags1.sort()
			self.assertEqual(tags1, ['tags'])
		check(ArtistIncludes)
		check(ReleaseIncludes)
		check(TrackIncludes)
		check(LabelIncludes)

# EOF
