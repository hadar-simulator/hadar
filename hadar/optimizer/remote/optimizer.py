#  Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
#  See AUTHORS.txt
#  This Source Code Form is subject to the terms of the Apache License, version 2.0.
#  If a copy of the Apache License, version 2.0 was not distributed with this file, you can obtain one at http://www.apache.org/licenses/LICENSE-2.0.
#  SPDX-License-Identifier: Apache-2.0
#  This file is part of hadar-simulator, a python adequacy library for everyone.
import logging
import sys
from time import sleep

import requests
from progress.bar import Bar
from progress.spinner import Spinner

from hadar.optimizer.input import Study
from hadar.optimizer.output import Result

logger = logging.getLogger(__name__)


class ServerError(Exception):
    def __init__(self, mes: str):
        super().__init__(mes)


def check_code(code):
    if code == 404:
        raise ValueError("Can't find server url")
    if code == 403:
        raise ValueError("Wrong token given")
    if code == 500:
        raise IOError("Error has occurred on remote server")


def solve_remote(study: Study, url: str, token: str = 'none') -> Result:
    """
    Send study to remote server.

    :param study: study to resolve
    :param url: server url
    :param token: authorized token (default server config doesn't use token)
    :return: result received from server
    """
    # Send study
    resp = requests.post(url='%s/api/v1/study' % url, json=study.to_json(), params={'token': token})
    check_code(resp.status_code)

    # Deserialize
    resp = resp.json()
    id = resp['job']

    Bar.check_tty = Spinner.check_tty = False
    Bar.file = Spinner.file = sys.stdout
    bar = Bar('QUEUED', max=resp['progress'])
    spinner = None

    while resp['status'] in ['QUEUED', 'COMPUTING']:
        resp = requests.get(url='%s/api/v1/result/%s' % (url, id), params={'token': token})
        check_code(resp.status_code)
        resp = resp.json()

        if resp['status'] == 'QUEUED':
            bar.goto(resp['progress'])

        if resp['status'] == 'COMPUTING':
            if spinner is None:
                bar.finish()
                spinner = Spinner('COMPUTING           ')
            spinner.next()

        sleep(0.5)

    if resp['status'] == 'ERROR':
        raise ServerError(resp['message'])

    return Result.from_json(resp['result'])
