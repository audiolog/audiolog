/* ------------------------------------------------------------------

   libofa -- the Open Fingerprint Architecture library

   Public Domain (PD) 2006 MusicIP Corporation
   No rights reserved.
   
   How to make this damn thing:
   if g++ -DHAVE_CONFIG_H -I. -I. -I.. -I../include    -g -O2 -Wall -g -MT example.o -MD -MP -MF ".deps/example.Tpo" -c -o example.o example.cpp; \
        then mv -f ".deps/example.Tpo" ".deps/example.Po"; else rm -f ".deps/example.Tpo"; exit 1; fi
/bin/bash ../libtool --mode=link g++  -g -O2 -Wall -g   -o example  example.o protocol.o decode.o wavefile.o -lcurl -lexpat ../lib/libofa.la  -lfftw3
g++ -g -O2 -Wall -g -o .libs/example example.o protocol.o decode.o wavefile.o  /usr/lib/libcurl.so /usr/lib/libexpat.so ../lib/.libs/libofa.so /usr/lib/libfftw3.so -Wl,--rpath -Wl,/usr/local/lib

-------------------------------------------------------------------*/

#include "protocol.h"
#include <string.h>

AudioData* loadWaveFile(const char* file);
AudioData* loadDataUsingLAME(const char* file);
AudioData* loadDataUsingOGGDEC(const char* file);

int main(int argc, char **argv) {
    AudioData* data = 0;
    
    // Go through each filename passed on the command line
    for(int i = 1; i < argc; i++)
    {
        char* file = argv[i];

        // Get the extension
        char fext[100] = "";
        char* p = strrchr(file, '.');
        if(p != NULL)
        {
            strcpy(fext, p+1);

            // Lowercase the extension
            p = fext;
            while(*p)
            {
                *p = tolower(*p);
                p++;
            }
        }
        
        if(strstr(fext, "wav"))
        {
            // Process a Wave file
            data = loadWaveFile(file);
        }
        else if(strstr(fext, "mp3"))
        {
            // Decode MP3
            //printf("Decoding file %s with lame\n", file);
            data = loadDataUsingLAME(file);
        } else if(strstr(fext, "ogg")) {
            // Decode Vorbis
            //printf("Decoding file %s with oggdec\n", file);
            data = loadDataUsingOGGDEC(file);
        }
        else
        {
            printf("Unable to detect filetype.\n");
        }
        if (!data) {
            printf("** Failed to load file\n");
            return -1;
        }

        // Get the fingerprint
        if (!data->createPrint()) {
            printf("** Failed to generate print.\n");
            delete data;
            return -1;
        }

        // Get the metadata.  Make sure to get your own client id
        // at http://www.musicdns.org before using this in your own application.
        TrackInformation *info = data->getMetadata("a66a78b0401f53189d5dd98a5c89f5a9", "Example 0.9.3", true);
        if (!info) {
            printf("** Failed to get metadata.\n");
        } else {
            // Print results.
            printf("Success.\n");
            printf("%s\n", info->getArtist().c_str());
            printf("%s\n", info->getTrack().c_str()); // Name of track, if available
            printf("%s\n", info->getPUID().c_str());
        }
        delete data;
    }
    
    return 0;
}

