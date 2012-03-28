"""High-level interface for accessing MusicBrainz.

==Illustration of MusicBrainz Process==

                 askMB                     |
                   |                       |
            constructFilter                |
              |          |                 |
    findExactMatch    findFuzzyMatch       |
              |          |                 |
              executeQuery                 |
                   |                       |
              getFunction                Time
                   |                       |
            translateParams                |
                   |                       |
               contactMB                   |
                   |                       |
           requireDesiredInfo              |
                   |                       |
           postProcessResults              |
                   |                       |
              parseResults                 V
"""

import pprint
import time

import musicbrainzngs as mb

p = pprint.pprint

mb.set_useragent("Audiolog", "0.3.1", "www.example.com")

def log(*args):
    print args
    
def quote(s): 
    return "%s" % s
    
def toUnicode(s):
    return s
    
def filterToOne(fn, seq):
    return filter(fn, seq) or [seq[0]]
    


@logfn("Matching the string {quote(match)} on {field}.")
def findExactMatch(field, match, track, preFilter, postFilter):
    """Non-fuzzy matching is easy..."""
    
    return executeQuery(field, match, preFilter, postFilter)


@logfn("Fuzzily matching the string {quote(match)} on {field}.")
def findFuzzyMatch(field, match, track, preFilter, postFilter):
    """Fuzzily match unreliable data (from tags and filename) to MusicBrainz.

    Tags and filenames especially may contain special characters or extraneous
    data which will make a MusicBrainz search fail. This function removes 
    special characters and, if the full string does not match, splits it
    based on a delimiters list and tries the substrings.

    Example:

    Filename: "2000 -*- The Better Life (Advance) -[[EAK-group]]-"
    Initial search for full string fails. String is broken into substrings.
    Substrings: "2000", "The Better Life", "Advance", "EAK", "group"
    Without any other filters "The Better Life" and "Advance" will both match
    and unable to choose one over the other, we will fail.
    With a filter (like the artist or date) then only "The Better Life" will
    match and the search will succeed.
    
    Fuzzy matching is only used for artist, release and title fields, because
    these are the only fields with strings to fuzzily match against."""
    
    # TODO: This can be revived after we create a 'similar?' function.
    """if isinstance(match, FilepathString):
        log("Splitting path into directory and file name, then trying each.")
        dirName, fileName = os.path.split(match)
        
        dirResult = executeQuery(field, dirName, preFilter, postFilter)
        if dirResult:
            # We won't look to see if the filename matches, because even if it
            # did, the directory generally has better odds of containing 
            # an artist or release anyway. (We know we are looking for an 
            # artist or release, because only requests for those fields pass in 
            # a filepath. Track title requests just pass in the file name.)
            return dirResult
        
        fileResult = executeQuery(field, fileName, preFilter, postFilter)
        if fileResult:
            return fileResult
    
    else:
        result = executeQuery(field, match, preFilter, postFilter)
        if result:
            return result"""
    
    delimiters = r"[/()\-~+_\[\]\{\}*]"
    substrings = [string.strip() for string in re.split(delimiters, match)
                  if string.strip()]
    
    log("MB did not find a match for the full string.")
    log("Searching for a match in substrings.")
    log("Substrings: %s\n" % substrings)

    results = [executeQuery(field, s, preFilter, postFilter), s for s in substrings]
    sources = dict([(r, s) for r, s in results if r])
    matches = set(sources.keys())
    
    whatFromWhere = {result, substring for substring in substrings
                     for result in [executeQuery(field, substring, preFilter, postFilter)]
                     if result}
                    

    matches = set()
    whatFromWhere = {}
    for substring in substrings:
        result = executeQuery(field, substring, preFilter, postFilter)
        if result:
            whatFromWhere[result] = substring
            matches.add(result)
    
    if len(matches) > 1:
        # If we have more than one result, attempt to remove matches which 
        # probably are not correct until we have only one match left or we run
        # out of methods for removing bogus results.
        # Potentially bogus results are removed in the order of the likelihood that
        # they are incorrect.
        #
        # The current filters (in order):
        #   - result is very different from substring
        #   - result looks like tracknumber or year
        #   - result is digits
        #   - result is (about) equal to already known artist, release or title
        #   - substring was digits
        
        # TODO:
        #   Order tests correctly.
        #   Use difflib in addition to aboutEqual.
        #   Use two levels of delimiters.
        #   Add filter to remove results which are (about) equal to one another.
        # 
        #   Order #1 (filter all results, filter all substring)
        #   - result looks like tracknumber or year
        #   - result is digits
        #   - result is (about) equal to already known artist, release or title
        #
        #   - substring looked like tracknumber or year
        #   - substring was digits
        #   - substring was (about) equal artist, release, title
        #
        #   Order #2 (filter result then substring, then next filter)
        #   - result looks like tracknumber or year
        #   - substring looked like tracknumber or year    
        #
        #   - result is digits
        #   - substring was digits    
        #
        #   - result is (about) equal to already known artist, release or title
        #   - substring was ... artist, release, title
    
        log("Multiple substrings matched: %s" % matches)
        log("Removing matches which are probably wrong.")
        
        # Remove matches which are either a tracknumber or a year.
        # Tracknumbers are identified by being one or two digits (possibly with
        # leading zero) under 99.
        # Years are four consecutive digits between 1600 and current year + 1.
        for match in matches.copy():
            if len(matches) > 1:        
                if match.isdigit():
                    num = int(match)
                    if functions.isTrackNumber(num) or functions.isDate(num):
                        matches.remove(match)
            else:
                break
        
        # Remove matches which are just digits.
        for match in matches.copy():
            if len(matches) > 1:        
                if match.isdigit():
                    matches.remove(match)
            else:
                break
        
        # Remove results which came from strings of digits.
        for match in matches.copy():
            if len(matches) > 1:
                if whatFromWhere[match].isdigit():
                    matches.remove(match)
            else:
                break
        
        # If we still have more than one result, than we will remove values that
        # are known to be correct for a different field. In particular, we'll
        # look at the artist, album and title fields and remove matches
        # equivalent to those fields - in that order.
        relatedFields = ["artist", "release", "title"]
        relatedFields.remove(field)
        relatedData = []
        for field in relatedFields:
            if field in track.metadata:
                relatedData.append(track.metadata[field])
        
        # Remove matches which are the same as the already known artist, 
        # release or title intelligently.
        def equal(match, datum):
            return match == datum
        
        def inside(match, datum):
            return datum.lower() in match.lower()
        
        if len(matches) > 1:
            for datum in relatedData:
                for equivalenceFunc in (equal, aboutEqual, inside):
                    for match in matches.copy():
                        if len(matches) > 1:
                            if equivalenceFunc(match, datum):
                                matches.remove(match)
                        else:
                            break
                            
        
        # Remove matches which are signficantly different than the substring
        # they came from.
        for match in matches.copy():
            if len(matches) > 1:
                diff = difflib.get_close_matches(whatFromWhere[match], [match])
                if not diff:
                    matches.remove(match)
            else:
                break
    
    if len(matches) == 1:
        match = matches.pop()
        log("MB matched a string to a %s: %s" % (field, quote(match)))
        return match
    else:
        log("%d substrings matched." % len(matches))
        if matches:
            log("Unable to select between them.")
            log("Filtered matches: %s" % matches)
        log("Fuzzy matching failed.")
        return u""


