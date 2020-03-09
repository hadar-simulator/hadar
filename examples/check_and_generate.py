from typing import List

import nbformat
import os
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

exporter = HTMLExporter()
ep = ExecutePreprocessor(timeout=600, kernel_name='python3', store_widget_state=True)


def read(name: str) -> nbformat:
    print('Reading...', end=' ')
    nb = nbformat.read('{name}/{name}.ipynb'.format(name=name), as_version=4)
    print('OK', end=' ')
    return nb


def execute(nb: nbformat, name: str) -> nbformat:
    print('Executing...', end=' ')
    ep.preprocess(nb, {'metadata': {'path': '%s/' % name}})
    print('OK', end=' ')
    return nb


def export(nb: nbformat, name: str):
    print('Exporting...', end=' ')
    html, _ = exporter.from_notebook_node(nb)
    with open('../docs/source/_static/examples/%s.html' % name, 'w') as f:
        f.write(html)
    print('OK', end=' ')


def list_notebook() -> List[str]:
    dirs = os.listdir('.')
    return [d for d in dirs if os.path.isfile('{name}/{name}.ipynb'.format(name=d))]


if __name__ == '__main__':
    for name in list_notebook():
        print(name, ':', end='')
        nb = read(name)
        nb = execute(nb, name)
        export(nb, name)
        print('')
