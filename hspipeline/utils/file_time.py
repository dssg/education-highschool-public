__author__ = "K. E. Frailey"
__credits__ = ["K. E. Frailey","Reid Johnson" ,"Data Science for Social Good"]
__version__ = "1"
__maintainer__ = "K. E. Frailey"
__email__ = "frailey@gmail.com"
__status__ = "Under Construction"


import logging
import os
import time

from ..config import settings

def time_file_name(string, suffix):
	localtime = time.localtime() # For naming log files
	log_time = '{:04d}_{:02d}_{:02d}'.format(localtime.tm_year, localtime.tm_mon, localtime.tm_mday)
	#return os.path.join(string, '_' + log_time + suffix)
	return string + '_' + log_time + suffix