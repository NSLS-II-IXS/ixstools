from __future__ import division, print_function, absolute_import

from .io import Specfile
from .fit import fit
from argparse import ArgumentParser
import fnmatch
import os
import yaml
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import pdb
import tempfile
from pprint import pformat

def run(specfile, configfile, scans=None, x=None, y=None, logy=None):
    with open(os.path.abspath(configfile), 'r') as f:
        config = yaml.load(f.read())
    if scans:
        config['scans'] = [int(s) for s in scans]
    if x:
        config['x'] = x
    if y:
        config['y'] = y
    if logy:
        config['logy'] = logy

    # make the scans integers
    config['scans'] = [int(s) for s in config['scans']]
    if 'logy' in config:
        # make the logy truthy
        config['logy'] = bool(config['logy'])

    print('Loaded config.')
    print(config)
    return run_programmatically(specfile, **config)


def run_programmatically(specfile, x, y, scans, monitors,
                         interpolation_mode='linear',
                         densify_interpolated_axis=1,
                         output_dir='align_output',
                         output_sep=' ',
                         logy=True):
    # switch matplotlib to agg backend for making figures and saving to disk
    matplotlib.use('Agg')
    # make the output directory
    os.makedirs(output_dir, exist_ok=True)
    sf = Specfile(specfile)
    exposure_time = {sid: np.average(sf[sid].scan_data.Seconds) for sid in scans}
    metadata = {'exposure time': exposure_time}
    # get the dataframes that we care about
    # make sure all the scans have the columns that we care about
    data = []
    y_keys = {}
    for sid in scans:
        specscan = sf[sid]
        if not set(monitors) < set(specscan.col_names):
            raise KeyError(
                '{} are the specified monitors and are not a complete subset '
                'of the available columns in scan {}. '
                'Column names in this scan are {} and {} are not in this scan'
                ''.format(monitors, sid, specscan.col_names,
                          set(monitors).intersection(specscan.col_names)))
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
    y_data = [sf[sid].scan_data[y_keys] for sid in scans]
    # output the raw data and make some matplotlib plots
    for x_vals, y_sid, sid in zip(x_data, y_data, scans):
        fpath = os.path.join(output_dir, '%s-raw' % sid)
        df = y_sid.copy().set_index(x_vals)
        df.to_csv(fpath, output_sep)
        fig, ax = plt.subplots()
        df.plot(logy=logy, ax=ax)
        ax.set_title("Scan %s" % sid)
        ax.set_xlabel(x)
        ax.set_ylabel("Raw counts")
        plt.savefig(fpath + '.png')
        plt.close(fig)

    monitor_data = [{monitor: np.average(sf[sid].scan_data[monitor])
                     for monitor in monitors}
                    for sid in scans]
    # normalize by the monitor
    normed = [y.divide(np.product(list(monitor.values())), 'rows')
              for y, monitor in zip(y_data, monitor_data)]
    # output the normalized data
    for x_vals, norm_vals, sid in zip(x_data, normed, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'norm']))
        norm_vals.to_csv(fpath, output_sep)
    # fit all the data
    fits = [[fit(x, cols[col_name]) for col_name in cols]
            for x, cols in zip(x_data, normed)]
    metadata['fits'] = {}
    # output the fit data
    for x_vals, fit_output, sid in zip(x_data, fits, scans):
        df_dict = {col_name: f.best_fit.values for col_name, f in zip(y_keys, fit_output)}
        # pdb.set_trace()
        df = pd.DataFrame(df_dict, index=x_vals)
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'fit']))
        df.to_csv(fpath, output_sep)
        metadata['fits'][sid] = {
            col_name: f.fit_report() for col_name, f in zip(y_keys, fit_output)
        }
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
    diff = np.average([np.average([np.average(np.diff(x)) for x, y in z]) for z in zeroed])
    minval = np.min([np.min([np.min(x) for x, y in z]) for z in zeroed])
    maxval = np.max([np.max([np.max(x) for x, y in z]) for z in zeroed])
    # compute the new axes
    new_axis = np.arange(minval, maxval, diff / densify_interpolated_axis)
    # set up the interpolators
    interpolators = [[interp1d(x, y, kind=interpolation_mode,
                               bounds_error=False,
                               fill_value=np.nan)
                      for x, y in z] for z in zeroed]

    # Create the interpolated values categorized by scan
    interpolated = [
        pd.DataFrame({col_name: interp(new_axis) for col_name, interp in
                      zip(y_keys, interpolator)},
                     index=new_axis) for interpolator in interpolators]


    # output the interpolated data
    for interp_df, sid in zip(interpolated, scans):
        fpath = os.path.join(output_dir, '-'.join([str(sid), 'interpolated']))
        interp_df.to_csv(fpath, output_sep)

    summed_by_scan = pd.DataFrame({
        sid: interp_df.dropna().sum(axis=1)
        for sid, interp_df in zip(scans, interpolated)}, index=new_axis)

    # output the summed data
    fpath = os.path.join(output_dir, '-'.join([str(sid), 'summed']))
    summed_by_scan.to_csv(fpath, output_sep)

    # sum by detector
    summed_by_detector = pd.DataFrame({
        det_name: np.sum([df[det_name].values for df in interpolated], axis=0)
        for det_name in list(y_data[0].columns)}, index=new_axis)
    # write metadata to file
    fname = '-'.join([str(sid) for sid in scans]) + 'metadata'
    with open(os.path.join(output_dir,  fname), 'w') as f:
        f.write(pformat(metadata))
    fig, axes = plt.subplots(ncols=2)
    if logy:
        plotfunc = 'semilogy'
    else:
        plotfunc = 'plot'
    for ax, df, title in zip(axes, [summed_by_scan, summed_by_detector],
                             ["Aligned and summed by scan",
                              "Aligned and summed by detector"]):
        for col_name in df:
            getattr(ax, plotfunc)(df[col_name], label=str(col_name),
                                  marker='o')
        ax.legend(loc=0)
        ax.set_title(title)
        ax.set_xlabel(r'$\Delta$E')
        ax.set_ylabel("Normalized counts per second")
        ax.axvline(linewidth=3, color='k', linestyle='--')
    fname = '-'.join([str(s) for s in scans] + ['final']) + '.png'
    plt.savefig(os.path.join(output_dir, fname))
    plt.show()
    return (x_data, monitor_data, y_data, normed, fits, zeroed, interpolated,
            summed_by_scan, scans, metadata)


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
