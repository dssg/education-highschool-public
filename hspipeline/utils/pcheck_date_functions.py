from datetime import date, datetime, timedelta
import math
import pandas as pd

def find_nth_pcheck_date(dt,n):
	'''Given a date, return the n'th persistence check date that comes after it'''

	# Function to shift forward one semester
	def find_next_pcheck_date(dt):
		'''Given a date, return the first persistence check date that comes after it'''

		if dt < datetime(dt.year,01,20):
			return datetime(dt.year,01,20)
		elif dt < datetime(dt.year,10,15):
			return datetime(dt.year,10,15)
		else:
			return datetime(dt.year+1,01,20)

	# Function to shift backward by one semester
	def find_prev_pcheck_date(dt):
		'''Given a date, return the first persistence check date that comes before it'''

		if dt <= datetime(dt.year,01,20):
			return datetime(dt.year-1,10,15)
		elif dt <= datetime(dt.year,10,15):
			return datetime(dt.year,01,20)
		else:
			return datetime(dt.year,10,15)

	# Check for null value
	if dt is pd.NaT: # Return "Not a Time" if given missing date
		return pd.NaT

	# Find the desired date
	retdate = dt
	if n>0:
		for _ in range(n):
			retdate = find_next_pcheck_date(retdate)
	elif n<0:
		for _ in range(n*-1):
			retdate = find_prev_pcheck_date(retdate)
	else:
		raise ValueError('Cannot find 0th magic date, n must be a positive or negative integer.')

	return retdate
