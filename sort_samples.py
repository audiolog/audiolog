import os
import sys
import shutil
import subprocess
import datetime
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
crashed = 0
rejected = 0
incorrect  = 0
correct = 0

samplesDirPath = join("..", "audiolog-samples")

inputDirPath = join("testing", "input")
outputDirPath = join("testing", "output")

testStartTime = datetime.datetime.now()
audiologRunDuration = datetime.timedelta()

for sample in sorted(os.listdir(samplesDirPath)):
    # Make sure this is a numbered (e.g. "02") sample directory.
    if not sample.isdigit():
        continue
    attempts += 1
    
    # Clean up from any previous runs to start fresh.
    for dirPath in (inputDirPath, outputDirPath):
        shutil.rmtree(dirPath, ignore_errors=True)
    os.makedirs(inputDirPath)
    os.makedirs(outputDirPath)

    # Determine necessary filepaths.
    sampleInputPath = join(samplesDirPath, sample, "input")
    sampleCorrectPath = join(samplesDirPath, sample, "correct")
    logPath = join(samplesDirPath, sample, "log")
    
    # Find the name of this sample and display it.
    genre, artist, year_album = [dirs[0] for root, dirs, files
                                 in os.walk(sampleCorrectPath) if len(dirs) == 1]
    name =  "%s - %s" % (artist, year_album[7:])
    if len(name) > 30:
        name = name[:27] + "..."
        
    # Print the sample we are sorting and make sure it's displayed immediately.
    print "\n", sample, name.ljust(30), 
    sys.stdout.flush()
    
    # Copy the sample into the current input folder.
    contentDirName = os.listdir(unicode(sampleInputPath))[0]
    sourcePath = join(sampleInputPath, contentDirName)
    destPath = join(inputDirPath, contentDirName)
    shutil.copytree(unicode(sourcePath), unicode(destPath))
    
    # Run Audiolog on this sample
    out = open(join(logPath, "output"), "w+")
    err = open(join(logPath, "error"), "w+")
    cmd = ["python", "src/audiolog.py", "--no-gui", "-s", outputDirPath, inputDirPath]
    runStartTime = datetime.datetime.now()
    subprocess.Popen(cmd, stdout=out, stderr=err).wait()
    audiologRunDuration += datetime.datetime.now() - runStartTime
    
    # Now let's get the error results (we'll use those) and close the files.
    err.seek(0)
    error = err.read()
    out.close()
    err.close()
    
    # Check for whether the sample was sorted at all.
    if not os.listdir(outputDirPath):
        if "Traceback" in error:
            crashed += 1
            print "program crashed"
        else:
            rejected += 1
            print "not sorted"
        continue

    # Create a text representation of the file names and audio metadata
    # for both the known correct output and the actual output.
    # These text representations can then be sent to a text comparision program
    # (diff) to find whether and where they differ.
    correctResults = resultsToText(sampleCorrectPath)
    actualResults = resultsToText(outputDirPath)
            
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
        incorrect += 1
        print "sorted incorrectly"
        # TODO: Possibly say where to look for more info.
        continue
    
    # If we got this far, then nothing went wrong. 
    correct += 1
    print "sorted correctly!"
    
testDuration = datetime.datetime.now() - testStartTime
print "\nOf %d total:" % attempts
print "  %d crashed" % crashed
print "  %d not sorted" % rejected
print "  %d sorted incorrectly" % incorrect
print "  %d sorted correctly"
print "Tests took %.1f minutes" % (testDuration.seconds/60.0),
print "(%.2f minutes per attempt)." % (testDuration.seconds*1.0/attempts/60.0)
print "Audiolog took %.1f minutes" % (audiologRunDuration.seconds/60.0),
print "(%.2f minutes per attempt)." % (audiologRunDuration.seconds*1.0/attempts/60.0)