#////////////// Moved, not changed
#@logfn("Querying MusicBrainz.")
def executeQuery(field, params, preFilter, postFilter):  # FIXME; pre and post filters?
    """Runs a MusicBrainz query from start to finish.
    
    Starts with finding which query function to use and finishing with
    extracting the correct data."""

    queryFunction = getMBFunction(field, params)
    queryParams = translateParams(field, params)
    
    log("Field:  %s" % field)
    if preFilter:  log("Pre:    %s" % preFilter)
    if postFilter: log("Post:   %s" % postFilter)
    if match:      log("Match:  %s" % match)
    
    finalResult = None
    results = contactMB(queryFunction, queryParams)
    #results = requireDesiredInfo(field, results)
    
    if results:
        result = postProcessResults(results, field, **postFilter) # TODO: This will probably be necessary.
        if result:
            finalResult = parseResult(field, queryFunction, result)
    
    log("Result: %s\n" % finalResult)
    return finalResult
#////////////// 


#//////////// Needs to be tested
def getMBFunction(field, params):
    """Return proper query function & filter based on field & whether we are matching."""

    functions = {
        "artist"     : mb.search_artists,
        "release"    : mb.search_release_groups,
        "date"       : mb.search_release_groups,
        "tracktotal" : mb.search_release_groups,
        "title"      : mb.search_recordings,
        "tracknumber": mb.search_recordings
    }

    f = functions[field]
    
    # If seeking artist, with
    #   only an artist name - mb.search_artists
    #   only a release name - mb.search_release_groups
    #   artist and release  - mb.search_release_groups, using artist in params
    if field == "artist" and "release" in params:
        f = mb.search_release_groups
        
    # TODO: This one too? Document it.
    # If looking for the track title, 
    #if field == "title" and not "title" in params:
    #    
    #    queryFilter = mbws.ReleaseFilter
    #    queryFunction = query.getReleases
    
    return f
