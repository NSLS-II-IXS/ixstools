import ixstools
from ixstools.io import Specfile
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
        col_name = scan.col_names[1]
        arts = scan.plot(ax, column_names=[col_name])
        assert len(arts[col_name].get_xdata()) > 0
