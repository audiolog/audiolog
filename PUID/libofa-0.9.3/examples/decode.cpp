/* ------------------------------------------------------------------

   libofa -- the Open Fingerprint Architecture library

   Public Domain (PD) 2006 MusicIP Corporation
   No rights reserved.

-------------------------------------------------------------------*/
#include "protocol.h"
#include <stdio.h>
#include <cstdlib>

AudioData* loadWaveFile(const char *file);

//	loadDataUsingLAME
//
//	Opens an audio file and converts it to a temp .wav file
//	Calls loadWaveFile to load the data
//
AudioData* loadDataUsingLAME(const char *file)
{
    char command[1000];
    const char* tempFile = "tempFile.wav";
    sprintf(command, "lame --quiet --decode \"%s\" \"%s\"", file, tempFile);
    
    if(system(command) == -1)
    {
        printf("Error decoding %s\n", file);
        return 0;
    }
    
    AudioData *data = loadWaveFile(tempFile);
    unlink(tempFile);
    return data;
}

AudioData* loadDataUsingOGGDEC(const char *file)
{
	char command[1000];
	const char* tempFile = "tempFile.wav";
	sprintf(command, "oggdec --quiet -o \"%s\" \"%s\"", tempFile, file);

	if(system(command) == -1)
	{
		printf("Error decoding %s\n", file);
		return 0;
	}

	AudioData *data = loadWaveFile(tempFile);
	unlink(tempFile);
	return data;
}
