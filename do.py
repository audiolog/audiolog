def do(command, filename, cue=None):
    """Takes a command and acts according to settings"""

    command = command.replace("$$", filename)
    if cue: command = command.replace("&&", cue + ".cue")
    if constants.SIMULATE or constants.VERBOSE:
            print "Command:", command
    if (not constants.SIMULATE) and ("rm " in command) and constants.PROMPT:
        certainty = raw_input("This will result in deletion. Are you sure (y/n)? ")
        if not ((certainty == 'y') or (certainty == 'Y')): return
    if not constants.SIMULATE:
        os.system(command)
        