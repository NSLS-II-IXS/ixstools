import ixstools
from ixstools.io import Specfile
import random
random.seed('test_io.py')
import pytest


@pytest.fixture
def specfile_object():
    return Specfile(ixstools.sample_spec_data)


def test_specfile_header_parsing(specfile_object):
    sf = specfile_object
    assert (sf.parsed_header['time_from_date'] ==
            sf.parsed_header['time_from_timestamp'])

    assert (len(sf.parsed_header['motor_spec_names']) ==
            len(sf.parsed_header['motor_human_names']))

    assert (len(sf.parsed_header['detector_spec_names']) ==
            len(sf.parsed_header['detector_human_names']))

    for scan in sf:
        assert (len(sf.parsed_header['motor_spec_names']) ==
                len(scan.motor_values))
