#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import logging
import os
import sys

from .workflow.pipeline import RestrictedPlug, FreePlug, Stage, FocusStage, Drop, Rename, Fault, RepeatScenario, ToShuffler, Clip
from .workflow.shuffler import Shuffler
from .optimizer.input import Consumption, Link, Production, InputNode, Study
from .optimizer.output import OutputProduction, OutputNode, OutputLink, OutputConsumption, Result
from .optimizer.optimizer import LPOptimizer, RemoteOptimizer
from .viewer.html import HTMLPlotting
from .analyzer.result import ResultAnalyzer

__version__ = '0.3.1'

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
