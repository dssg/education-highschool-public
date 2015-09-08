__author__ = "K. E. Frailey"
__credits__ = ["K. E. Frailey","Reid Johnson", "Data Science for Social Good"]
__version__ = "1"
__maintainer__ = "K. E. Frailey"
__email__ = "frailey@gmail.com"
__status__ = "Under Construction"

import pandas as pd


def make_dummies(X):
	dummy_cols = [X.columns[i] for i, tp in enumerate(X.dtypes) if tp == 'object']
	for col in dummy_cols:
	    temp = pd.get_dummies(X[col], prefix=col)
	    X = pd.concat([X, temp], axis=1).drop(col, axis=1)
	return X