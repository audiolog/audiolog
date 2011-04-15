# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
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

from etc.logger import log, logfn, logSection
from AbstractFinder import AbstractReleaseFinder

class GenreFinder(AbstractReleaseFinder):
    """Gatherer of genre data from all available sources."""
        
    fieldName = "genre"
        
    def __init__(self):
        self.getters = [#(self.getMusicDNS, 1),
                        (self.getTag, 1)]               # In AbstractFinder
        # We can add some unusual getters (like Wikipedia) here...
        
    def run(self, release):
        """Overload run and always return True (successful)."""
        
        AbstractReleaseFinder.run(self, release)
        return True
    
    @logfn("Looking in MusicDNS results.")
    def getMusicDNS(self, track):
        """Return genre if MusicDNS provided one."""

        return track.musicDNS["genre"]
