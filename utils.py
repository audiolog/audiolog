import os
import string

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

def aboutEqual(str1, str2):
    """Return True if the strings are nearly or exactly equal, else False.
    
    To do this we lowercase both strings, strip them of punctuation and
    whitespace, then compare for equality."""
        
    str1 = restrictChars(str1.lower(), True, True, False, False)
    str2 = restrictChars(str2.lower(), True, True, False, False)
    
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
    
    t = ""
    for ch in s:
        if ch in validChars:
            t += ch
    
    return t

def o_o(a, b=None):
    """Oh really?"""
    
    if a:
        return a
    else:
        return b
