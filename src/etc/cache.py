import os
import cPickle
from functools import wraps
from copy import copy

from logger import log

dirPath = os.path.dirname(__file__)

mbCache = {}
fpCache = {}

def loadCache():
    global mbCache, fpCache
    
    try:
        mb = open(os.path.join(dirPath, "mb.cache"), "r")
        mbCache = cPickle.load(mb)
    except:
        pass
    
    try:
        fp = open(os.path.join(dirPath, "fp.cache"), "r")
        fpCache = cPickle.load(fp)
    except:
        pass

def saveCache():
    global mbCache, fpCache

    mb = open(os.path.join(dirPath, "mb.cache"), "w")
    cPickle.dump(mbCache, mb)
    
    fp = open(os.path.join(dirPath, "fp.cache"), "w")
    cPickle.dump(fpCache, fp)

def memoizeFP(fn):
    global fpCache
    @wraps(fn)
    def decorated_function(path):
        if path in fpCache:
            return fpCache[path]
        else:
            val = fn(path)
            fpCache[path] = val
            return val
    return decorated_function

def memoizeMB(fn):
    """Decorator that makes fn remember and return the results of previous calls.
    
    This helpful because calls to MusicBrainz are time-consuming (at least one 
    second), so not actually have to make that call saves us a lot of time."""
    
    #global mbCache
    mbCache = {}
    stats = {"hits": 0,
             "calls": 0}
    
    def hashDict(d):
        return hash(tuple(sorted(d.items())))
    
    def fixPostFilter(post):
        d = copy(post)
        if "tracks" in d:
            if (hasattr(d["tracks"][0], "metadata") and 
                "title" in d["tracks"][0].metadata):
                d["tracks"] = str([t.metadata["title"] for t in d["tracks"]])
            else:
                del d["tracks"]
        return d
    
    @wraps(fn)
    def decoratedFunction(f, m, pre, post):
        stats["calls"] = stats["calls"] + 1
        
        hashable = True
        try:
            cargs = f, m, hashDict(pre), hashDict(fixPostFilter(post))
        except Exception, e:
            hashable = False
            log("Not hashable: %s" % e)
            
        if hashable and cargs in mbCache:
            stats["hits"] = stats["hits"] + 1
            log("Hit MusicBrainz cache (%d hits of %d tries)." % (stats["hits"], stats["calls"]))
            return mbCache[cargs]
        else:
            log("Missed MusicBrainz cache (%d hits of %d tries)." % (stats["hits"], stats["calls"]))
            val = fn(f, m, pre, post)
            if hashable:
                mbCache[cargs] = val
            return val
    return decoratedFunction
