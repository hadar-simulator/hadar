#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import pickle
import unittest
from unittest.mock import MagicMock

from hadar.optimizer.input import Study, Consumption
from hadar.optimizer.output import Result, OutputConsumption, OutputNode
from hadar.optimizer.remote.optimizer import _solve_remote_wrap


class MockRequest:
    pass


class MockResponse:
    def __init__(self, content, code=200):
        self.content = content
        self.status_code = code

class RemoteOptimizerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.study = Study(node_names=['a'], horizon=1) \
            .add_on_node('a', data=Consumption(cost=0, quantity=[0], name='load'))

        self.result = Result(nodes={
            'a': OutputNode(consumptions=[OutputConsumption(cost=0, quantity=[0], name='load')],
                            productions=[], links=[])})

    def test_success(self):
        requests = MockRequest()
        requests.post = MagicMock(return_value=MockResponse(pickle.dumps(self.result)))

        _solve_remote_wrap(study=self.study, url='localhost', token='pwd', rqt=requests)

        requests.post.assert_called_with(data=pickle.dumps(self.study), url='localhost', params={'token': 'pwd'})

    def test_404(self):
        requests = MockRequest()
        requests.post = MagicMock(return_value=MockResponse(content=None, code=404))

        self.assertRaises(ValueError,
                          lambda: _solve_remote_wrap(study=self.study, url='localhost', token='pwd', rqt=requests))

        requests.post.assert_called_with(data=pickle.dumps(self.study), url='localhost', params={'token': 'pwd'})

    def test_403(self):
        requests = MockRequest()
        requests.post = MagicMock(return_value=MockResponse(content=None, code=403))

        self.assertRaises(ValueError,
                          lambda: _solve_remote_wrap(study=self.study, url='localhost', token='pwd', rqt=requests))

        requests.post.assert_called_with(data=pickle.dumps(self.study), url='localhost', params={'token': 'pwd'})

    def test_500(self):
        requests = MockRequest()
        requests.post = MagicMock(return_value=MockResponse(content=None, code=500))

        self.assertRaises(IOError,
                          lambda: _solve_remote_wrap(study=self.study, url='localhost', token='pwd', rqt=requests))

        requests.post.assert_called_with(data=pickle.dumps(self.study), url='localhost', params={'token': 'pwd'})