#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
from typing import Dict, Union

import numpy as np
import pandas as pd

from hadar.preprocessing.pipeline import Pipeline, TO_GENERATOR

__all__ = ['Composition', 'Generator', 'Timeline']

class Composition:
    def __init__(self):
        pass

    def __getitem__(self, item):
        pass


class Timeline:
    def __init__(self, data: np.ndarray = None):
        self.data = data
        self.sampling = None

    def sample(self, nb):
        self.sampling = np.random.randint(0, self.data.shape[0], nb)

    def __getitem__(self, item: int):
        return self.data[self.sampling[item]]


class TimelinePipeline(Timeline):
    def __init__(self, data: pd.DataFrame, pipeline: Pipeline):
        Timeline.__init__(self)

        if TO_GENERATOR not in pipeline.plug.outputs:
            raise ValueError("Pipeline output must have a 'to_generate' column, but has %s", pipeline.plug.outputs)

        self.data = data
        self.pipeline = pipeline

    def compute(self):
        res = self.pipeline.compute(self.data)
        drop_columns = res.columns.get_level_values(1).unique().drop(TO_GENERATOR)
        res = res.drop(drop_columns, axis=1, level=1)
        self.data = res.values.T


class Generator:
    def __init__(self):
        pass

    def add_timeline(self, name: str, data: Union[pd.DataFrame, pd.Series, np.ndarray]):
        pass

    def add_pipeline(self, name: str, data: pd.DataFrame, pipeline: Pipeline):
        pipeline.assert_computable(data)

        self.pipelines[name] = pipeline

    def compute(self, nb_scn) -> Composition:
        pass
