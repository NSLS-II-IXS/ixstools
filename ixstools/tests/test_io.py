import ixstools
from ixstools.io import Specfile
import random
random.seed('test_io.py')
import pytest


@pytest.fixture
def specfile_object():
    return Specfile(ixstools.sample_spec_data)


def test_specfile_header_parsing(specfile_object):
    assert (specfile_object.parsed_header['time_from_date'] ==
            specfile_object.parsed_header['time_from_timestamp'])


def test_specfile_plotting(specfile_object):
    import matplotlib
    matplotlib.use('agg')
    fig, ax = matplotlib.pyplot.subplots()
    for scan in specfile_object:
        # select a random column from within the spec file, but
        # because the seed is set, it will be the *same* random column
        # each time...
        col_name = random.choice(scan.col_names)
        arts = scan.plot(ax, column_names=[col_name])
        assert len(arts[col_name].get_xdata()) > 0

