import os
import csvkit
import subprocess
import io
import pandas as pd
import numbers
import decimal
import datetime
import math


def check_datetime(x):
    r = re.compile('\d{2,4}[\/-]\d{2}[\/-]\d{2,4}')
    k = re.compile('\d{4}')
    if r.match(x) or k.match(x):
        return True   
    else:
        return False

def numer_is_actually_categ(series):
	"""returns true if the guess is that the numeric seires is actually categorical"""
	return len(series.unique())<math.sqrt(len(series))


def all_files(direc):
    """moves recursively through a directory and returns the list of files within it all subdirectories"""
    file_list=[]
    for element in os.listdir(direc):
    	if os.path.isdir(element):
    		file_list=file_list+all_files(os.path.join(direc, element))
    	else:
    		file_list=file_list+[os.path.join(direc,element)]
    return file_list

def filter_ftype(file_list,ftype=".csv"):
	"""returns only desired file types--include the "."! """
	if ftype[0] != ".":
		ftype="."+ftype
	return [f for f in file_list if os.path.splitext(f)[1]==ftype]

def remove_files_by_ext(file_list, bad_extension):
	"""removes files from list that have a given extension"""
	if not bad_extension:
		return file_list
	else:
		return [f for f in file_list if f[-len(bad_extension):] != bad_extension]

def get_files(direc, ftype,bad_extension):
	"""returns the list of files anywhere in the directory or its subdirectories
		and does NOT have a bad_extension.  note: bad extesnion is important to
		not create more files"""
	file_list=all_files(direc)
	file_list=filter_ftype(file_list, ftype)
	return remove_files_by_ext(file_list, bad_extension)
 
def get_df(f, delimiter):
	"""returns a pandas dataframe after reading a csv, excel, sql, or json file"""
	ftype=os.path.splitext(f)[1]
	file_types=	{'.csv':pd.read_csv,'.xls':pd.read_excel,'.xlsx':pd.read_excel,'.sql':pd.read_sql,'.json':pd.read_json}
	if ftype in file_types:
		read_type=file_types[ftype]
		if ftype == ".csv":
			return read_type(f, sep=delimiter, error_bad_lines=False, )
		return read_type(f,error_bad_lines=False)
	else:
		print '"File type not supported.  Supported file types: csv, excel, sql, json"'
		return None

def check_numeric(series):
    """returns whether a pandas series contains a numeric data type"""
    number_types=["float16", "float32", "float64", "float128", "int8", "int16", "int32","int64","uint8", "uint16", "uint32", "uint64"]
    return series.dtype in number_types

def begin_csv(directory):
	header=['common_feature','path','variable','type','values_or_range','dist_or_std','mean_or_mode','median','n_rows','number_missing']
	with open(os.path.splitext(directory)[0]+'_variables.csv', 'w') as f:
		f.write(make_csv_line(header)+'\n')


def write_csv_line(directory,df, name="desc.csv"):
	"""takes a dataframe  and writes a descriptive csv of it"""
	with open(os.path.splitext(directory)[0]+'_variables.csv', 'a') as f:
		for variable in df.columns:
			f.write(make_csv_line( get_var_stats(name, df[variable]))+'\n')

def get_var_stats(name, series):
	"""returns categorical statistics or continuous statistics"""
	if check_numeric(series):
		return ['None',name ] +get_cont_stats(series)
	elif False:
		#to be converted if possible....
		return ['None',name]+ get_dt_stats(series)
	else:
		return ['None',name]+get_categ_stats(series)

def summarize_list(a_list):
	if len(a_list)<10:
		return a_list.sort()
	else:
		a_list.sort()
		return str(a_list[:3])+"..."+str(a_list[-3:]) +" total:" + str(len(a_list))

def categ_dist(series):
	return [series[series==value].count() for value in series.unique()]

#def prefix(func):   ##########i'll add decorators when i get the chance
#		def add_path(series):
#			return []
#	return add_path


#####THIS IS VERY MEMORY WASTING!!!!! CHANGE THE LAST ELEMENT!!!!!!!
def get_categ_stats(series):
	return [series.name, series.dtype, summarize_list(series.unique()),summarize_list(categ_dist(series)),series.mode(),'median',pd.isnull(series).count(), len(series[pd.isnull(series)])]

def get_cont_stats(series):
	return [series.name, series.dtype, [series.min(),series.max()],series.std(),series.mean(),'median',pd.isnull(series).count(), len(series[pd.isnull(series)])]

def get_dt_stats(series):
	###wishlisht function
	return ["get_date_time"]*7

def prep_list_for_csv(stats_list):
	return [str(element).replace(",","::") for element in stats_list]

def make_csv_line(line_list):
    """takes a list and writes it into a csv-style line"""
    return str(prep_list_for_csv(line_list))[1:][:-1].replace("'","")

def make_stats_dir(directory, ftype, bad_extension="_variables.csv", delimiter=","):
	file_names=get_files(directory, ftype, bad_extension)
	begin_csv(directory)
	for f in file_names:
		write_csv_line(directory,get_df(f, delimiter), os.path.splitext(f)[0])