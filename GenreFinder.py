# -*- coding: utf-8 -*-

"""This file is DONE."""

from AbstractFinder import AbstractReleaseFinder

class GenreFinder(AbstractReleaseFinder):
    """Gatherer of genre data from all available sources."""
        
    fieldName = "genre"
        
    def __init__(self):
        self.getters = [(self.getTag, 1)]               # In AbstractFinder
        # We can some usual getters (like Wikipedia) here...
        
    def do(self, release):
        """Overload do and always return True (successful)."""
        
        AbstractReleaseFinder.do(self, release)
        return True
