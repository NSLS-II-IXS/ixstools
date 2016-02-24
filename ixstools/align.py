from __future__ import division, print_function, absolute_import

from .io import Specfile
from .fit import fit
from argparse import ArgumentParser
import fnmatch
import os
import yaml
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


def run(specfile, configfile):
    with open(os.path.abspath(configfile), 'r') as f:
        config = yaml.load(f.read())
    return run_programmatically(specfile, **config)


def run_programmatically(specfile, x, y, scans, monitor,
                         interpolation_mode='linear',
                         densify_interpolated_axis=1):
    sf = Specfile(specfile)
    # get the dataframes that we care about
    # make sure all the scans have the columns that we care about
    data = []
    y_keys = {}
    for sid in scans:
        specscan = sf[sid]
        if monitor not in specscan.col_names:
            raise KeyError(
                '{} is the specified monitor and is not found in scan {}. '
                'Column names in this scan are {}'.format(
                    monitor, sid, specscan.col_names))
        if x not in specscan.col_names:
            raise KeyError(
                '{} is the specified x axis and is not found in scan {}. '
                'Column names in this scan are {}'.format(
                    x, sid, specscan.col_names))
        if '*' in y:
            # need to check to make sure that all the keys are in all the
            y_keys[sid] = fnmatch.filter(specscan.col_names, y)
        else:
            # set(A) < set(B) being True means that A is a subset of B
            # Make sure that all the keys that are specified in the config
            # are in the column names of the spec scan
            if not set(y_keys[sid]) < set(specscan.col_names):
                raise KeyError(
                    '{} are found in the config file under the "y:" section '
                    'but are not found in scan {}'
                    ''.format(set(y_keys[sid]).difference(specscan.col_names)))
    if y_keys:
        keys = list(sorted(y_keys))
        for k1, k2 in zip(keys, keys[1:]):
            if y_keys[k1] != y_keys[k2]:
                print('Scans have different y keys.\nScan {}: {}\nScan{}: {}'
                      ''.format(k1, y_keys[v1], k2, y_keys[k2]))
        y_keys = y_keys[keys[0]]
    else:
        y_keys = y

    # looks like we made it through the gauntlet!
    x_data = [sf[sid].scan_data[x] for sid in scans]
    norm_data = [sf[sid].scan_data[monitor] for sid in scans]
    y_data = [sf[sid].scan_data[y_keys] for sid in scans]
    # normalize by the monitor
    normed = [y.divide(norm, 'rows') for y, norm in zip(y_data, norm_data)]
    # fit all the data
    fits = [[fit(x, cols[col_name]) for col_name in cols]
            for x, cols in zip(x_data, normed)]
    # zero everything
    zeroed = [
        [(np.array(f.userkws['x'] - f.params['center'], dtype=float), f.data)
         for f in fit] for fit in fits]
    # compute the average difference between data points
    diffs = [np.average([np.average(np.diff(x)) for x, y in z]) for z in zeroed]
    minvals = [np.min([np.min(x) for x, y in z]) for z in zeroed]
    maxvals = [np.max([np.max(x) for x, y in z]) for z in zeroed]
    # compute the new axes
    new_axis = [np.arange(minval, maxval, diff / densify_interpolated_axis)
                for minval, maxval, diff in zip(minvals, maxvals, diffs)]
    # set up the interpolators
    interpolators = [[interp1d(x, y, kind=interpolation_mode,
                               bounds_error=False,
                               fill_value=np.nan)
                      for x, y in z] for z in zeroed]
    # Create a dict of the interpolated values so it can easily be passed to pandas
    interpolated = [
        pd.DataFrame({col_name: interp(axis) for col_name, interp in
                      zip(y_keys, interpolator)}, index=axis)
                    for axis, interpolator in
                    zip( new_axis, interpolators)]

    return x_data, norm_data, y_data, normed, fits, zeroed, interpolated, scans
    # fit it

    # plot it


def main():
    p = ArgumentParser(
        description="command line tool for aligning IXS formatted spec files")
    p.add_argument(
        'specfile',
        help='Path to the specfile you wish to parse'
    )
    p.add_argument(
        '-c', '--config',
        action='store',
        default='align.conf'
    )

    args = p.parse_args()
    run(args.config, args.specfile)


if __name__ == "__main__":
    # the name of the file that you wish to open
    specfilename = '/home/edill/dev/python/ixstools/data/20160219'
    # the name of the x column
    x = 'HRM_En'
    # the name of the detector (y column)
    y = 'TD*'
    # the name of the monitor column
    monitor = 'SRcur'
    # the scans that you wish to process
    scans = [18, 20, 22, 24]
    interpolation_mode = 'linear'
    # The number to divide the step size by
    # use a value < 1 for more interpolated points
    # use a value > 1 for less interpolated points
    densify_interpolated_axis_factor = 1
    # the name of the output file that you are going to write
    output_path = '/tmp/foo'

    print('scans = {}'.format(scans))
    print('writing to {}'.format(output_path))


    f = Specfile(specfilename)
    data = {scan_id: f[scan_id].scan_data[[x]+y].copy() for scan_id in scans}

    print("Scan keys in data = %s" % data.keys())
    #
    # normalized = [(x, y / f[scan_id].scan_data[monitor].values)
    #               for scan_id, (x, y) in zip(scans, raw)]
    # fits = [fit(xdata, ydata) for (xdata, ydata) in normalized]
    #
    # data = fit_and_align(params)
