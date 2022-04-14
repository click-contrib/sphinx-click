import shutil

import pytest
from sphinx.testing import path

# this is necessary because Sphinx isn't exposing its fixtures
# https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
pytest_plugins = ['sphinx.testing.fixtures']


@pytest.fixture
def rootdir(tmpdir):
    src = path.path(__file__).parent.abspath() / 'roots'
    dst = tmpdir.join('roots')
    shutil.copytree(src, dst)
    roots = path.path(dst)
    print(dst)
    yield roots
    shutil.rmtree(dst)
