import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from lmfit.models import LorentzianModel, LinearModel

class Specfile:
    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        with open(self.filename, 'r') as f:
            scan_data = f.read().split('#S')
        scan_data = [section.split('\n') for section in scan_data]
        self.header = scan_data.pop(0)
        self.scans = {}
        for scan in scan_data:
            sid = int(scan[0].split()[0])
            self.scans[sid] = Specscan(self, scan)

    def __getitem__(self, key):
        return self.scans[key]

    def __len__(self):
        return len(self.scans)-1

    def __iter__(self):
        return (self.scans[sid] for sid in sorted(self.scans.keys()))


class Specscan:
    def __init__(self, specfile, raw_scan_data):
        self.specfile = specfile
        self.raw_scan_data = raw_scan_data
        header_row = self.raw_scan_data.pop(0).split()
        self.scan_id = int(header_row.pop(0))
        self.scan_command = header_row.pop(0)
        self.scan_args = header_row
        for row in self.raw_scan_data:
            if row.startswith('#L'):
                self.col_names = row.split()[1:]
        scan_data = [row.split() for row in self.raw_scan_data
                     if not row.startswith('#') if row]
        self.scan_data = pd.DataFrame(
            data=scan_data, columns=self.col_names, dtype=float)
    def __repr__(self):
        return 'Specfile("%s")[%s]' % (self.specfile.filename, self.scan_id)

    def __str__(self):
        return str(self.scan_data)

    def __len__(self):
        return len(self.scan_data)

    def plot(self, column_names=None, x=None):
        if x is None:
            x = self.scan_data.columns[0]
        if column_names is None:
            column_names = self.scan_data.columns
        ncols = 2
        nrows = int(np.ceil(len(column_names)/ncols))
        try:
            self.ncols
            self.nrows
        except AttributeError:
            self.ncols = 0
            self.nrows = 0
        if self.ncols != ncols or self.nrows != nrows:
            self.ncols, self.nrows = ncols, nrows
            self.fig, self.axes = plt.subplots(nrows=nrows,
                                               ncols=ncols,
                                               figsize=(5*ncols, 2*nrows))
        self.arts = {}
        for data, ax in zip(column_names, self.axes.ravel()):
            ax.cla()
            self.arts[data] = ax.plot(self.scan_data[x], self.scan_data[data], label=data)
            ax.legend(loc=0)


def fit(x, y, bounds=None):
    """Fit a lorentzian + linear background to `field` in `scan`

    Parameters
    ----------
    scan : Specscan object
    field : The field to fit
    bounds : The +/- range to fit the data to

    Returns
    -------
    fit : lmfit.model.ModelFit
        The results of fitting the data to a linear + lorentzian peak

    Examples
    --------
    >>> fit = fit_lorentzian(scan.scan_data)
    >>> fit.plot()
    """
    lorentzian = LorentzianModel()
    linear = LinearModel()
    center = x[np.argmax(y)]
    if bounds is None:
        lower, upper = 0, len(x)
    else:
        lower = center - bounds
        upper = center + bounds
        if lower < 0:
            lower = 0
        if upper > len(x):
            upper = len(x)
    bounds = slice(lower, upper)
    y = y[bounds]
    x = x[bounds]
    lorentzian_params = lorentzian.guess(y, x=x, center=center)
    linear_params = linear.guess(y, x=x)
    lorentzian_params.update(linear_params)
    model = lorentzian + linear
    return model.fit(y, x=x, params=lorentzian_params)


def get_data(specfile, x, y, scan_ids):
    """Get some data out of a specfile

    Parameters
    ----------
    specfile : instance of Specfile
    x : string
        name of the 'x' axis
    y : list
        name(s) of the 'y' axes
    scan_ids : int or list
        scan numbers for which data should be retrieved

    Returns
    -------
    dict
        Dictionary of dataframes, keyed on the scan id
    """
    return {scan_id: f[scan_id].scan_data[[x]+y].copy() for scan_id in scan_ids}


if __name__ == "__main__":
    # the name of the file that you wish to open
    specfilename = '../data/20160219'
    # the name of the x column
    x = 'HRM_En'
    # the name of the detector (y column)
    y = ['PD21']
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
    print('scans = {}'.format(scans))
    output_path = '/tmp/foo'
    print('writing to {}'.format(output_path))

    f = Specfile(specfilename)

    data = get_data(f, x, y, scans)

    print("Scan keys in data = %s" % data.keys())
    #
    # normalized = [(x, y / f[scan_id].scan_data[monitor].values)
    #               for scan_id, (x, y) in zip(scans, raw)]
    # fits = [fit(xdata, ydata) for (xdata, ydata) in normalized]
    #
    # data = fit_and_align(params)
