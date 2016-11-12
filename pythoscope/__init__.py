import sys

reload(sys)
sys.setdefaultencoding("utf-8")

from cmdline import main, __version__
from snippet import start, stop
