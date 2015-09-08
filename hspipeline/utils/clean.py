import os


def edit_file(file_name, to_file_name, delimiter=',', replacement_value=',', exact_values=[], near_values=[]):
	"""Takes a file with delimiter (default ","), replaces values specified, and writes a new file."""

	def replace_empty(in_question):
		if in_question.lower().strip().strip("\"") in exact_values or any(in_question.lower().strip() in near for near in near_values):
			return replacement_value
		else:
			return in_question

	def make_csv_line(line):
	    """Reads a line and replaces exact_values then produces CSV line."""
#	    line_list=[item.replace(",", "\",\"") for item in get_line(line, delimiter)] # bug: escapes each comma individually, even when part of a larger string
	    line_list=[item for item in get_line(line, delimiter)]
	    return str(line_list)[1:][:-1].replace("'","")

	def get_line(line, delimiter):
		"""Replaces exact_values with appropriate value."""
		return [replace_empty(col).strip() for col in line.split(delimiter)]

	with open(file_name, 'r') as f:
		with open(to_file_name, 'w') as t:
			for line in f:
				to_line=make_csv_line(line)
				t.write(to_line + '\n')

	return "Done."

exact_values = ['none', 'nan', 'na', '.', '\"n/a\"', '\"\"', 'null', 'n/a']