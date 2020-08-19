#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import json
import pickle
import unittest
from http.server import BaseHTTPRequestHandler
from typing import Dict, List, Tuple
from unittest.mock import MagicMock

from hadar import RemoteOptimizer
from hadar.optimizer.input import Study, Consumption
from hadar.optimizer.output import Result, OutputConsumption, OutputNode, OutputNetwork
from hadar.optimizer.remote.optimizer import _solve_remote_wrap, ServerError, check_code


class MockSchedulerServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode())

        assert self.path == '/study'
        assert isinstance(data, Study)

        self.send_response(200)
        body = json.dumps({'job': 123, 'status': 'QUEUED', 'progress': 1}).encode()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assert '/job/next' == self.path

        study = hd.Study(horizon=1)\
            .network()\
                .node('a')\
                    .consumption(name='load', cost=1000, quantity=10)\
                    .production(name='prod', cost=10, quantity=10)\
            .build()

        job = JobDTO(study=study, id='123', version='1', created=147, status='QUEUED')
        data = pickle.dumps(job)

        self.send_response(200)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def handle_twice(handle_request):
    handle_request()  # one for GET /job/next
    handle_request()  # second for POST /job/123

class RemoteOptimizerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.study = Study(horizon=1) \
            .network().node('a').consumption(cost=0, quantity=[0], name='load').build()

        nodes = { 'a': OutputNode(consumptions=[OutputConsumption(cost=0, quantity=[0], name='load')],
                                  productions=[], storages=[], links=[])}
        self.result = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

    def test_job_terminated(self):
        pass

    def eetest_job_error(self):
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

    def test_check_code(self):
        self.assertRaises(ValueError, lambda: check_code(404))
        self.assertRaises(ValueError, lambda: check_code(403))
        self.assertRaises(IOError, lambda: check_code(500))

    def no_test_server(self):
        optim = RemoteOptimizer(url='http://localhost:5000')
        res = optim.solve(self.study)
        print(res)