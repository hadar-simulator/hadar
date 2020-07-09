#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.

import pickle
import unittest
from typing import Dict, List, Tuple
from unittest.mock import MagicMock

from hadar import RemoteOptimizer
from hadar.optimizer.input import Study, Consumption
from hadar.optimizer.output import Result, OutputConsumption, OutputNode
from hadar.optimizer.remote.optimizer import _solve_remote_wrap, ServerError


class MockResponse:
    def __init__(self, content, code=200):
        self.content = pickle.dumps(content)
        self.status_code = code


class MockRequest:
    def __init__(self, unit: unittest.TestCase, post: List[Dict], get: List[Dict]):
        self.unit = unit
        self._post = post
        self._get = get

    @staticmethod
    def cut_url(url):
        return url[4:]  # Remove 'host at the beginning

    def get(self, url, params):
        self.unit.assertEqual(self._get[0]['url'], MockRequest.cut_url(url))
        self.unit.assertEqual(self._get[0]['params'], params)
        res = self._get[0]['res']
        del self._get[0]
        return res

    def post(self, url, params, data):
        self.unit.assertEqual(self._post[0]['url'], MockRequest.cut_url(url))
        self.unit.assertEqual(self._post[0]['params'], params)
        self.unit.assertEqual(pickle.dumps(self._post[0]['data']), data)
        res = self._post[0]['res']
        del self._post[0]
        return res


class RemoteOptimizerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.study = Study(horizon=1) \
            .network().node('a').consumption(cost=0, quantity=[0], name='load').build()

        self.result = Result(nodes={
            'a': OutputNode(consumptions=[OutputConsumption(cost=0, quantity=[0], name='load')],
                            productions=[], links=[])})

    def test_job_terminated(self):
        requests = MockRequest(unit=self,
                               post=[dict(url='/study', params={'token': 'pwd'}, data=self.study,
                                          res=MockResponse({'job': 'myid', 'status': 'QUEUED', 'progress': 1}))
                                     ],
                               get=[dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'QUEUED', 'progress': 1})),
                                    dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'COMPUTING', 'progress': 0})),
                                    dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'TERMINATED', 'result': 'myresult'}))
                                    ])

        res = _solve_remote_wrap(study=self.study, url='host', token='pwd', rqt=requests)
        self.assertEqual('myresult', res)

    def test_job_error(self):
        requests = MockRequest(unit=self,
                               post=[dict(url='/study', params={'token': 'pwd'}, data=self.study,
                                          res=MockResponse({'job': 'myid', 'status': 'QUEUED', 'progress': 1}))
                                     ],
                               get=[dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'QUEUED', 'progress': 1})),
                                    dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'COMPUTING', 'progress': 0})),
                                    dict(url='/result/myid', params={'token': 'pwd'},
                                         res=MockResponse({'status': 'ERROR', 'message': 'HUGE ERROR'}))
                                    ])

        self.assertRaises(ServerError,
                          lambda: _solve_remote_wrap(study=self.study, url='host', token='pwd', rqt=requests))

    def test_404(self):
        requests = MockRequest(unit=self,
                               post=[dict(url='/study', params={'token': 'pwd'}, data=self.study,
                                          res=MockResponse(None, 404))],
                               get=[])
        requests.post = MagicMock(return_value=MockResponse(content=None, code=404))

        self.assertRaises(ValueError,
                          lambda: _solve_remote_wrap(study=self.study, url='host', token='pwd', rqt=requests))

    def test_403(self):
        requests = MockRequest(unit=self,
                               post=[dict(url='/study', params={'token': 'pwd'}, data=self.study,
                                          res=MockResponse(None, 403))],
                               get=[])

        self.assertRaises(ValueError,
                          lambda: _solve_remote_wrap(study=self.study, url='host', token='pwd', rqt=requests))

    def test_500(self):
        requests = MockRequest(unit=self,
                               post=[dict(url='/study', params={'token': 'pwd'}, data=self.study,
                                          res=MockResponse(None, 500))],
                               get=[])

        self.assertRaises(IOError,
                          lambda: _solve_remote_wrap(study=self.study, url='host', token='pwd', rqt=requests))

    def no_test_server(self):
        optim = RemoteOptimizer(url='http://localhost:5000')
        res = optim.solve(self.study)
        print(res)