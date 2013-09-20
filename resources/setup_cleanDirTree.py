# py2exe setup.py file to create an executable from cleanDirTree.py
# @author: Aaron Ponti
#
# From the root folder of the useful_scripts project:
#
#     python resources/setup_cleanDirTree.py py2exe
#
# The generated distribution will be in dist/

# Needed imports
from distutils.core import setup
import py2exe

# Create a console executable from dataCompletedScript.py
setup(name='CleanDirTree',
      version='0.1.0',
      author='Aaron Ponti',
      author_email='aaron.ponti@bsse.ethz.ch',
      console=['useful_scripts/cleanDirTree.py'])
