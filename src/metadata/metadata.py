# -*- coding: utf-8 -*-

#  Azul Music Organizer
#  Copyright © 2009  Matt Hubert <matt@cfxnetworks.com> and Robert Nagle <rjn945@gmail.com>
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

"""Wrapper around the functionality provided by ReleaseManager.

This file instantiates a ReleaseManager object then invokes its mainloop. If a
ReleaseManagerError is raised, indicating we could not fill an essential field,
then the directory is rejected, otherwise it is accepted."""

import Manager

import etc.functions
import etc.logger
from etc.utils import *

def handleMetadata(directoryPath, audioFilePaths):
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
