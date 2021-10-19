import os
import sys
import time
import argparse
import datetime
from pathlib import Path


__version__ = "0.3.2"


class CleanDirTree:
    """CleanDirTree scans a directory tree recursively for all files and folders that have not been
     accessed for a user-defined time.

    The found files are optionally logged and optionally deleted. Empty folders that have not been
    accessed are deleted; if a folder contains an empty subfolder, only the contained subfolder is
    deleted. The parent will be deleted in the next run.

    :param path: full path to the folder to be scanned
    :type path : string
    :param days: number of days without access for a file to be deleted
    :type days : int
    :param log_file: (optional) log file name with full path. If not specified, actions will not be logged.
    :type log_file : string
    :param dry_run: (optional, default True) if True, files will be checked but not deleted.
    :type dry_run: Boolean
    :param verbose: (optional, default False) if False, the script will log with higher verbosity.
    :type verbose: Boolean

    Please mind that if both log_file and dry_run are omitted, nothing will be done.

    *Copyright Aaron Ponti, 2013 - 2021.*

    """

    def __init__(self, path, days, log_file="", exclude_dirs=None, dry_run=True, verbose=False):
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
        :param verbose: (optional, default False) if False, the script will log with
        higher verbosity.
        :type verbose: Boolean

        Please mind that if both log_file and dry_run are omitted, nothing will be done.
    """

        # Path to be scanned
        self._path = ""

        # Log file name
        self._log_file = ""

        # Log file handles
        self._log_file_handle = None

        # Excluded sub-directories
        self._exclude_dirs = None

        # Dry run
        self._dry_run = True

        # Verbose
        self._verbose = False

        # Current time in seconds
        self._current_time = 0

        # Time threshold in seconds
        self._time_threshold = 1e100

        # Constant
        self._SECONDS_PER_DAY = 24 * 60 * 60

        # Counters
        self._num_files_deleted = 0
        self._num_dirs_deleted = 0

        # Check that 'path' points to an existing directory
        if not os.path.isdir(path):
            sys.stderr.write(f"Path does not exist.{os.linesep}")
            sys.exit(1)

        # Cosmetic change for Windows
        if os.name == "nt" and len(path) == 2 and path[1] == ":":
            path = path + "\\"

        # Set the path
        self._path = path

        # Check that days is a positive integer
        days = int(days)
        if days < 0:
            sys.stderr.write(f"Please specify a number of days larger than or equal to 0.{os.linesep}")
            sys.exit(1)

        # Log file
        self._log_file = log_file

        # Exclude dirs
        self._exclude_dirs = exclude_dirs
        if self._exclude_dirs is not None:
            for i in range(len(self._exclude_dirs)):
                if os.path.isabs(self._exclude_dirs[i]):
                    sys.stderr.write(f"Excluded sub-directories must be relative paths!{os.linesep}")
                    sys.exit(1)
                else:
                    self._exclude_dirs[i] = os.path.join(path, self._exclude_dirs[i])

        # Dry run flag
        self._dry_run = dry_run

        # Verbose flag
        self._verbose = verbose

        # Calculate days since last access in s
        self._time_threshold = days * self._SECONDS_PER_DAY

        # Store current time in s
        self._current_time = time.time()

    def __del__(self):
        """Destructor."""

        if self._log_file_handle is not None:
            self._log_file_handle.close()
            self._log_file_handle = None

    def run(self):
        """Scans and (optionally) cleans the specified path."""

        # Is there something to do?
        if self._log_file == "" and self._dry_run:
            sys.stdout.write(f"Nothing to do. Please set the log file or remove --dry-run.")
            sys.exit(0)

        # Open log file
        if self._log_file != "":

            # Make sure that the path to the log file exists, otherwise create it
            log_dir = Path(self._log_file).parent
            try:
                log_dir.mkdir(exist_ok=True, parents=True)
            except:
                sys.stdout.write(f"Can not create log file in {log_dir}{os.linesep}.")
                sys.exit(1)

            # Open the file
            try:
                self._log_file_handle = open(self._log_file, 'a')
            except FileNotFoundError as e:
                sys.stderr.write(f"Could not open log file {self._log_file}{os.linesep}")
                sys.exit(1)

            # Write the header
            run_str = "run"
            if self._dry_run:
                run_str = "dry run"

            run_time = datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S")
            self._log_file_handle.write(f"{os.linesep}{os.linesep}"
                                        f"* * * CleanDirTree: [{self._path}], {run_str} on "
                                        f"{run_time}{os.linesep}")

            if self._exclude_dirs is not None:
                if self._verbose:
                    self._log_file_handle.write("Excluded directories: ")
                    for exclude_dir in self._exclude_dirs:
                        self._log_file_handle.write(f"[{exclude_dir}] ")
                    self._log_file_handle.write(f"{os.linesep}")

        else:

            self._log_file_handle = None

        # Process the path recursively
        for root, subdirs, files in os.walk(self._path, topdown=False):

            # Process files
            for f in files:
                full_file = os.path.join(root, f)
                if os.path.isdir(full_file):
                    continue
                a_time = os.stat(full_file).st_atime

                # If the file has not been accessed for more than the
                # given time threshold, we can delete it (provided we are not
                # in a dry run)
                d_time = self._current_time - a_time
                if d_time > self._time_threshold:

                    # Log?
                    if self._log_file_handle is not None:
                        self._log_file_handle.write(f"[FILE]     {full_file} (last access on "
                                                    f"{time.ctime(a_time)}, "
                                                    f"{int(d_time / self._SECONDS_PER_DAY)} days ago)"
                                                    f"{os.linesep}")

                    # Delete?
                    if not self._dry_run:
                        try:
                            os.remove(full_file)
                            self._num_files_deleted += 1
                        except:
                            self._log_file_handle.write(f"[ERROR]    Could not delete file {full_file}{os.linesep}")

            # Process folders
            for d in subdirs:

                dir_name = os.path.join(root, d)

                # Check whether current dir is one of the excluded directories
                # or is contained in one
                if self._is_to_be_excluded(dir_name):
                    if self._verbose:
                        self._log_file_handle.write(f"[EXCLUDED] {dir_name}{os.linesep}")
                    continue

                # If the directory is empty, we delete it. Scanning the folders for files changes
                # the access time, and therefore we will never find a folder that hasn't been accessed
                # long enough to be deleted.
                try:
                    filenames = os.listdir(dir_name)
                    if len(filenames) == 0:

                        # Log?
                        if self._log_file_handle is not None:
                            self._log_file_handle.write(f"[DIR]      {dir_name}{os.linesep}")

                        # Delete?
                        if not self._dry_run:
                            try:
                                os.rmdir(dir_name)
                                self._num_dirs_deleted += 1
                            except:
                                self._log_file_handle.write(
                                    f"[ERROR]    Could not delete directory {dir_name}{os.linesep}")

                except:
                    # We couldn't even access the folder; skip
                    # Log?
                    if self._log_file_handle is not None:
                        self._log_file_handle.write(
                            f"[ERROR]    Could not access directory {dir_name}{os.linesep}")

        # Write footer and close the file
        if self._log_file_handle is not None:

            # Write the header
            file_str = "files"
            if self._num_files_deleted == 1:
                file_str = "file"

            dir_str = "directories"
            if self._num_dirs_deleted == 1:
                dir_str = "directory"

            self._log_file_handle.write(f"{os.linesep}Deleted {self._num_files_deleted} {file_str} "
                                        f"and {self._num_dirs_deleted} {dir_str}{os.linesep}")

            # Close the file
            self._log_file_handle.close()
            self._log_file_handle = None

    def _is_to_be_excluded(self, curr_dir):
        """Check whether currDir is one of the excluded directories or is
        contained in one.
        """

        # Are there directories to be excluded?
        if self._exclude_dirs is None:
            return False

        # Build full path
        full_path = os.path.join(self._path, curr_dir)

        # Is full_path one of the excluded dirs or is it contained in one?
        for exclDir in self._exclude_dirs:
            if full_path.find(exclDir) == 0:
                return True

        # Not found. Return False
        return False


# === Program entry point ===

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(
        description="Deletes files and folders that have not been accessed for a user-defined number "
                    "of days from a specified location.",
        epilog="Copyright, Aaron Ponti, ETH Zurich, 2013 - 2021")
    parser.add_argument("path", help="full path to directory to be processed.")
    parser.add_argument("days", type=int,
                        help="number of days without access for a file or an (empty) folder to be deleted.")
    parser.add_argument("log_file", default="", help="log file with full path.")
    parser.add_argument("--exclude-dirs", dest="exclude_dirs", nargs="*",
                        help="optional list of sub-directories (relative path) to ignore.")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="do not delete, log only.")
    parser.add_argument("--verbose", dest="verbose", action='store_true', help='verbose output.')
    parser.add_argument("-v", "--version", help="show version information", action="version",
                        version=f"cleanDirTree version {__version__}.")
    args = parser.parse_args()

    # Instantiate the CleanDirTree object and process the folder
    cleanDirTree = CleanDirTree(args.path, args.days, args.log_file,
                                args.exclude_dirs, args.dry_run, args.verbose)
    cleanDirTree.run()

    sys.exit(0)