#///////////////


#@logfn("Accessing MusicBrainz web service.")
def contactMB(func, params, depth=0):
    """Robustly connect to MusicBrainz through the MB WebService.
    
    Params is a dictionary."""

    time.sleep(depth)

    try:
        result = func(**params)
    except Exception, e:
        if depth < 3:
            log("Received error: %s." % quote(str(e)))
            log("Waiting, then trying again.")
            result = contactMB(func, params, depth+1)
        else:
            log("Failed 3 times. Returning None.")
            result = None
    
    return result

#p(contactMB(mb.search_artists, {"query": "Pink Floyd"}))
#p(contactMB(mb.search_release_groups, {"query": "The Dark Side of the Moon", "artist": "Pink Floyd"}))
#p(contactMB(mb.get_release_group_by_id, {"id": "f5093c06-23e3-404f-aeaa-40f72885ee3a"}))

#p(contactMB(mb.search_recordings, {"artist": "Pink Floyd", "dur": "1412000"}))
#=> Should return "Echoes" -- but it doesn't
#p(contactMB(mb.search_recordings, {"release": "The Dark Side of the Moon", "tnum": "3"}))
#=> Should return "Time" -- but it doesn't
#p(contactMB(mb.search_releases, {"query": "The Dark Side of the Moon", "artist": "Pink Floyd"}))
#p(contactMB(mb.search_recordings, {"query": "Time", "release": "The Dark Side of the Moon", "artist": "Pink Floyd"}))
#p(contactMB(mb.get_release_by_id, {"id": "ac496d60-9b3a-497c-b650-1810f0b730bf", "includes": ["recordings"]}))
#p(contactMB(mb.get_recording_by_id, {"id": "b9e991d3-ccf6-46e2-aa87-590f7b74ac52", "includes": ["releases", "release-rels"]}, ))


#////////////// Changed, needs full testing
def translateParams(field, params):
    """Construct params to MB standards then instantiate filter with params."""
            
    newParams = {}
    for k, v in params.items():
        if field == k:
            newParams["query"] = v
        elif field == "track":  # FIXME: title?
            newParams["recording"] = v
        else:
            newParams[k] = v
    
    # FIXME: Other translations?
    
    return newParams
#///////////
#p(translateParams("artist", {"artist": "Pink Flooyd", "release": "The Dark Side of the Moon"}))
#=> {"query": "Pink Flooyd", "release": "The Dark Side of the Moon"}


