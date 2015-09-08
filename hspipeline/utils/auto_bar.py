from __future__ import division
import pandas as pd
import os
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt



def remove_earlier_duplicates(dataframe, index, constraint_col):
    for item in dataframe[index].unique():
        duplicates=dataframe[index]==item
        evaluate=dataframe[duplicates]
        if len(evaluate[constraint_col])>1:
            max_val=evaluate[constraint_col].max
            retain_duplicate=dataframe[constraint_col]==max_val
            keepers=[max_dup or  not dupl for max_dup, dupl in zip(retain_duplicate.tolist(), duplicates.tolist())]
            dataframe=dataframe[keepers ]
    return dataframe

def cntgc_table_contents(dataframe, hier_list):
    dataframe=dataframe[hier_list]
    group_by_dict={}
    if len(hier_list)==0:
        return [len(dataframe)]
    else:
        upper=hier_list[0]
        uppers=dataframe[upper].unique()
        for each in uppers:
            this_group=dataframe[dataframe[upper]==each]
            group_by_dict[each]=cntgc_table_contents(this_group, hier_list[1:])
            total=sum([tot[0] for tot in group_by_dict.values()])
        return [total, group_by_dict]

def get_values(sub_list,grains):
	"""takes cntgc_table_contents output and outputs a list 
			of the elements of the cartesian products' counts for 
			all possible values the finest grain""" 
	finest_grain=grains[-1]
	plot_list=[]
	if len(grains)==1:
		return plot_list +[[sub_list[1][each][0] if each in sub_list[1] else 0 for each in finest_grain]]
	else:
		for grain in grains[0]:
			plot_list=plot_list+get_values(sub_list[1][grain], grains[1:])
		return plot_list

def cartesian_product(list_of_lists):
	"""takes a list of lists, outputs a list (of strings) of the cartesian product of the elements"""
	if len(list_of_lists)==1:
		return [""]
	else:
		c_product=[]
		for level in list_of_lists[0]:
			c_product=c_product+[str(level)+" "+str(element) for element in cartesian_product(list_of_lists[1:])]
        return c_product

def plot_values(dataframe, hier_list):
	"""returns a list of the counts for the lowest level, grouped into lists by cartesian product excluding lowest level"""
	grains=[dataframe[level].unique() for level in hier_list]
	return cartesian_product(grains), get_values(cntgc_table_contents(dataframe,hier_list), grains)

def make_bar_plot(dataframe, hier_list):
    """takes a (pandas) dataframe and a hierarchical list and outputs a bar plot
	    	 of the counts at the finest grain of the list by all other grains"""
    ###I stole the tableau20 scheme from a website
    tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),  
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),  
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),  
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),  
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]  
    for i in range(len(tableau20)):  
        r, g, b = tableau20[i]  
        tableau20[i] = (r / 255., g / 255., b / 255.)  

    def bars(data, bar_width, i=0,col='b', lab='lab'):
         return plt.bar(index+bar_width*i,data,width=bar_width,alpha=opacity,color=col,label=lab)

    finest_grain=dataframe[hier_list[-1]].unique()
    fig, ax = plt.subplots()
    index = np.arange(len(finest_grain))
    opacity = 0.4

    names, values= plot_values(dataframe,hier_list)
    bar_width = 1/(len(names)+1)

    i=0
    for value,name,color in zip(values,names, tableau20[:len(values)]):
        bar2=bars(value,bar_width,i, col=color,lab=name )   
        i+=1
    title=""
    for level in hier_list[:(-1)]:
        title= title+ level + " by "
    title= title+ " per " + hier_list[-1]
    plt.xlabel(hier_list[-1])
    plt.ylabel('Total Number')
    plt.title(title)
    plt.xticks(index + bar_width, finest_grain)
    plt.legend()

    plt.tight_layout()
    plt.show()
