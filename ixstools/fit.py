import os
import numpy as np
from lmfit.models import GaussianModel

def fit(x, y, bounds=None):
    """Fit a gaussian background to `field` in `scan`

    Parameters
    ----------
    x : array
    y : array
    bounds : The +/- range to fit the data to

    Returns
    -------
    fit : lmfit.model.ModelFit
        The results of fitting the data to a gaussian peak

    Examples
    --------
    >>> fit = fit_gaussian(scan.scan_data)
    >>> fit.plot()
    """
    gaussian = GaussianModel()
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
    gaussian_params = gaussian.guess(y, x=x, center=center)
    model = gaussian
    return model.fit(y, x=x, params=gaussian_params)
