"""Wrapper around the functionality provided by release.

This file instantiates a release object then invokes its mainloop. If the
release raises a ReleaseError, indicating we could not fill an essential field,
then the directory is rejected, otherwise it is accepted."""

import functions
import release
from functions import quote
from LogFrame import log

def handleAudio(directoryPath, audioFilePaths):
    """Create and run a Release object."""
    
    album = release.Release(directoryPath, audioFilePaths)
    try:
        album.do()
    except release.ReleaseError:
        log("Attempt to identify and tag audio failed.\n", 3, "Errors")
        functions.rejectItem(directoryPath)
    else:
        log("Attempt to identify and tag audio succeeded.", 3, "Successes")
        log("Directory has been sorted successfully.\n", 2, "Successes")
        functions.acceptItem(directoryPath, album.getNewPath())        