__author__ = "K. E. Frailey"
__credits__ = ["K. E. Frailey", "Data Science for Social Good"]
__version__ = "1"
__maintainer__ = "K. E. Frailey"
__email__ = "frailey@gmail.com"
__status__ = "Under Construction"

"""
the purpose of this is to easily make, track, combine, and reference
features, labels, and row selections over time

we'll refer to features, labels, and row selections as 'datas'

the goals are:
	keep records
	reuse, update, and adopt datas to new ERDs

to get there, we need to:
	log datas
	reference created datas
	combine created datas
	build on existing datas
	map ERDs between eachother
	update ERDs
	map SQL from features between ERDS
"""

###make subfeature class for time (inheret)
####make post selection individual selection
####make features based on just a subseet (HIERARCHY/CONDITIONAL)

###note we can catually store these in a database if we want
#########WRITE A FUNCTION TO ADD An ELEMEnt TO A JSON FILE, ie write over last character ( "}") and write new key:item +"}"

from erd import *
from functools import wraps
import json
import os
from documenter import *


class Ftype:
	vrange=None
	def __init__(self,name):
		self.name=name

class Categorical(Ftype):
	def __init__(self, values): ###I CANT REMEMBER HOW TO PROPERLY OVERIDE INIT in inheritence
		if isinstance(values, list):
			self.range=values
		else:
			print "Categorical must be a list"
			raise TypeError

class OrdinalCategorical(Categorical):
	def _init_(self, values):
		self.values=values


class Numeric(Ftype):

	def __init__(self, v_range):
		if isinstance(v_range, tuple): ###PUT IN check if number condition as well--in old code i have a way!
			self.range=v_range
		else:
			print "Numeric must have a tuple range of numbers"
			raise TypeError
