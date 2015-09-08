### Initialiation ###
import numpy as np

### Define function to convert column of integers with missing to string ###
# This is necessary because otherwise they get exported to csv as 12.0, etc. And then SQL thinks they're floats.
# See: http://pandas.pydata.org/pandas-docs/stable/gotchas.html#nan-integer-na-values-and-na-type-promotions

def int_with_NaN_tostr(int):
    if np.isnan(int):
        return "NaN"
    elif int.is_integer():
        return np.char.mod('%d', int)
    else:
        raise TypeError('Input is not an integer or NaN')

