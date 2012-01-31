import os
import sys
import shutil
import subprocess
import datetime
from os.path import join

from helpers import openAudioFile, toUnicode, timeToStr

def log(msg):
    """Write msg to stdout and log file."""
    
    global logFile
    utf8_msg = toUnicode(msg).encode("UTF-8")
    print utf8_msg,
    sys.stdout.flush()
    logFile.write(utf8_msg)

def resultsToText(dirPath):
    """Given a directory path, write file names and audio metadata to text."""
    
    filenames = ""
    metadata = ""
    indent = ""
    fields = ["artist", "date", "album", "tracknumber", "tracktotal", "title"]
    for root, dirs, files in os.walk(dirPath):
        for dir in sorted(dirs):
            filenames += (indent + dir).ljust(50) + "\n"
        for file in sorted(files):
            filenames += (indent + file).ljust(50) + "\n"
            if os.path.splitext(file)[1].lower() in (".ogg", ".mp3"):
                audioFile = openAudioFile(join(root, file))
                md = "\n".join([field.ljust(16) + audioFile[field][0].ljust(40)
                                for field in fields]
                metadata += md + "\n\n"
        indent += "  "
    return toUnicode(filenames) + "\n" + toUnicode(metadata)

attempts = 0
crashed = 0
rejected = 0
incorrect  = 0
correct = 0

samplesDirPath = "samples"

inputDirPath = join("testing", "input")
outputDirPath = join("testing", "output")

testStartTime = datetime.datetime.now()
logFileName = testStartTime.strftime("%Y-%m-%d %H-%M") + ".txt"
logFilePath = join(samplesDirPath, "log", logFileName)
logFile = open(logFilePath, "w")

for sample in sorted(os.listdir(samplesDirPath)):
    # Make sure this is a numbered (e.g. "02") sample directory.
    if not sample.isdigit():
        continue
    #num = int(sample)
    #if not num in (99,):
    #    continue
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
    outPath = join(logPath, "output")
    errPath = join(logPath, "error")
    metaPath = join(logPath, "meta")
    
    # Find the name of this sample and display it.
    genre, artist, year_album = [dirs[0] for root, dirs, files
                                 in os.walk(sampleCorrectPath) 
                                 if len(dirs) == 1]
    name = toUnicode("%s - %s" % (artist, year_album[7:]))
    if len(name) > 30:
        name = name[:27] + "..."
    log("\n%s %s " % (sample, name.ljust(30)))
    
    # Copy the sample into the current input folder.
    contentDirName = os.listdir(sampleInputPath)[0]
    sourcePath = join(sampleInputPath, contentDirName)
    destPath = join(inputDirPath, contentDirName)
    shutil.copytree(sourcePath, destPath)
    
    # Run Audiolog on this sample
    cmd = ["python", "audiolog", "--no-gui", "-s", outputDirPath, inputDirPath]
    with open(outPath, "w") as out, open(errPath, "w") as err:
        subprocess.Popen(cmd, stdout=out, stderr=err).wait()
    
    with open(outPath, "r") as out, open(errPath, "r") as err:
        output = out.read()
        error = err.read()
    
    metadata = [s for s in output.split("\n\n\n\n") if "Results:" in s]
    with open(metaPath, "w") as meta:
        meta.write("\n\n\n".join(metadata).strip().replace(" "*20, ""))

    # Check for whether the sample was sorted at all.
    if not os.listdir(outputDirPath):
        if "Traceback" in error:
            crashed += 1
            log("program crashed\n")
        else:
            rejected += 1
            log("not sorted\n")
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
        f.write(toUnicode(text).encode("UTF-8"))
        f.close()
        
    # Now let's diff the filenames.
    diff = open(join(logPath, "diff"), "w")
    p = subprocess.Popen(["diff", "-y", "--left-column", 
                          join(logPath, "correct"), join(logPath, "actual")], 
                         stdout=diff)
    p.wait()
    if correctResults != actualResults:
        incorrect += 1
        log("sorted incorrectly\n")
        continue
    
    # If we got this far, then nothing went wrong. 
    correct += 1
    log("sorted correctly!\n")
    
testDuration = datetime.datetime.now() - testStartTime
log("\nOf %d total:\n" % attempts)
log("  %d crashed\n" % crashed)
log("  %d not sorted\n" % rejected)
log("  %d sorted incorrectly\n" % incorrect)
log("  %d sorted correctly\n" % correct)
log("Tests took %s " % (timeToStr(testDuration)))
log("(%s per attempt).\n" % (timeToStr(testDuration/attempts)))
