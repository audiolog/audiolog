# -*- coding: utf-8 -*-

"""Wrapper around the functionality provided by ReleaseManager.

This file instantiates a ReleaseManager object then invokes its mainloop. If a
ReleaseManagerError is raised, indicating we could not fill an essential field,
then the directory is rejected, otherwise it is accepted."""

import functions
import logger
import Manager
from utils import *

def handleAudio(directoryPath, audioFilePaths):
    """Create and run a ReleaseManager object."""
    
    releaseManager = Manager.ReleaseManager(directoryPath, audioFilePaths)
    try:
        releaseManager.run()
    except Manager.ReleaseManagerError, e:
        logger.log("Attempt to identify and tag audio failed.", "Errors")
        logger.log(str(e), "Errors")
        functions.rejectItem(directoryPath)
    else:
        logger.log("Attempt to identify and tag audio succeeded.", "Successes")
        logger.log("Directory has been sorted successfully.", "Successes")
        functions.acceptItem(directoryPath, releaseManager.getNewPath())
