conf  = {
    # name of the x axis
    'x': 'HRM_En',
    # the name of the detector(s). Respects standard file globbing
    'y': 'TD*',
    # the name of the monitor column
    'monitors': ['SRcur', 'PD11'],
    # the scans that you wish to process
    'scans': [20, 22],
    # interpolation mode options are
    # 'linear'
    # 'nearest'
    # 'zero'
    # 'slinear'
    # 'quadratic
    # 'cubic'
    # where 'slinear', 'quadratic' and 'cubic' refer to a spline interpolation
    # of first, second or third order)
    'interpolation_mode': 'linear',
    # The multiplicative factor to increase (>1) or decrease (<1) the interpolated
    # axis
    'densify_interpolated_axis': 1,
    # Folder to write the data (respects relative and absolute paths).
    # Defaults to 'align_output' folder in current directory
    'output_dir': 'align_output/',
    # The separator in the output files.
    # Defaults to space: ' '
    'output_sep': ',',
    # Plot *all* plots with a log scale on the y axis.
    # Defaults to True
    'logy': True,
}