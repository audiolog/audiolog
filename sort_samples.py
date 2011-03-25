import os
import sys
import shutil
import subprocess
import datetime
from cStringIO import StringIO
from os.path import join

import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis as Ogg
from mutagen.easyid3 import EasyID3

def openAudioFile(filePath):
    """Return, based on extension, an MP3 or Ogg Mutagen object."""
    
    extension = os.path.splitext(filePath)[1].lower() 
    if extension == ".mp3":
        return MP3(filePath, ID3=EasyID3)
    elif extension == ".ogg":
        return Ogg(filePath)
    else:
        raise NotImplementedError
    
def metadataToText(filePath):
    """Given file path, write audio tag metadata to text."""
    
    audioFile = openAudioFile(filePath)
    text = ""
    for field in sorted(audioFile.keys()):
        if not field == "genre":
            text += field.ljust(16) + str(audioFile[field]).ljust(40) + "\n"
    return text

def resultsToText(dirPath):
    """Given a directory path, write file names and audio metadata to text."""
    
    filenames = ""
    metadata = ""
    indent = ""
    for root, dirs, files in os.walk(dirPath):
        for dir in sorted(dirs):
            filenames += (indent + dir).ljust(50) + "\n"
        for file in sorted(files):
            filenames += (indent + file).ljust(50) + "\n"
            if os.path.splitext(file)[1].lower() in (".ogg", ".mp3"):
                metadata += metadataToText(join(root, file)) + "\n"
        indent += "  "
    return filenames + "\n" + metadata    

attempts = 0
correct = 0

toSortPath = join("samples", "current_input")
sortedPath = join("samples", "Sorted")

testStartTime = datetime.datetime.now()
azulRunDuration = datetime.timedelta()

for sample in sorted(os.listdir("samples")):
    # Make sure this is a numbered (e.g. "02") sample directory.
    if not sample.isdigit():
        continue
    attempts += 1
    
    # Clean up from any previous runs to start fresh.
    for folder in ("Sorted", "Deletes", "Rejects", "current_input"):
        shutil.rmtree(join("samples", folder), ignore_errors=True)    

    # Determine necessary filepaths and create potentially missing directories.
    logPath = join("samples", sample, "log")
    inputPath = join("samples", sample, "input")
    correctPath = join("samples", sample, "correct")
    os.makedirs(toSortPath)
    os.makedirs(sortedPath)
    
    # Find the name of this sample and display it.
    genre, artist, year_album = [dirs[0] for root, dirs, files in os.walk(correctPath) if dirs]
    name =  "%s - %s" % (artist, year_album[7:])
    if len(name) > 30:
        name = name[:27] + "..."
        
    # Print the sample we are sorting and make sure it's displayed immediately.
    print "\n", sample, name.ljust(30), 
    sys.stdout.flush()
    
    # Copy the sample into the current input folder.
    contentDirName = os.listdir(inputPath)[0]
    sourcePath = join(inputPath, contentDirName)
    destPath = join(toSortPath, contentDirName)
    shutil.copytree(sourcePath, destPath)
    
    # Run Azul on this sample
    out = open(join(logPath, "output"), "w+")
    err = open(join(logPath, "error"), "w+")
    runStartTime = datetime.datetime.now()
    subprocess.Popen(["src/azul.py", toSortPath], stdout=out, stderr=err).wait()
    azulRunDuration += datetime.datetime.now() - runStartTime
    
    # Now let's get the error results (we'll use those) and close the files.
    err.seek(0)
    error = err.read()
    out.close()
    err.close()
    
    # Check for whether the sample was sorted at all.
    # The next line is needed until libofa (getPUID) error is resolved.
    if not os.listdir(sortedPath):
    #error = "\n".join([line for line in error.splitlines() if not "libofa" in line])
    #if error:
        print "program crashed" if "Traceback" in error else "not sorted"
        # TODO: Possibly say where to look for more info.
        continue

    # Create a text representation of the file names and audio metadata
    # for both the known correct output and the actual output.
    # These text representations can then be sent to a text comparision program
    # (diff) to find whether and where they differ.
    correctResults = resultsToText(correctPath)
    actualResults = resultsToText(sortedPath)
            
    # Now we write the texts to text files because that's how diff likes things.
    for name, text in (("correct", correctResults), ("actual", actualResults)):
        f = open(join(logPath, name), "w")
        f.write(text)
        f.close()
        
    # Now let's diff the filenames.
    diff = open(join(logPath, "diff"), "w")
    p = subprocess.Popen(["diff", "-y", "--left-column", 
                          join(logPath, "correct"), join(logPath, "actual")], 
                         stdout=diff)
    p.wait()
    if correctResults != actualResults:
        print "sorted incorrectly"
        # TODO: Possibly say where to look for more info.
        continue
    
    # If we got this far, then nothing went wrong. 
    print "sorted correctly!"
    correct += 1
    
testDuration = datetime.datetime.now() - testStartTime
print "\nCorrectly sorted %d of %d." % (correct, attempts)
print "Tests took %.1f minutes" % (testDuration.seconds/60.0),
print "(%.2f minutes per attempt)." % (testDuration.seconds*1.0/attempts/60.0)
print "Azul took %.1f minutes" % (azulRunDuration.seconds/60.0),
print "(%.2f minutes per attempt)." % (azulRunDuration.seconds*1.0/attempts/60.0)


# Run Azul on this sample
#out = StringIO()
#err = StringIO()
#p = subprocess.Popen(["python", "src/azul.py", toSortPath], 
                     #stdout=out, stderr=errs)
#p.wait()
#output = out.getvalue()
#error = err.getvalue()

# Run Azul on this sample
#p = subprocess.Popen(["python", "src/azul.py", toSortPath], 
                     #stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#output, error = p.communicate()