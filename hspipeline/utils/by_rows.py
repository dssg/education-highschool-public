import os
import json

def update_cumulative(o_list, location, add):
	return o_list[:location] + [each+add for each in o_list[location:]]

def correct_length(length, line_list):
	if len(line_list)<length:
		return line_list+[""]*(length-len(line_list))
	elif len(line_list)==length:
		return line_list
	else:
		return line_list[:length]

def trim_formatting(line):
	return line.replace("\n","").replace("\r","").strip()

def separate_features(row, columns_numbers):
	return [[row[each] for each in columns_numbers ] , [row[each] for each in range(len(row)) if each not in columns_numbers]]

def list_to_line(row_list, append=False):
	if append:
		row_list=[""]+row_list
	return ",".join(row_list)

def process_line(line, unq_dict, columns, items):
	line=trim_formatting(line).split(",")
	key=[each for each in separate_features(line, columns)[0]]
	key=list_to_line(key)
	if key in unq_dict:
		unq_dict[key]+=[items]
	else:
		unq_dict[key]=[items]
	return unq_dict

def audit_unique(from_file, columns):
	unique={}
	place=0
	with open(from_file, 'r') as f:
		header=f.readline()
		place+=len(header) ###this skips the header
		for line in f:
			process_line(line, unique, columns,(place,place))
			place+=len(line)
	return unique

def update_feature_dict(f_dict, features):
	"""incriments the feature dictionary location by adding a new column"""
	for feature in features:
		f_dict[feature]=f_dict[feature]+[f_dict[feature][-1]+len(features)]
	return f_dict

def col_indices(line, names):
	return [line.index(name) for name in names]

def consolidate(orig_file, id_names, feature_names=None):
	"""takes a csv and reformats it to consoldate rows
		by unique values of given id_names (given in list!) """
	cons_file=os.path.splitext(orig_file)[0]+"_consolidate"+"_"+"_".join(id_names) +".csv" #make file name for by_rows
	with open(orig_file, 'r') as f: #get header
		head=trim_formatting(f.readline())
		header=head.split(",")
	cons_col=col_indices(header,id_names)
	if not feature_names:
		feature_names = separate_feature(header, cons_col)[1]
	feat_col=col_indices(header, feature_names)
	unique, replicates, end_stops=[["head"], [1], [len(head)]]
	head=list_to_line(id_names+feature_names)
	unique_dict=audit_unique(orig_file, cons_col)
	max_repl=max([len(unique_dict[key]) for key in unique_dict])
	repeated_feature_columns={feat:[col] for feat, col in zip(feature_names, feat_col)}
	for repl in range(1,max_repl):
		head_append=[each+"_"+str(repl) for each in feature_names]
		head= head+list_to_line(head_append, True)
		repeated_feature_columns=update_feature_dict(repeated_feature_columns, feature_names)	
	with open(cons_file, "w") as c:
		c.write(head)
		with open(orig_file,"r") as f:
			for unique in unique_dict:
				c.write("\n " + unique)
				i =0
				for location in unique_dict[unique]:
					f.seek(location[0])
					line=trim_formatting(f.readline()).split(",")
					c.write(list_to_line(separate_features(line, feat_col)[0],True))
					i+=1
				if i< max_repl:
					c.write(","*len(feat_col)*(max_repl-i))
	print "done"
	return cons_file,{unique_id:col for unique_id,col in zip(id_names, cons_col)}, repeated_feature_columns

def check_feature_columns(feature_names):
	no_problem=True
	indices=range(len(feature_names))
	for i in indices:
		if any([(feature_names[i] in feature_names[j]) for j in indices if j != i]):
			print "ERROR: FEATURE NAME CONFLICT"
			print feature_names[i]
	return no_problem

def list_counts(a_list):
	return {key:len([i for i in a_list if key==i]) for key in a_list}

def mode_of_list(a_list):
	mode=[] 
	counts=list_counts(a_list)
	mode=[]
	current_max=0
	for key in counts:
		if counts[key]>current_max: 
			mode, current_max=[key], counts[key]
		elif counts[key]==current_max:
			mode=mode+[counts[key]]
	return mode, current_max

def make_choice(unique_id, feature_name, values):
	"""prompts user to choose the value from a list to write to for a value conflict for a given feature """
	print str(unique_id) + " has a conflict in "+ feature_name 
	print "\t "+ " : ".join([str(val) for val in values])
	print "choose "+ " : ".join([ str(i)+ " for "+ str(val)  for i,val in  zip(range(len(set(values))), set(values))]) +" or N for Null or M for mode"
	choice=trim_formatting(raw_input("-->"))
	if choice in [str(i) for i in range(len(set(values)))]:
		return list(set(values))[int(choice)]
	elif choice in ["N"]:
		return ""
	elif choice in ["M"]:
		mode=mode_of_list(values)
		if len(mode)>1:
			print "There is more than one mode:"
			print mode
			return make_choice(unique_id, feature_name, values)
		else:
			return str(mode[0])
	else:
		print "INVALID INPUT"
		return make_choice(unique_id, feature_name, values)

