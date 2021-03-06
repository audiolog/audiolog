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

import os
import string

try:
    import chardet
except ImportError:
    chardet = None

def translateForFilename(fileName):
    """Replace special filesystem characters with dashes when renaming files.
    
    This would have been nice as str.translate, but unfortunately that doesn't
    work for Unicode.
    
    Note that this function should only be appliced to file names, not file 
    paths because paths should contain these special filesytem characters."""
    
    fileName = fileName.replace("/", "-")
    fileName = fileName.replace("\\", "-")
    fileName = fileName.replace(":", "-")
    return fileName

def ext(filePath, lower=True):
    """Return the extension of the file path or name, lowercased by default."""
    
    extension = os.path.splitext(filePath)[1]
    if lower: 
        extension = extension.lower()
    return extension

def quote(string):
    """Return the string in quotes.
    
    This is used on file names and paths whenever they are shown to the user."""
    
    return '"%s"' % string

def toUnicode(obj, knownEncoding=None):
    """Takes an object and returns a Unicode.
    
    If obj is a str, care is taken to determine the best encoding, using the 
    encoding passed by the caller (if any), an encoding detection algorithm, 
    and the knowledge that UTF-8 is very common."""
    
    if isinstance(obj, unicode):
        return obj
    
    elif isinstance(obj, str):
        encodings = [knownEncoding] if knownEncoding else []
        if chardet:
            detected = chardet.detect(obj)
            if detected["confidence"] > 0.9:
                encodings.extend([detected["encoding"], "UTF-8"])
            else:
                encodings.extend(["UTF-8", detected["encoding"]])
        else:
            encodings.append("UTF-8")
        
        # Try encodings is order of likeliness. If we recieve an error,
        # that encoding probably wasn't correct.
        for enc in encodings:
            try:
                return obj.decode(enc)
            except UnicodeDecodeError:
                pass
            
        # All the encodings failed. (This should happen very rarely).
        # As a last resort, we'll just leave out the broken characters.
        return obj.decode(encodings[0], "ignore")
    
    else:
        return toUnicode(str(obj))
    

def aboutEqual(str1, str2):
    """Return True if the strings are nearly or exactly equal, else False.
    
    To do this we lowercase both strings, strip them of punctuation and
    whitespace, then compare for equality."""
        
    str1 = restrictChars(str1.lower(), whitespace=False, punctuation=False)
    str2 = restrictChars(str2.lower(), whitespace=False, punctuation=False)
    
    return str1 == str2

def restrictChars(s, letters=True, digits=True, whitespace=True, punctuation=True, custom=None):
    """Take a string and return that string stripped of all non-valid characters.
    
    This function is called before queries to MusicBrainz because MB barfs
    when fed weird characters."""
    
    validChars = ""
    if letters: validChars += string.letters
    if digits: validChars += string.digits
    if whitespace: validChars += string.whitespace
    if punctuation: validChars += string.punctuation
    if custom: validChars += custom
    
    return "".join([char for char in s if char in validChars])

def xor(a, b):
    """Return exclusive or of a and b."""

    return (a and (not b)) or (b and (not a))
