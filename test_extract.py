import os.path
import shutil
import subprocess

import extract

def test_extract():
    """Test extract.extract function.
    
    We want to test all supported formats:
        - Zip
        - Rar
        - Tar
        - Gzip
        - Bzip2
        - Ace
        
    Is one archive per format enough testing?
    
    Method:
    Create a temporary copy of a set of archives.
    Extract them using extract.extract.
    Call "ls -sR" on that directory and a directory we know to be correct.
    The results should be the same."""
    
    archiveDirPath = os.path.join(os.cwd(), "test_archives")
    tempArchiveDirPath = os.path.join(os.cwd(), "test_archives_copy")
    comparisonDirPath = os.path.join(os.cwd(), "test_archives_extracted")    
    shutil.copy(archiveDirPath, tempArchiveDirPath)
    archiveNames = os.listdir(tempArchiveDirPath)
    archivePaths = [os.path.join(tempArchiveDirPath, name) for name in archiveNames]
    
    extract.extract(archivePaths)
    
    cmd = "ls -sR" % "test_archives"
    p1 = subprocess.Popen([command, tempArchiveDirPath], stdout=subprocess.PIPE)
    actual = p1.communicate()
    p2 = subprocess.Popen([command, comparisonDirPath], stdout=subprocess.PIPE)
    expected = p2.communicate()
    
    assert actual == expected

    