def line_to_list(line):
	return trim_formatting(line).split(",")

def get_indices(full_list, column_names, partial_match=False):
	"""returns the indices of the first (partial_match=False) occurence of the column names
		or a list of the indices of the  occurences of the column_names"""
	if partial_match:
		return {key:[i for i in  range(len(full_list)) if key in full_list[i] ] for key in column_names}
	else: 
		return {key:next(i for i in  range(len(full_list)) if key == full_list[i] ) for key in column_names}

def process_header(header, id_names, feature_names):
	"""takes the header and id/feature NAMES andreturn the indices of the exact id_columns
		and a dictionary of the repeated feature columns with partial_match """
	header=line_to_list(header)
	return get_indices(header, id_names), get_indices(header, feature_names, True)

def prompt_column_names(input_file):
	"""prompts the user to choose the uique id and features from a csv header"""
	def check_feat_response(response, name, id_names, feature_names):
		if response=="F":
			feature_names=feature_names+[name]
		elif response=="U":
			id_names=id_names+[name]
		elif response=="N":
			pass
		else:
			print "ERROR: Response not recognized"
			response=raw_input("Please choose F, U, or N -->")
			id_names, feature_names= check_feat_response(response ,name, id_names, feature_names)
		return id_names, feature_names

	with open(input_file, "r") as f:
		line=f.readline()
		header=line_to_list(line)
	print "Please choose F, U, or N"
	id_names=[]
	feature_names=[]
	for name in header:
		print "Is " + name + " a feature (F),  part of the unique identifier (U), or neither (N)"
		response=raw_input("-->")
		id_names, feature_names=check_feat_response(response, name, id_names, feature_names)
	return id_names, feature_names


def check_duplicates(input_file, id_names, feature_names, log_file=None, id_indices= None, feature_indices=None):
	"""takes a csv, like the one made by consolidate, which has unique_ids and possibly repeated features
		and gets user feedback to write a file in which the features of a
		unique id are consolidated"""
	def get_logger(log_file):
		if log_file:
			with open(log_file, 'r') as log:
				choices_log=json.load(log)
		else:
			log_file=os.path.splitext(input_file)[0]+"_log.json" #make log file
			choices_log={}
		return log_file, choices_log

	if not check_feature_columns(feature_names):
		return False
	log_file, choices_log=get_logger(log_file)
	res_file=os.path.splitext(input_file)[0]+"_resolved.csv" ###make file to write to
	with open(input_file, "r") as f: ###open by-row file
		with open(res_file, "w") as r: ###open file to write to
			header=f.readline() #get the header
			if not id_indices and not feature_indices:
				id_indices, feature_indices =process_header(header, id_names, feature_names) #find which columns hold the info 
			r. write(list_to_line(id_names + feature_names)) #write the new csv header
			for line in f:
				info=line_to_list(line) #get the line into list format
				unique_id=list_to_line(separate_features(info, [id_indices[key] for key in id_names])[0]) #get the unique id for a row
				r.write("\n "+unique_id) # write the row's unique id
				if unique_id in choices_log:
					choices=choices_log[unique_id]
				else:
					choices={} #make a dictionary of 
				for feature_name in feature_indices:
					print info
					print feature_indices
					values=[info[ind] for ind in feature_indices[feature_name] if info[ind]] ###get the values in this line at the indices of the appropriate features
					if values==[values[0]]*len(values): #check if all values are the same
						value=values[0] #return the only value
					elif feature_name in choices and choices[feature_name][0]==values:
						value=choices[feature_name][1]
					else:
						value=make_choice(unique_id, feature_name, values) #ask user to choose value
						choices[feature_name]=[values, value]
					r.write(","+value) #write appropriate value for this feature
				choices_log[unique_id]=choices
	with open(log_file, "w") as log:
		json.dump(choices_log, log)		

def console_and_resolve(csv_file, id_names=None, feature_names=None, log_file=None, get_feat=False ):
	if not id_names and not feature_names:
		id_names,feature_names=prompt_column_names(csv_file)
	elif not feature_names:#defaults to remaining if only the
		with open(csv_file) as f:
			header=line_to_list(f.readline())
		feature_names = separate_feature(header, cons_col)[1]
	cons_file, id_col, feat_col=consolidate(csv_file, id_names, feature_names)
	check_duplicates(cons_file, id_names, feature_names, log_file, id_col, feat_col)