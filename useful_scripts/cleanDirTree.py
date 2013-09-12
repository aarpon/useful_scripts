#!/usr/bin/python

import os
import sys
import time
import argparse
import datetime

__VERSION__ = "0.1.0"

class Walker(object):
    """Walker scans a directory tree recursively for all files and folders that
have not been accessed for a user-defined time.

The found files are logged and optionally deleted. Empty folders that have not
been accessed are deleted; if a folder contains an empty subfolder, only the 
contained subfolder is deleted. The parent will be deleted in the next run.

:param path: full path to the folder to be scanned
:type path : string
:param days: number of days without access for a file to be deleted
:type days : int

*Copyright Aaron Ponti, 2013.*

    """

    # Path to be scanned
    _path = ""
    
    # List of files to be deleted with full path
    _filesToDelete = []
    
    # List of empty folders to be deleted with full path
    _emptyDirsToDelete = []
    
    # Current time in seconds
    _currentTime = 0
    
    # Time threshold in seconds
    _timeThreshold = 1e100
    
    # Constant
    _SECONDS_PER_DAY = 24 * 60 * 60


    def __init__(self, path, days):
        """Constructor.
    
:param path: full path to the folder to be scanned
:type path : string
:param days: number of days without access for a file to be deleted
:type days : int
    """
                
        # Check that 'path' points to an existing directory
        if not os.path.isdir(path):
            sys.stderr.write("Path does not exist.")
            sys.exit(1)

        # Set the path
        self._path = path

        # Check that days is a positive integer
        days = int(days)
        if days < 0:
            sys.stderr.write("Please specify a number of days larger than " \
                             "or equal to 0.")
            sys.exit(1)

        # Calculate days since last access in s
        self._timeThreshold = days * self._SECONDS_PER_DAY

        # Store current time in s
        self._currentTime = int(round(time.time()))


    def scan(self):
        """Scans the (stored) path."""
    
        # Scan
        os.path.walk(path, self._processDir, None)


    def _processDir(self, args, dirname, filenames):
        """Private callback for os.path.walk()."""
        
        # If the directory is empty, we check whether it hasn't been accessed
        # in more than the given time threshold. If it is the case, we add it
        # to the list of empty folders to delete 
        if len(filenames) == 0:
            
            # Get and check last access time
            atime = os.stat(dirname).st_atime
            dTime = self._currentTime - atime
            if (dTime) > self._timeThreshold:
                self._emptyDirsToDelete.append(dirname)
            return

        # Check all the files in the directory for access time. We skip
        # subdirectories. They will be processed in the code block above
        # if they are empty. If they are not, they will eventually be. 
        for filename in filenames:
            fullfile = os.path.join(dirname,filename)
            if os.path.isdir(fullfile):
                continue
            atime = os.stat(fullfile).st_atime
            
            # If the file has not been accessed for more than the
            # given time threshold, we add it to the list of files to
            # be deleted
            dTime = self._currentTime - atime
            if (dTime) > self._timeThreshold:
                self._filesToDelete.append(fullfile)


    # Delete the files
    def delete(self):
        """Delete the files and folders found during the scan."""

        # Delete files
        for current in self._filesToDelete:
            os.remove(current)
        
        # Delete (empty) directories
        for current in self._emptyDirsToDelete:
            os.rmdir(current)


    def log(self, log_file):
        """Log the result of the scan to file.
        
:param log_file: full path to the log file
:type path : string

        """

        
        try:

            # Open the file (in 'append' mode)
            f = open(log_file, 'a')

            # Write the header
            f.write("\n* * * CleanDirTree run - " + \
                    datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S") + \
                    "\n\n")

            # Write the list of files and empty folder found
            nFiles = len(self._filesToDelete)
            nDirs  = len(self._emptyDirsToDelete)
            if nFiles == 0 and nDirs == 0:
                f.write("Nothing to delete.\n")
            else:
                if nDirs > 0:
                    f.write("\n=== Directories:\n")
                    for current in self._emptyDirsToDelete:
                        f.write(current + os.linesep)                    
                if nFiles > 0:
                    f.write("\n=== Files:\n")
                    for current in self._filesToDelete:
                        f.write(current + os.linesep)

            # Close the file
            f.close()

        except:
            sys.stderr.write("Error: could not write to file " + log_file + "!")


# === Program entry point ===

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(description='CleanDirTree ' + __VERSION__)
    parser.add_argument('path', nargs=1,
                   help='full path to directory to be scanned')
    parser.add_argument('days', type=int, nargs=1,
                   help='number of days without access for a file " \
                   "or an empty folder to be deleted')
    parser.add_argument('log_file', nargs=1,
                   help='log file with full path')    
    parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                   help='do not delete, log only')
    args = parser.parse_args()

    # Get the path
    path = args.path[0]
    
    # Get the days
    days = args.days[0]
    
    # Get the log file
    log_file = args.log_file[0]

    # Get the dry-run flag
    dry_run = args.dry_run

    # Instantiate the Crawler and process
    walker = Walker(path, days)
    walker.scan()
    
    # Delete if requested
    if dry_run == False:
        walker.delete()

    # Log
    walker.log(log_file)
