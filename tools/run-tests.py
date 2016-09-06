#!/usr/bin/python

import glob
import shutil
import sys

from os import system as run
from os import remove as rm

def cp(src, dst):
    shutil.copy(glob.glob(src)[0], dst)

def main():
    run("nosetests")

if __name__ == '__main__':
    sys.exit(main())
