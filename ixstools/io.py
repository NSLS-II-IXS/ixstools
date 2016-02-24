import numpy as np
import pandas as pd
import os

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
