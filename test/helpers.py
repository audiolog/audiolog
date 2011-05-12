"""This files allows us to remove dependencies on Audiolog."""

import os

import chardet

import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis as Ogg
from mutagen.easyid3 import EasyID3

def toUnicode(obj, knownEncoding=None):
    """Takes an object and returns a Unicode.
    
    If obj is a str, care is taken to determine the best encoding, using the 
    encoding passed by the caller (if any), an encoding detection algorithm, 
    and the knowledge that UTF-8 is very common."""
    
    if isinstance(obj, unicode):
        return obj
    
    elif isinstance(obj, str):
        encodings = [knownEncoding] if knownEncoding else []
        detected = chardet.detect(obj)
        if detected["confidence"] > 0.9:
            encodings.extend([detected["encoding"], "UTF-8"])
        else:
            encodings.extend(["UTF-8", detected["encoding"]])
        
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

def openAudioFile(filePath):
    """Return, based on extension, an MP3 or Ogg Mutagen object."""
    
    extension = os.path.splitext(filePath)[1].lower()
    try:
        if extension == ".mp3":
            return MP3(filePath, ID3=EasyID3)
        elif extension == ".ogg":
            return Ogg(filePath)
        else:
            log("Cannot access %s tags. File must be an MP3 or Ogg." % quote(filePath))
            # TODO: There's no good reason not to support other formats.
            # Mutagen supports lots of formats.
            raise NotImplementedError
    except HeaderNotFoundError:
        log("Could not open %s. File seems corrupted." % quote(filePath))
