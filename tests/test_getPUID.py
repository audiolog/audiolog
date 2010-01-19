# -*- coding: utf-8 -*-

import os
import subprocess

def getPUID(filePath):
	output = subprocess.Popen([os.path.join(os.getcwd(), "getPUID"), '"' + filePath + '"'], stdout = subprocess.PIPE).communicate()[0]
	output = output.splitlines()

	if output[0] == "Success.":
		return output[1:]
	else:
		print "Unable to get PUID."
		return False

stuff = getPUID("test.mp3")

for thing in stuff:
	print "Thing: " + thing
