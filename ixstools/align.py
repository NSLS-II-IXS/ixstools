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
import pdb
import tempfile

def run(specfile, configfile, scans=None, x=None, y=None):
    with open(os.path.abspath(configfile), 'r') as f:
        config = yaml.load(f.read())
    if scans:
        config['scans'] = [int(s) for s in scans]
    if x:
        config['x'] = x
    if y:
        config['y'] = y
    print('Loaded config.')
    print(config)
    return run_programmatically(specfile, **config)


def run_programmatically(specfile, x, y, scans, monitor,
                         interpolation_mode='linear',
                         densify_interpolated_axis=1,
                         output_dir='align_output',
                         output_sep=' '):
    # make the output directory
    os.makedirs(output_dir, exist_ok=True)
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
            # pdb.set_trace()
            if not set(y) < set(specscan.col_names):
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
    monitor_data = [sf[sid].scan_data[monitor] for sid in scans]
    y_data = [sf[sid].scan_data[y_keys] for sid in scans]
    # output the raw data
    for x_vals, monitor_sid, y_sid, sid in zip(x_data, monitor_data, y_data, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'raw']))
        df = y_sid.copy()
        df[monitor] = pd.Series(monitor_sid, index=x_vals)
        df.to_csv(fpath, output_sep)

    # normalize by the monitor
    normed = [y.divide(norm, 'rows') for y, norm in zip(y_data, monitor_data)]
    # output the normalized data
    for x_vals, norm_vals, sid in zip(x_data, normed, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'norm']))
        norm_vals.to_csv(fpath, output_sep)
    # fit all the data
    fits = [[fit(x, cols[col_name]) for col_name in cols]
            for x, cols in zip(x_data, normed)]
    # output the fit data
    for x_vals, fit_output, sid in zip(x_data, fits, scans):
        df_dict = {col_name: f.best_fit.values for col_name, f in zip(y_keys, fit_output)}
        # pdb.set_trace()
        df = pd.DataFrame(df_dict, index=x_vals)
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'fit']))
        df.to_csv(fpath, output_sep)
    # zero everything
    zeroed = [
        [(np.array(f.userkws['x'] - f.params['center'], dtype=float), f.data)
         for f in fit] for fit in fits]
    # output the zeroed data
    for zeroed_vals, sid in zip(zeroed, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'zeroed']))
        col_names = [['x-%s' % col_name, 'y-%s' % col_name] for col_name in y_keys]
        df_dict = {col_name: col
                   for col_name_pair, xy in zip(col_names, zeroed_vals)
                   for col_name, col in zip(col_name_pair, xy)}
        pd.DataFrame(df_dict).to_csv(fpath, output_sep)

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
    # output the interpolated data
    for interp_df, sid in zip(interpolated, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'interpolated']))
        interp_df.to_csv(fpath, output_sep)

    summed = [interp_df.dropna().sum(axis=1) for interp_df in interpolated]

    for sid, df in zip(scans, summed):
        plt.plot(df, label=str(sid))
    plt.legend(loc=0)
    plt.show()
    return (x_data, monitor_data, y_data, normed, fits, zeroed, interpolated,
            summed, scans)
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
    p.add_argument(
        '-s', '--scans',
        action='store',
        nargs='*'
    )
    p.add_argument(
        '-x',
        action='store',
        nargs='?',
    )
    p.add_argument(
        '-y',
        action='store',
        nargs='*'
    )

    args = p.parse_args()
    # turn the scans into integers
    args.scans = [int(s) for s in args.scans]
    print('Arguments from command line init')
    print(args)
    run(args.specfile, args.config, args.scans, args.x, args.y)
