import ixstools
from ixstools.io import Specfile
import random
random.seed('test_io.py')
import pytest


@pytest.fixture
def datapath():
    return ixstools.sample_spec_data


def test_specfile(datapath):
    sf = Specfile(datapath)
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use('agg')
    fig, ax = plt.subplots()
    for scan in sf:
        # select a random column from within the spec file, but
        # because the seed is set, it will be the *same* random column
        # each time...
        col_name = random.choice(scan.col_names)
        arts = scan.plot(ax, column_names=[col_name])
        assert len(arts[col_name].get_xdata()) > 0
