# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
#  Copyright © 2011  Matt Hubert <matt@cfxnetworks.com> 
#                    Robert Nagle <rjn945@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Generate audio fingerprints using OFA; search for matches in MusicDNS."""

import time
import urllib
try:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import iterparse
    from xml.etree.ElementPath import Path
except ImportError:
    from elementtree import ElementTree
    from elementtree.ElementTree import iterparse
    from elementtree.ElementPath import Path

import musicdns

from etc.utils import *
from etc.cache import memoizeFP
from etc.logger import log, logfn, logSection

def lookup_fingerprint_metadata(fingerprint, duration, musicdns_key, **opt):
    """Given the fingerprint of an audio file, lookup metadata from MusicDNS.
    
    This function is extremely similar to (and uses code from) the 
    lookup_fingerprint function provide by pyofa. This unfortunate duplication
    is necessary because that function only returns a PUID, not the associated
    metadata. I'm open to solutions that involve less duplication, including
    submitting a patch to pyofa."""

    req = '/ofa/1/track'
    url = 'http://%s:%d%s' % (musicdns.musicdns_host, musicdns.musicdns_port, req)
    postargs = dict(

        # Identification.
        cid=musicdns_key,
        cvr="pyofa/%s" % musicdns.__version__,
        
        # The given fingerprint.
        fpt=fingerprint,

        # These are required by the license agreement, to help fill out the
        # MusicDNS database.
        art=opt.pop('art', ''),
        ttl='02-Track_02',
        alb=opt.pop('alb', ''),
        tnm=opt.pop('tnm', ''),  # track no.
        gnr=opt.pop('gnr', ''),
        yrr=opt.pop('yrr', ''),
        brt=opt.pop('brt', ''),
        fmt='', ##MPEG-1 Layer 3',
        dur=str(duration),

        # Return the metadata?
        rmd='2',

        # FIXME: What are those? Found from Picard, not in protocol docs.
        ## rmt='0',
        ## lkt='1',
        )

    data = urllib.urlencode(postargs)
    f = urllib.urlopen(url, data)

    # Parse the response.
    tree = ElementTree.parse(f)
    musicdns.sanitize_tree(tree) 
    
    metadata = {}
    
    el = tree.find('//puid')
    metadata["puid"] = el.attrib['id'] if el is not None else None
    
    el = tree.find('//artist/name')
    metadata["artist"] = el.text if el is not None else None
    
    el = tree.find('//title')
    metadata["title"] = el.text if el is not None else None
    
    el = tree.find('//genre/name')
    metadata["genre"] = el.text if el is not None else None
    
    el = tree.find('//first-release-date')
    metadata["year"] = el.text if el is not None else None

    return metadata

@memoizeFP
def askMusicDNS(filePath):
    """Fingerprint audio file; look for match in MusicDNS database.
    
    filePath must point to an audio file with a supported format (MP3 or OGG).

    This functions uses OFA (the Open Fingerprint Architecture) accessed via 
    the pyofa wrapper to generate an audio fingerprint for the given file.
    Then it queries MusicDNS to see if the fingerprint matches a known song.
    If so, it returns a dictionary of metadata including the PUID and (if found) 
    the artist, song title, genre and year of first release.    . 
    If the process fails for any reason, it returns None."""
    
    fileName = os.path.basename(filePath)
    #try:
    filePath = toUnicode(filePath).encode("UTF-8")
    #except:
    #    log("Filepaths to be fingerprinted must contain only ASCII chars.")
    #    log("Bad filepath: %s" % filePath)
    #    return None
    
    log("Generating an audio fingerprint for %s." % quote(fileName))
    try:
        fingerprint, duration = musicdns.create_fingerprint(filePath)
    except IOError:
        log("%s is not a supported filetype for audio fingerprinting." % 
            quote(fileName))
        return None
    
    log("Searching for a match in the MusicDNS database.")
    try:
        metadata = lookup_fingerprint_metadata(fingerprint, duration, 
                                               "a66a78b0401f53189d5dd98a5c89f5a9")
    except:
        log("Unable to search for MusicDNS match.")
        return None
        
    if metadata["puid"]:
        log("MusicDNS found a match.")
    else:
        log("MusicDNS failed to find a match.") 
        
    return metadata
