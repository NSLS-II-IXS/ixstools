import os
import numpy as np
from lmfit.models import LorentzianModel, LinearModel


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
