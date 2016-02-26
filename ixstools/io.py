import numpy as np
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt


def parse_specdate(specdate):
    # example spec date: 'Fri Feb 19 14:01:35 2016'
    return datetime.strptime(specdate, '%a %b %d %H:%M:%S %Y')


def noop(arg):
    return arg


spec_line_mapper = {
    '#E': ('time_from_timestamp', lambda x: datetime.fromtimestamp(int(x))),
    '#D': ('time_from_date', parse_specdate),
    # '#C': ('mode')
}


class Specfile:
    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        with open(self.filename, 'r') as f:
            scan_data = f.read().split('#S')
        scan_data = [section.split('\n') for section in scan_data]
        self.header = scan_data.pop(0)
        # parse header
        for line in self.header:
            if not line.startswith('#'):
                continue
            line_type, line_contents = line.split(' ', 1)
            attr, func = spec_line_mapper.get(line_type, (line_type[1:], noop))
            setattr(self, attr, func(line_contents))
            print(line)
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

    def plot(self, ax, column_names=None, x=None):
        """Plot the values contained in the spec versus some x.

        Parameters
        ----------
        ax : axes or array of axes
            One axes object or a list of axes objects of the same length as
            the number of column_names.
            If one axes object is passed, all lines will be plotted on the
            same axes object, otherwise each data channel will be plotted on
            its own axes object
        column_names : list, optional
            The list of column names to plot.
            Defaults to all column names
        x : string, optional
            The x axis to plot `column_names` against.
            Defaults to the first column in the spec file

        Returns
        -------
        arts : dict
            The line artists from the call to `ax.plot()`
        """
        if x is None:
            x = self.scan_data.columns[0]
        if column_names is None:
            column_names = list(self.scan_data.columns)
            column_names.remove(x)
        try:
            len(ax)
        except TypeError:
            iterable = ((col_name, ax) for col_name in column_names)
        else:
            if len(ax.ravel() != len(column_names)):
                raise ValueError("Please give me the same number of axes (%s) "
                                 "as column_names (%s)" % (len(ax.ravel(),
                                                           len(column_names))))
            iterable = zip(col_name, ax)

        arts = {}
        for y, ax in iterable:
            ax.cla()
            art, = ax.plot(self.scan_data[x], self.scan_data[y], label=y)
            arts[y] = art
            ax.legend(loc=0)
        return arts
