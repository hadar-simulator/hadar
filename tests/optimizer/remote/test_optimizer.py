#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from hadar import RemoteOptimizer
from hadar.optimizer.input import Study
from hadar.optimizer.output import Result, OutputConsumption, OutputNode, OutputNetwork
from hadar.optimizer.remote.optimizer import check_code


class MockSchedulerServer(BaseHTTPRequestHandler):
    def do_POST(self):
        assert self.path == '/api/v1/study?token='

        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode())
        assert isinstance(Study.from_json(data), Study)

        self.send_response(200)
        body = json.dumps({'job': 123, 'status': 'QUEUED', 'progress': 1}).encode()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assert '/api/v1/result/123?token=' == self.path

        nodes = {'a': OutputNode(consumptions=[OutputConsumption(cost=0, quantity=[0], name='load')],
                                  productions=[], storages=[], links=[])}
        res = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

        self.send_response(200)
        body = json.dumps({'job': 123, 'status': 'TERMINATED', 'result': res.to_json()}).encode()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def handle_twice(handle_request):
    handle_request()  # one for Post /study
    handle_request()  # second for GET /result/123


class RemoteOptimizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.study = Study(horizon=1) \
            .network().node('a').consumption(cost=0, quantity=[0], name='load').build()

        nodes = {'a': OutputNode(consumptions=[OutputConsumption(cost=0, quantity=[0], name='load')],
                                  productions=[], storages=[], links=[])}
        self.result = Result(networks={'default': OutputNetwork(nodes=nodes)}, converters={})

    def test_job_terminated(self):
        # Start server
        httpd = HTTPServer(('localhost', 6964), MockSchedulerServer)
        server = threading.Thread(None, handle_twice, None, (httpd.handle_request,))
        server.start()

        optim = RemoteOptimizer(url='http://localhost:6964')
        res = optim.solve(self.study)

        self.assertEqual(self.result, res)

    def test_check_code(self):
        self.assertRaises(ValueError, lambda: check_code(404))
        self.assertRaises(ValueError, lambda: check_code(403))
        self.assertRaises(IOError, lambda: check_code(500))