def postProcessResults(field, fn, result, date=None, tracknumber=None, tracktotal=None, titles=None):
    """Apply the postquery filter to the result returned by the MB query."""
    
    if fn == mb.search_release_group:
        # There are two levels of releases to look at. The outer level is 
        # release groups, each of which contains releases. We want to deal with
        # the releases themselves but to iterate through every release in every
        # group would be too costly. Instead we iterate through the inner 
        # releases only on high score results, while looking at only the
        # earliest release on low score results. 
        releases = []
        for releaseGroup in result["release-group-list"]:
            if releaseGroup["ext:score"] > 70:
                for release in releaseGroup["release-list"]:
                    r = mb.get_release_by_id(release["id"], ["recordings", "release-groups"])
                    # XXX: This assumes that releases without dates are always 
                    # incorrect. We might want to reconsider that.
                    if "date" in r["release"]:
                        releases.append(r)
            else:
                rg = mb.get_release_group_by_id(releaseGroup["id"], ["releases"])
                earliestDate = rg["release-group"].get("first-release-date")
                if not earliestDate:
                    log("Discarding release group with no first release date.")
                    continue
                
                for release in rg["release-group"]["release-list"]:
                    if release.get("date") == earliestDate:
                        releases.append(mb.get_release_by_id(release["id"], 
                                        ["recordings", "release-groups"]))
                        break
        
        if date:
            releases = [release for release in releases
                        if release["release"]["date"].split("-")[0] == date]
        
        if tracktotal:
            releases = [release for release in releases
                        if len(release["release"]["medium-list"][0]["track-list"]) == int(tracktotal)]  # FIXME: Only looks at first disc
        
        if titles:
            releases, oldReleases = [], releases
            for release in oldReleases:
                for title, track in zip(titles, release["release"]["medium-list"][0]["track-list"]):
                    if not aboutEqual(title, track["recording"]["title"]):      # FIXME: aboutEqual ain't very smart
                        break
                else:
                    releases.append(release)
        
        if len(releases) > 1:
            # We applied the pre and post filters and we still have more than 1
            # result. Now we apply intelligence.
            tn     = lambda release: len(release["release"]["medium-list"][0]["track-list"]) >= tracknumber
            status = lambda release: release["release"]["status"] == "Official"
            type   = lambda release: release["release"]["release-group"]["type"] == "Album"
            # TODO: Any more criteria? Potentiall check that pre-filter worked.
                        
            filters = (tn, status, type) if tracknumber else (status, type)
            for f in filters:
                releases = filterToOne(f, releases)
                if len(releases) == 1:
                    break
        
        # The releases are in order of declining score (by release group, not by
        # release). So we'll take the first remaining element, which has the
        # highest score. After this, we have one release.
        # TODO: Make sure this isn't empty.
        release = releases[0]
        
        if tracknumber:
            # We have a release and track number and we want a track title.
            # The recordings that result from this have: id, title, (sometimes) length
            return release["medium-list"][0]["track-list"][tracknumber-1]["recording"]
        
        return release
    
    elif fn == mb.search_recordings:
        # This returns a "track in context" which has this form:
        # {'position': '4',
        #  'recording': {'id': '8dfd6d32-b8aa-4abe-80ee-27c358733e91',
        #                'title': 'The Great Gig in the Sky'}}
        # parseResult depends on this form to retrieve the tracknumber and title.
        for recording in result["recording-list"]:
            for release in recording["release-list"]:
                r = mb.get_release_by_id(release["id"], ["recordings", "release-groups"])
                for medium in r["release"]["medium-list"]:
                    for track in medium["track-list"]:
                        if track["recording"]["id"] == recording["id"]:
                            if tracknumber:
                                if track["position"].rjust(2, "0") == tracknumber:
                                    return track
                            else:
                                return track
            return None
        
    elif fn == mb.search_artists:
        # TODO: Way to perfer between multiple options?
        return result["artist-list"][0]



#////////////// Changed, needs full testing
#@logfn("Parsing MB results.")
def parseResult(field, fn, result):
    """Pull from the result the data field and return it.
    
    We have successfully conquered all of the dungeons. 
    Below is the key to the final castle."""
    
    finalResult = None
    
    if fn == mb.search_artists:
        finalResult = result["name"]
    
    elif fn == mb.search_release_groups:
        if field == "release":
            finalResult = result["title"]
            
        elif field == "artist":
            finalResult = result["artist-credit-phrase"]
            
        elif field == "date":
            subresult = mb.get_release_by_id(result["id"], ["recordings"])
            finalResult = subresult["release-group"]["first-release-date"].split("-")[0]
            
        elif field == "tracktotal":
            subresult = mb.get_release_by_id(result["id"], ["recordings"])
            finalResult = len(subresult["release"]["medium-list"][0]["track-list"])
    
    # postProcessResult provides a "track in context" with position and recording.
    elif fn == mb.search_recordings:
        if field == "title":
            finalResult = result["recording"]["title"]
    
        elif field == "tracknumber":
            finalResult = result["position"].rjust(2, "0")
    
    if not finalResult:
        log("Something went wrong in parseResult. "
            "Result type: %s  field: %s" % (fn.__name__, field))
    
    return toUnicode(finalResult)
#\\\\\\\\\\\\\\  Needs testing


class FilepathString(unicode):
    """Marks a string as being a filepath.
    
    This class is a hack. Its purpose it to allow the Finders to mark a string
    as being a filepath (as opposed to a tag value or a filename) because later 
    the MusicBrainz fuzzy matcher treats these differently. Explicitly passing 
    this metadata would muck up multiple function interfaces, hence this class."""
    
    pass
