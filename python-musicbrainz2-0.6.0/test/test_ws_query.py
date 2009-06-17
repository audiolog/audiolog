"""Tests for webservice.Query."""
import unittest
from musicbrainz2.model import Tag
from musicbrainz2.webservice import Query, IWebService


class FakeWebService(IWebService):

	def __init__(self):
		self.data = []

	def post(self, entity, id_, data, version='1'):
		self.data.append((entity, id_, data, version))


class QueryTest(unittest.TestCase):

	def testSubmitUserTags(self):
		ws = FakeWebService()
		q = Query(ws)
		t1 = [u"foo", u"bar", u"f\u014do"]
		t2 = [Tag(u"foo"), Tag(u"bar"), Tag(u"f\u014do")]

		prefix = 'http://musicbrainz.org/artist/'
		uri = prefix + 'c0b2500e-0cef-4130-869d-732b23ed9df5'

		q.submitUserTags(uri, t1)
		q.submitUserTags(uri, t2)

		self.assertEquals(len(ws.data), 2)
		self.assertEquals(ws.data[0], ws.data[1])

# EOF
