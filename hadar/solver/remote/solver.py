import logging
import pickle

import requests

from hadar.solver.input import Study
from hadar.solver.output import Result


logger = logging.getLogger(__name__)


def solve_remote(study: Study, url: str, token: str = 'none') -> Result:
    """
    Send study to remote server.

    :param study: study to resolve
    :param url: server url
    :param token: authorized token (default server config doesn't use token)
    :return: result received from server
    """
    return _solve_remote_wrap(study, url, token, requests)


def _solve_remote_wrap(study: Study, url: str, token: str = 'none', rqt=None) -> Result:
    """
    Same method than solve_remote but with with request library in parameter to inject mock during test.

    :param study: study to resolve
    :param url: server url
    :param token: authorized token (default server config doesn't use token)
    :param rqt: requests library, main requests when use by user, mock when testing.
    :return: result received from server
    """
    # Send study
    resp = rqt.post(url=url, data=pickle.dumps(study), params={'token': token})
    if resp.status_code == 404:
        raise ValueError("Can't find server url")
    if resp.status_code == 403:
        raise ValueError("Wrong token given")
    if resp.status_code == 500:
        raise IOError("Error has occurred on remote server")
    # Deserialize
    result = pickle.loads(resp.content)
    logging.info("Result received from server")
    return result
