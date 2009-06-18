# -*- coding: utf-8 -*-

import os

import clean

def test_standardizeFilenames():
    """Test the clean.standardizeFilenames function.
    
    We want to test that:
        - Periods and underscores are appropriately replaced with spaces.
        - Special characters are removed.
        - There are no consecutive spaces.
        - That item names do not begin or end in a space.
        - That extensions are lowercased.
        - That the above works on file and directory paths and
          on Windows and *nix paths."""
    
    itemNamePairs = [
        ["this.is.a.test.",                 "this is a test"],
        ["now.with.extensions.mp3",         "now with extensions.mp3"],
        ["this.has.a space.test",           "this.has.a space.test"],            
        ["_underscores_should_go_",         "underscores should go"],
        ["even_with_extensions.ogg",        "even with extensions.ogg"],
        [" no spaces at ends ",             "no spaces at ends"],
        ["no ♣ chars",                      "no chars"],
        ["¿At the start?",                  "At the start?"],
        ["¾ lots of ½ÏÝ charsß",            "lots of chars"],
        ["¾ lots of ½ÏÝ charsß.mp3",        "lots of chars.mp3"],
        ["lowercase.OGG",                   "lowercase.ogg"],
        ["lowercase.MP3",                   "lowercase.mp3"],
        ["team.LEET",                       "team LEET"],
        ["  spaces      not  accepted  ",   "spaces not accepted"],
        [".all.Þæ.together.now.MP3",        "all together now.mp3"]
    ]
    
    for baseDirPath in ("C:\\test\\", "/test/"):
            for (givenName, expectedName) in itemNamePairs:
                givenPath = os.path.join(baseDirPath, givenName)
                expectedPath = os.path.join(baseDirPath, expectedName)
                assert clean.standardizeFilenames([givenPath], False) == [expectedPath]
                
    