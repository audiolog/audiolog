import os
import json
import sqlite3
import StringIO
from time import sleep

from logger import log
from utils import toUnicode

dbConn = None
cursor = None

class Stats(object):
    """Wrapper around some ints."""
    
    def __init__(self):
        self.hits = 0
        self.calls = 0
        
    def __str__(self):
        return "%d hits of %d calls" % (self.hits, self.calls)


def loadCacheDB():
    global dbConn, cursor
    
    dbPath = os.path.expanduser(os.path.join("~", "cache.sqlite3"))
    exists = os.path.exists(dbPath)
    dbConn = sqlite3.connect(dbPath)
    cursor = dbConn.cursor()
    
    if not exists:
        cursor.execute("create table fp (path text, result text)")
        cursor.execute("create table mb (url text, result text)")
        
def saveCacheDB():
    if dbConn:
        dbConn.commit()

        
def memoizeFP(fn):
    global dbConn, cursor
    
    def dbMemoizedFunction(path):
        cursor.execute("select result from fp where path=?", (path,))
        result = cursor.fetchone()
        
        if result:
            return json.loads(result[0])
        else:
            result = fn(path)
            cursor.execute("insert into fp values (?, ?)", (path, json.dumps(result)))
            return result
        
    # This dispatch function is necessary because the status of the database
    # connection can change while the program is running.
    def dispatchFunction(path):
        if dbConn:
            return dbMemoizedFunction(path)
        else:
            return fn(path)

    return dispatchFunction

def memoizeMB(fn):
    """Decorator that makes fn remember and return the results of previous calls.
    
    This is helpful because calls to MusicBrainz are time-consuming (at least 
    one second), so not actually have to make that call saves us a lot of time."""
    
    global dbConn, cursor
    
    stats = Stats()
    
    cache = {}
    def dictMemoizedFunction(self, url):
        stats.calls += 1
        if url in cache:
            stats.hits += 1
            #log("Hit MusicBrainz cache (%s)." % stats)
            text = cache[url]
        else:
            #log("Missed MusicBrainz cache (%s)." % stats)
            result = fn(self, url)
            text = result.read()
            cache[url] = text
        return StringIO.StringIO(text)  # fn must return a file-like object
    
    def dbMemoizedFunction(self, url):
        stats.calls += 1
        cursor.execute("select result from mb where url=?", (toUnicode(url),))
        result = cursor.fetchone()
        
        if result:
            stats.hits += 1
            #log("Hit MusicBrainz DB cache (%s)." % stats)
            text = result[0].encode("UTF-8")
        else:
            #log("Missed MusicBrainz DB cache (%s)." % stats)
            sleep(1)
            result = fn(self, url)
            text = result.read()
            cursor.execute("insert into mb values (?, ?)", (toUnicode(url), toUnicode(text)))
        return StringIO.StringIO(text)   # fn must return a file-like object
    
    # This dispatch function is necessary because the status of the database
    # connection can change while the program is running.
    def dispatchFunction(self, url):
        if dbConn:
            return dbMemoizedFunction(self, url)
        else:
            return dictMemoizedFunction(self, url)

    return dispatchFunction 
    
