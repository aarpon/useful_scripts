#!/usr/bin/python

import os
import sys
import time
import argparse
import datetime

__VERSION__ = "0.1.1"

class CleanDirTree(object):
    """CleanDirTree scans a directory tree recursively for all files and
folders that have not been accessed for a user-defined time.

The found files are optionally logged and optionally deleted. Empty folders
that have not been accessed are deleted; if a folder contains an empty 
subfolder, only the contained subfolder is deleted. The parent will be deleted 
in the next run.

:param path: full path to the folder to be scanned
:type path : string
:param days: number of days without access for a file to be deleted
:type days : int
:param log_file: (optional) log file name with full path. If not specified, 
actions will not be logged.
:type log_file : string
:param dry_run: (optional, default True) if True, files will be checked but not
deleted. 
:type dry_run: Boolean

*Copyright Aaron Ponti, 2013.*

    """

    # Path to be scanned
    _path = ""
    
    # Log file name
    _logFile = ""

    # Log file handles
    _logFileHandle = None

    # Excluded subdirectories
    _exclude_dirs = None

    # Dry run
    _dryRun = True

    # Verbose
    _verbose = False

    # Current time in seconds
    _currentTime = 0
    
    # Time threshold in seconds
    _timeThreshold = 1e100
    
    # Constant
    _SECONDS_PER_DAY = 24 * 60 * 60

    # Counters
    _nFilesDeleted = 0
    _nDirsDeleted = 0


    def __init__(self, path, days, log_file="", \
                 exclude_dirs = None, dry_run=True, verbose=False):
        """Constructor.
    
:param path: full path to the folder to be scanned
:type path : string
:param days: number of days without access for a file to be deleted
:type days : int
:param log_file: (optional) log file name with full path. If not specified, 
actions will not be logged.
:type log_file : string
:param dry_run: (optional, default True) if True, files will be checked but not
deleted. 
:type dry_run: Boolean

Please mind that if both log_file and dry_run are omitted, nothing will be done.
    """
                
        # Check that 'path' points to an existing directory
        if not os.path.isdir(path):
            sys.stderr.write("Path does not exist.\n")
            sys.exit(1)

        # Cosmetic change for Windows
        if os.name == "nt" and len(path) == 2 and path[1] == ":":
            path = path + "\\"

        # Set the path
        self._path = path

        # Check that days is a positive integer
        days = int(days)
        if days < 0:
            sys.stderr.write("Please specify a number of days larger than " \
                             "or equal to 0.\n")
            sys.exit(1)

        # Log file
        self._logFile = log_file

        # Exclude dirs
        self._exclude_dirs = exclude_dirs
        if self._exclude_dirs is not None:
            for i in range(len(self._exclude_dirs)):
                if os.path.isabs(self._exclude_dirs[i]):
                    sys.stderr.write("Excluded sub-directories must " \
                                     "be relative paths!\n")
                    sys.exit(1)
                else:
                    self._exclude_dirs[i] = os.path.join(path, \
                                                         self._exclude_dirs[i])

        # Dry run flag
        self._dryRun = dry_run

        # Verbose flag
        self._verbose = verbose

        # Calculate days since last access in s
        self._timeThreshold = days * self._SECONDS_PER_DAY

        # Store current time in s
        self._currentTime = time.time()

    def __del__(self):
        '''Destructor.'''
        
        if self._logFileHandle is not None:
            self._logFileHandle.close()
            self._logFileHandle = None

        
    def run(self):
        """Scans and (optionally) cleans the specified path."""

        # Is there something to do?
        if self._logFile == "" and self._dryRun:
            sys.stdout.write("Nothing to do. Please set the log file or " \
                             "remove --dry-run.\n")
            sys.exit(0)

        # Open log file
        if self._logFile != "":
            
            # Open the file
            try:
                self._logFileHandle = open(self._logFile, 'a')
            except:
                sys.stderr.write("Could not open log file " + self._logFile + "\n")
                sys.exit(1)

            # Write the header
            runStr = "run"
            if self._dryRun:
                runStr = "dry run"

            self._logFileHandle.write("\n* * * CleanDirTree: [" + \
                    self._path + "], " + runStr + " on " + \
                    datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S") + \
                    "\n\n")
            
            if self._exclude_dirs is not None:
                if self._verbose:
                    self._logFileHandle.write("Excluded directories: ")
                    for exclude_dir in self._exclude_dirs:
                        self._logFileHandle.write("[" + exclude_dir + "] ")
                    self._logFileHandle.write("\n\n")

        else:
            
            self._logFileHandle = None

        # Process the path recursively
        os.path.walk(self._path, self._processDir, None)

        # Write footer and close the file
        if self._logFileHandle is not None:
            
            # Write the header
            fileStr = "files"
            if self._nFilesDeleted == 1:
                fileStr = "file"
            
            dirStr = "directories"
            if self._nDirsDeleted == 1:
                dirStr = "directory"

            self._logFileHandle.write("\nDeleted " + \
                    str(self._nFilesDeleted) + " " + fileStr + " and " + \
                    str(self._nDirsDeleted) + " " + dirStr + ".\n\n")
            
            # Close the file
            self._logFileHandle.close()
            self._logFileHandle = None


    def _isToBeExcluded(self, currDir):
        '''Check whether currDir is one of the excluded directories or is
        contained in one.
        '''

        # Are there directories to be excluded?
        if self._exclude_dirs is None:
            return False
        
        # Build full path
        fullPath = os.path.join(self._path, currDir)
        
        # Is fullPath one of the excluded dirs or is it contained in one?
        for exclDir in self._exclude_dirs:
            if fullPath.find(exclDir) == 0:
                return True
            
        # Not found. Return False
        return False


    def _processDir(self, args, dirname, filenames):
        """Private callback for os.path.walk()."""
        
        # Check whether current dir is one of the excluded directories
        # or is contained in one
        if self._isToBeExcluded(dirname):
            if self._verbose:
                self._logFileHandle.write("[EXCLUDED] " + dirname + os.linesep)
            return

        # If the directory is empty, we check whether it hasn't been accessed
        # in more than the given time threshold. If it is the case, we delete it. 
        if len(filenames) == 0:
            
            # Get and check last access time
            atime = os.stat(dirname).st_atime
            dTime = self._currentTime - atime
            if (dTime) > self._timeThreshold:
                
                # Log?
                if self._logFileHandle is not None:
                    self._logFileHandle.write("[DIR]      " + dirname + \
                        " (last access on " + time.ctime(atime) + \
                        ") " + os.linesep)

                # Delete?
                if not self._dryRun:
                    try:
                        os.rmdir(dirname)
                        self._nDirsDeleted += 1
                    except:
                        self._logFileHandle.write("[ERROR]    Could not " + \
                            "delete directory " + dirname + os.linesep) 
                                    
            return

        # Check all the files in the directory for access time. We skip
        # sub-directories. They will be processed in the code block above
        # if they are empty. If they are not, they will eventually be. 
        for filename in filenames:
            fullfile = os.path.join(dirname,filename)
            if os.path.isdir(fullfile):
                continue
            atime = os.stat(fullfile).st_atime
            
            # If the file has not been accessed for more than the
            # given time threshold, we can delete it (provided we are not
            # in a dry run)
            dTime = self._currentTime - atime
            if (dTime) > self._timeThreshold:
                
                # Log?
                if self._logFileHandle is not None:
                    self._logFileHandle.write("[FILE]     " + fullfile + \
                        " (last access on " + time.ctime(atime) + \
                        ") " + os.linesep)

                # Delete?
                if not self._dryRun:
                    try:
                        os.remove(fullfile)
                        self._nFilesDeleted += 1
                    except:
                        self._logFileHandle.write("[ERROR]    Could not " + \
                            "delete file " + fullfile + os.linesep)


# === Program entry point ===

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(
         description='Deletes files and folders that have not been ' \
        'accessed for a user-defined number of days from a ' \
        'specified location.', \
        epilog="Copyright, Aaron Christian Ponti, 2013 - 2014" )
    parser.add_argument('path', help='full path to directory to be processed.')
    parser.add_argument('days', type=int,
                   help='number of days without access for a file ' \
                   'or an (empty) folder to be deleted.')
    parser.add_argument('log_file', default="",
                   help='log file with full path.')
    parser.add_argument('--exclude-dirs', dest='exclude_dirs', nargs = "*",
                   help='optional list of sub-directories (relative path) ' \
                   'to ignore.')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                        help='do not delete, log only.')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='verbose output.')
    parser.add_argument('-v', '--version', help='show version information', \
                        action='version',
                        version='cleanDirTree version ' + __VERSION__ + '.')
    args = parser.parse_args()

    # Instantiate the CleanDirTree object and process the folder
    cleanDirTree = CleanDirTree(args.path, args.days, args.log_file, \
                                args.exclude_dirs, args.dry_run, args.verbose)
    cleanDirTree.run()
