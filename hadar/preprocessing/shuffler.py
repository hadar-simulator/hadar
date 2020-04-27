#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import multiprocessing
from typing import Dict, Union

import numpy as np
import pandas as pd
from numpy.random.mtrand import randint

from hadar.preprocessing.pipeline import Pipeline, TO_SHUFFLER

__all__ = ['Shuffler', 'Timeline']


class TimelineError(Exception):
    def __init__(self, name):
        Exception.__init__(self, name)

class Timeline:
    def __init__(self, data: np.ndarray = None, sampler = randint):
        self.data = data
        self.sampler = sampler

    def sample(self, nb) -> np.ndarray:
        if self.data is None:
            raise TimelineError('timeline data is empty. Do you compute all TimelinePipeline before sampling ?')
        sampling = self.sampler(0, self.data.shape[0], nb)
        return self.data[sampling]


class TimelinePipeline(Timeline):
    def __init__(self, data: pd.DataFrame, pipeline: Pipeline, sampler = randint):
        Timeline.__init__(self, sampler=sampler)

        if TO_SHUFFLER not in pipeline.plug.outputs:
            raise ValueError("Pipeline output must have a 'to_generate' column, but has %s", pipeline.plug.outputs)

        self.df = data
        self.pipeline = pipeline

    def compute(self):
        res = self.pipeline.compute(self.df)
        drop_columns = res.columns.get_level_values(1).unique().drop(TO_SHUFFLER)
        if drop_columns:
            res = res.drop(drop_columns, axis=1, level=1)
        self.data = res.values.T


def compute(tl: TimelinePipeline):
    tl.compute()


class Shuffler:
    def __init__(self, sampler=randint):
        self.timelines = dict()
        self.sampler = sampler

    def add_data(self, name: str, data: np.ndarray):
        self.timelines[name] = Timeline(data, sampler=self.sampler)

    def add_pipeline(self, name: str, data: pd.DataFrame, pipeline: Pipeline):
        pipeline.assert_computable(data)

        self.timelines[name] = TimelinePipeline(data, pipeline, sampler=self.sampler)

    def shuffle(self, nb_scn):
        # Compute pipelines
        # pool = multiprocessing.Pool()
        # pool.map(compute,

        _ = (compute(tl) for tl in self.timelines.values() if isinstance(tl, TimelinePipeline))

        return {name: tl.sample(nb_scn) for name, tl in self.timelines.items()}


