from tagging:

    def printAudioInfo(filePath):
        """Takes a path to an OGG or MP3 and print the info we can find"""
        
        audioFile = openAudioFile(filePath)
        log("Info for " + quote(filePath) + ":", 
        for key in audioFile:
            print key
            print "\t", audioFile[key]
        print "Length:\n\t", audioFile.info.length
        print "Bitrate:\n\t", audioFile.info.bitrate
    
from traverse:
    
    # Display subdirectories
    if subdirectoryPaths:
        log("\tsubdirectoryPaths", "Debugging")
        for subdirectoryPath in subdirectoryPaths:
            log("\t\t" + quote(subdirectoryPath), "Debugging")
            
            
    # Display files
    if subdirectoryPaths:
        log("\nBack in " + quote(directoryPath), "Debugging")
            
    if filePaths:
        log("\tfilePaths", "Debugging")
        for filePath in filePaths:
            log("\t\t" + quote(filePath), "Debugging")
        
        log("\tfilePathsByType", "Debugging")
        for fileType in filePathsByType:
            log("\t\t" + fileType, "Debugging")
            for filePath in filePathsByType[fileType]:
                log("\t\t\t" + quote(filePath), "Debugging")
                

from extract:

def makeDestDirectory(archivePath):
    directoryPath = os.path.splitext(archivePath)[0]
    if not os.path.exists(directoryPath): os.mkdir(directoryPath)
    return directoryPath

def unzip(archivePath, destDirectoryPath):
    return os.system('unzip "' + archivePath + '" -d "' + destDirectoryPath + '"')

def unrar(archivePath, destDirectoryPath):
    return os.system('unrar x "' + archivePath + '" "' + destDirectoryPath + '"')
    
def untar(archivePath, destDirectoryPath):
    return os.system('tar -xf "' + archivePath + '" "' + destDirectoryPath + '"')
    
def ungz(archivePath, destDirectoryPath):
    return os.system('tar -zxf "' + archivePath + '" "' + destDirectoryPath + '"')
    
def unbz2(archivePath, destDirectoryPath):
    return os.system('tar -jxf "' + archivePath + '" "' + destDirectoryPath + '"')

def unace(archivePath, destDirectoryPath):
    return os.system('unace x -y "' + archivePath + '" "' + destDirectoryPath + '/"') # unace is fucked up...

def un7z(archivePath, destDirectoryPath):
    return -1

def defaultExtractor(archivePath, destDirectoryPath):
    return -1

extractorFunctions = {".zip": unzip, ".rar": unrar, ".tar": untar, ".gz": ungz, 
                        ".bz2": unbz2, ".ace": unace, ".7z": un7z}


from convert:

def convertWAV(filePath):
    command = 'oggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "%s.wav"' % filePath
    log(command, "Commands")
    return os.system(command)

def convertFLAC(filePath):
    command = 'oggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "%s.flac"' % filePath
    log(command, "Commands")
    return os.system(command)

def convertAPE(filePath):
    command = 'mac "$$.ape" "$$.wav" -d; \noggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "$$.wav"'
    command = command.replace("$$", filePath)
    log(command, "Commands")
    return os.system(command)

def convertMPC(filePath):
    command = 'mpc123 -w "$$.wav" "$$.mpc"; \noggenc -q ' + str(configuration.ENCODING_QUALITY["MEDIUM"]) + ' "$$.wav"'
    command = command.replace("$$", filePath)
    log(command, "Commands")
    return os.system(command)

def defaultConvertor(filePath):
    return
    
convertorFunctions = {".ape": convertAPE, ".flac": convertFLAC, ".wav": convertWAV, ".mpc": convertMPC}



from getters.getFilename release:
        # Get a list of every possible release title
        results = re.split(delimiters, containingDirName) 
        for i in range(len(results)):
            results[i] = results[i].strip()
        results = [result for result in results if result] # Remove empty entires
        
        releases = []
        query = mb.Query()
        
        for result in results:
            params = mb.ReleaseFilter(title = result, artistName = track.track["artist"], limit = 1)
            result = getMB(query.getReleases, params)
            
            if len(result) > 0: # If result is found in MB
                releases.append(result[0].getRelease().getTitle())
        
        if len(releases) == 1: # We found a match
            return releases[0]
        elif len(releases) == 2: # We found a match, but one may be a false positive
            if functions.aboutEqual(track.track["artist"], releases[0]):
                print "Returning", releases[1]
                return releases[1] # Return the one that isn't self-titled
            elif functions.aboutEqual(track.track["artist"], releases[1]):
                print "Returning", releases[0]
                return releases[0]
            else:
                print "Two different non-artist release names found"
                return ""
        else:
            print len(releases), "possible releases found in filename."
            if releases:
                print "\tPossible releases:", releases
            print "Unable to determine a release from filename."
            return ""

from getters.getFilename title:
        # Get a list of every possible release title
        results = re.split(delimiters, baseName) 
        for i in range(len(results)):
            results[i] = results[i].strip()
        results = [result for result in results if result] # Remove empty entires
        
        titles = []
        query = mb.Query()
        
        for result in results:
            params = mb.TrackFilter(title = result, artistName = track.track["artist"], releaseTitle = track.track["release"], limit = 1)
            result = getMB(query.getTracks, params)
        
            if len(result) > 0:
                titles.append(result[0].getTrack().getTitle())
        
        if len(titles) == 1: # We found a match
            return titles[0]
        elif len(titles) == 2: # We found a match, but one may be a false positive
            if functions.aboutEqual(track.track["artist"], titles[0]):
                print "Returning", titles[1]
                return titles[1] # Return the one that isn't self-titled
            elif functions.aboutEqual(track.track["artist"], titles[1]):
                print "Returning", titles[0]
                return titles[0]
            else:
                print "Two different non-artist titles found"
                return ""
        else:
            print len(titles), "possible titles found in filename."
            if titles:
                print "\tPossible titles:", titles
            print "Unable to determine a title from filename."
            return ""

from getters:


def getMB(track, field, filt):
    """Construct and execute a MusicBrainz query."""

    query = mb.Query()
    
    if field == "artist":
        params = mb.ArtistFilter(name = filt, limit = 1)
        result = getMB(query.getArtists, params)
        
        if len(result) > 0:
            return result[0].getArtist().getName()
        else:
            return ""
        
    elif field == "release":        
        params = mb.ReleaseFilter(title = filt, artistName = track.track["artist"], limit = 1)
        result = getMB(query.getReleases, params)
        
        if len(result) > 0:
            return result[0].getRelease().getTitle()
        else:
            return ""
    
    elif field == "date":
        params = mb.ReleaseFilter(title = track.track["release"], artistName = track.track["artist"], limit = 1)
        result = getMB(query.getReleases, params)
        
        if len(result) > 0:
            if result[0].getRelease().getEarliestReleaseDate():
                return result[0].getRelease().getEarliestReleaseDate().split("-")[0]
            else:
                return ""
        else:
            return ""
    
    elif field == "tracktotal":
        params = mb.ReleaseFilter(title = track.track["release"], artistName = track.track["artist"], limit = 1)
        result = getMB(query.getReleases, params)
        
        if len(result) > 0:
            tracktotal = result[0].getRelease().getTracksCount()
            return unicode(tracktotal).rjust(2, u"0")
        else:
            return ""
    
    elif field == "title":
        params = mb.TrackFilter(title = tag, artistName = track.track["artist"], releaseTitle = track.track["release"])
        result = getMB(query.getTracks, params)
        
        if len(result) > 0:
            return result[0].getTrack().getTitle()
        else:
            return ""
    
    elif field == "tracknumber":
        params = mb.TrackFilter(title = track.track["title"], artistName = track.track["artist"], releaseTitle = track.track["release"])
        result = getMB(query.getTracks, params)
        
        if len(result) > 0:
            tracknumber = result[0].getTrack().getReleases()[0].getTracksOffset() + 1  # Track numbers are zero-indexed.
            return unicode(tracknumber).rjust(2, u"0") 
        else:
            return ""