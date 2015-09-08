#!/bin/bash
shopt -s expand_aliases
source ~/.bash_profile

#FILEPATH=~/dssgdat/
FILEPATH=/Users/Robin/Documents/dssg/education-highschool/experiments/features/
FILENAME=_feature_category.csv

cat $FILEPATH$FILENAME | psqlaws -c "\COPY wake._feature_category FROM STDIN with (format csv, header);"