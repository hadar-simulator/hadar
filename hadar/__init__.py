import logging
import os
import sys

from hadar.preprocessing.pipeline import *
from hadar.solver.input import *
from hadar.solver.output import *
from hadar.solver.solver import *
from hadar.viewer.html import *
from hadar.viewer.jupyter import *
from hadar.aggregator.result import *

__version__ = '0.2.1'

level = os.getenv('HADAR_LOG', 'WARNING')

if level == 'INFO':
    level = logging.INFO
elif level == 'DEBUG':
    level = logging.DEBUG
elif level == 'WARNING':
    level = logging.WARNING
elif level == 'ERROR':
    level = logging.ERROR
else:
    level = logging.WARNING

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logging.basicConfig(level=level, handlers=[handler])
