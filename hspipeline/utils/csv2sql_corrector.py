import os
import pandas as pd
import os
import re

def edit_csv2sql(file_name, to_file_name):
	"""takes a file with delimiter (default ",") and replaces values specified and writes a new file"""

	def make_csv_line(line):
	    """reads a line and replaces exact_values then produces csv line"""
	    return str(line)[1:][:-1].replace("'","")

	def accomodate_escaped_commas(line, direction):
		if direction=="from_esc":
			return line.replace("\",\"",":COMMA:")
		elif direction=="to_esc":
			return line.replace(":COMMA:","\",\"")

	def line_length(line, runnning_max):
		"""counts length of characters in line """
		line=accomodate_escaped_commas(line, "from_esc")
		contender=[accomodate_escaped_commas(element, "to_esc") for element in line.split(",")]
		contender=[len(element) for element in contender]
		return [current if current>new else new for current, new in zip(runnning_max, contender) ]

	with open(file_name, 'r') as f:
		with open(to_file_name, 'w') as t:
			line=f.readline() 
			t.write(line)
			to_line=[0]*len(accomodate_escaped_commas(line, "from_esc").split(","))
			for line in f:
				to_line=line_length(line,to_line)
			t.write(make_csv_line(to_line) + '\n')
	return "Done."




def edit_all_csv2sql(direc, to_direc):
    """moves recursively through a directory and returns the list of files within it all subdirectories"""
    file_list=[]
    for element in os.listdir(direc):
    	if os.path.isdir(element):
    		edit_all_csv2sql(os.path.join(direc, element), os.path.join(to_direc, element))
    	else:
    		prefix, suffix=os.path.splitext(os.path.join(to_direc,element))
    		edit_csv2sql(os.path.join(direc,element), prefix +"_charcounts"+suffix)
    return "All done."


def edit_create_commands(command_file, key_file, count_directory, count_suffix="_charcounts" ):
	def cnt_dct(file_name):
		pre, post=os.path.splitext(file_name)
		pre1, pre2=pre.rsplit('/',1)
		columns=[]
		counts=[]
		with open(pre1+"/"+count_directory+"/"+pre2+count_suffix+post, 'r') as f:
			columns=[each.strip("\"").strip() for each in f.readline().split(",")]
			counts=[each.strip() for each in f.readline().split(",")]
		print pre1+"/"+count_directory+"/"+pre2+count_suffix+post
		print dict(zip(columns, counts))
		return dict(zip(columns, counts))

	prefix, suffix=os.path.splitext(command_file)
	keys={}
	with open(key_file, 'r') as key_file:
		for line in key_file:
			keys[line.split(";")[1].strip()]=line.split(";")[0]
	with open(command_file) as c:
		with open(prefix + "_edit"+suffix, 'w') as n:
			count_dict={}
			begun= False
			for line in c:
				if "CREATE TABLE" in line:
					begun =True
					name=line.strip("CREATE TABLE").split()[0].strip()
					count_dict=cnt_dct(keys[name])
				elif ");" in line:
					begun=False
				elif begun and "VARCHAR" in line:
					variable=re.sub("\"*","",line.split("VARCHAR")[0]).strip()
					line=re.sub("VARCHAR\(\d*\)", "VARCHAR("+count_dict[variable] +")", line)
				n.write(re.sub("NOT NULL","",line)+"\n")