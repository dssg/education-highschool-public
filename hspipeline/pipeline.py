import csv
import hashlib
import io
import itertools
import json
import logging
import os
import random
import re
import time

import matplotlib.pylab as plt
import numpy as np
import pandas as pd
from sklearn import cross_validation
from sklearn import metrics
from sklearn.base import TransformerMixin
from sklearn.cross_validation import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import Imputer
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import config
from utils.database import connect as db_connect

log_filepath = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_filepath): os.makedirs(log_filepath)

localtime = time.localtime() # For naming log files
log_time = '{:04d}_{:02d}_{:02d}'.format(localtime.tm_year, localtime.tm_mon, localtime.tm_mday)
logging.basicConfig(filename=os.path.join(log_filepath, 'classification' + log_time + '.log'), 
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

class DataFrameImputer(TransformerMixin):
    def __init__(self):
        """Impute missing values.

        Columns of dtype object are imputed with the most frequent value 
        in column.

        Columns of other types are imputed with mean of column.

        """
    def fit(self, X, y=None):

        self.fill = pd.Series([X[c].value_counts().index[0]
            if X[c].dtype == np.dtype('O') else X[c].mean() for c in X],
            index=X.columns)

        return self

    def transform(self, X, y=None):
        return X.fillna(self.fill)

def subsample(X, y, subsample_ratio=1.0):
    """Data subsampling.

    This function takes in a list or array indexes that will be used for training
    and it performs subsampling in the majority class (c == 0) to enforce a certain ratio
    between the two classes.

    Parameters
    ----------
    X : np.ndarray
        The entire dataset as a ndarray.
    y : np.ndarray
        The labels.
    subsample_ratio : float
        The desired ratio for subsampling.

    Returns
    --------
    np.ndarray 
        The new list of array indexes to be used for training.
    """
    # Get indexes of instances that belong to classes 0 and 1.
    indexes_0 = np.where(y == 0)[0]
    indexes_1 = np.where(y == 1)[0]

    # Determine how large the new majority class set should be.
    sample_length = int(len(indexes_1) * subsample_ratio)
    if sample_length > len(indexes_0):
        print("Subsampling ratio is too large to subsample.")
        return np.concatenate((indexes_0, indexes_1), axis=1)
    else:
        samples_0 = random.sample(indexes_0, sample_length)
        sample_indexes = np.concatenate((samples_0, indexes_1), axis=1)
        return sample_indexes

#############################################################
# SMOTE implementation by Karsten Jeschkies.                #
# The MIT License (MIT)                                     #
# Copyright (c) 2012-2013 Karsten Jeschkies <jeskar@web.de> # 
#                                                           #
# This is an implementation of the SMOTE Algorithm.         #
# See: "SMOTE: synthetic minority over-sampling technique"  #
# by Chawla, N.V et al.                                     #
#############################################################

def SMOTE(T, N, k, h=1.0):
    """Synthetic minority oversampling.

    Returns (N/100) * n_minority_samples synthetic minority samples.

    Parameters
    ----------
    T : array-like, shape = [n_minority_samples, n_features]
        Holds the minority samples.
    N : percentage of new synthetic samples:
        n_synthetic_samples = N/100 * n_minority_samples. Can be < 100.
    k : int. Number of nearest neighbors.
    Returns
    -------
    S : Synthetic samples. array, 
        shape = [(N/100) * n_minority_samples, n_features]
    """
    n_minority_samples, n_features = T.shape

    if N < 100:
        # Create synthetic samples only for a subset of T.
        # TODO: Select random minortiy samples.
        N = 100
        pass

    if (N % 100) != 0:
        raise ValueError("N must be less than or a multiple of 100.")

    N = N / 100
    n_synthetic_samples = N * n_minority_samples
    S = np.zeros(shape=(n_synthetic_samples, n_features))

    # Learn nearest neighbors.
    neigh = NearestNeighbors(n_neighbors=k)
    neigh.fit(T)

    # Calculate synthetic samples.
    for i in xrange(n_minority_samples):
        nn = neigh.kneighbors(T[i], return_distance=False)
        for n in xrange(N):
            nn_index = random.choice(nn[0])
            # NOTE: nn includes T[i]; we don't want to select it.
            while nn_index == i:
                nn_index = random.choice(nn[0])
                
            dif = T[nn_index] - T[i]
            gap = np.random.uniform(low=0.0, high=h)
            S[n + i * N, :] = T[i, :] + gap * dif[:]

    return S

def extract_data(district):    
    engine = db_connect(config.settings['general']['database'])

    if district == 'wcpss':
        # Data that maps student IDs to cohorts.
        cohort_selection_query = ('''SELECT * 
            FROM wake._cohort 
            ORDER BY student_id 
            ;''')

        # Student-level features that are time-invariant.
        features_constant_selection_query = ('''SELECT * 
            FROM wake._cohort_feature 
            ORDER BY student_id 
            ;''')

        # Student-level features that are time-variant.
        features_by_time_selection_query = ('''SELECT * 
            FROM wake._cohort_by_year_feature 
            ORDER BY student_id 
            ;''')

        # Student-level feature categories.
        #features_categories_selection_query = ('''SELECT * 
        #    FROM wake._feature_category 
        #    ;''')
        
        # Student-level outcome labels.
        labels_selection = ('''SELECT * 
            FROM  wake._label 
            ORDER BY student_id 
            ;''')
    elif district == 'vps':
        # Data that maps student IDs to cohorts.
        cohort_selection_query = ('''SELECT * 
            FROM vancouver._cohort 
            ORDER BY student_id 
            ;''')

        # Student-level features that are time-invariant.
        features_constant_selection_query = ('''SELECT * 
            FROM vancouver._cohort_feature 
            ORDER BY student_id 
            ;''')

        # Student-level features that are time-variant.
        features_by_time_selection_query = ('''SELECT * 
            FROM vancouver._cohort_by_year_feature 
            ORDER BY student_id 
            ;''')

        # Student-level feature categories.
        features_categories_selection_query = ('''SELECT * 
            FROM vancouver._feature_category 
            ;''')
        
        # Student-level outcome labels.
        labels_selection = ('''SELECT * 
            FROM  vancouver._label 
            ORDER BY student_id 
            ;''')

    cohorts = pd.read_sql(sql=cohort_selection_query, con=engine)
    features_constant = pd.read_sql(sql=features_constant_selection_query, con=engine)
    features_by_time = pd.read_sql(sql=features_by_time_selection_query, con=engine)
    #feature_categories = pd.read_sql(sql=features_categories_selection_query, con=engine)
    feature_categories = None
    labels = pd.read_sql(sql=labels_selection, con=engine)

    return cohorts, features_constant, features_by_time, feature_categories, labels

def extract_instances(features, labels, unit_col):
    # The outcome label is assumed to be the last column in labels.
    labels = labels.rename(columns={labels.columns[-1]: 'label'})

    # Merge all data (identifier, feature(s), and label). Each instance should have one or more features and a label.
    data = pd.merge(features, labels, how='inner', on=[unit_col])

    return data

def extract_features(features_constant, features_by_time, unit_col, time_col, columns_to_dummy=None):
    def flatten_multi_index(df):
        mi = df.columns
        suffixes, prefixes = mi.levels
        col_names = []
        for (i_s, i_p) in zip(*mi.labels):
            col_names.append("{time_col}_{prefix}_{suffix}".format(time_col=str(time_col), 
                                                                   prefix=str(prefixes[i_p]), 
                                                                   suffix=str(suffixes[i_s]),
                                                                   ))
        df.columns = col_names
        return df

    # If a student has repeated a grade, take only the last record.
    features_by_time.drop_duplicates(subset=[unit_col, time_col], take_last=True, inplace=True)

    # Reshape the features by time so that there is one instance instance per identifier.
    features_by_time = flatten_multi_index(features_by_time.pivot(index=unit_col, columns=time_col)).reset_index()

    # Merge all feature data.
    features = pd.merge(features_constant, features_by_time, how='outer', on=[unit_col])

    # Encode nominal features to conform with scikit-learn.
    if columns_to_dummy is not None or isinstance(features, pd.Series):
        # Encode only specified feature columns.
        features = pd.get_dummies(features, columns=columns_to_dummy)
    else:
        # Encode all 'object' type feature columns.
        dummy_cols = [features.columns[i] for i, tp in enumerate(features.dtypes) if tp == 'object']
        for col in dummy_cols:
            #print('Encoding feature \"' + col + '\" ...')
            #print('Old dataset shape: ' + str(features.shape))
            temp = pd.get_dummies(features[col], prefix=col)
            features = pd.concat([features, temp], axis=1).drop(col, axis=1)
            #print('New dataset shape: ' + str(features.shape))
            #unique_vals, X[col] = np.unique(X[col], return_inverse=True)

    return features

def write_summary_results(output_file, output, headers):
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    if not os.path.exists(output_file):
        # Write headers to results CSV.
        with open(output_file, 'w+') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow([str(x) for x in headers])
    with open(output_file, 'r') as csvfile_read:
        # Write (append) to results CSV.
        with open(output_file, 'a') as csvfile_append:
            output_exist = []
            csvreader = csv.reader(csvfile_read)
            print
            for row in csvreader:
               output_exist.append(str(row[8]))
            csvwriter = csv.writer(csvfile_append, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in output:
                if str(row[8]) not in output_exist:
                    csvwriter.writerow([str(x) for x in row])
                else:
                    print("Summmary results already exist for this model configuration.")

def write_model_results(model_file, y_true, y_pred, y_prob, sid):
    if not os.path.exists(os.path.dirname(model_file)):
        os.makedirs(os.path.dirname(model_file))
    if not os.path.exists(model_file):
        # Write (append) to results CSV.
        with open(model_file, 'a') as csvfile_append:
            csvwriter = csv.writer(csvfile_append, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in zip(sid, y_true, y_pred, y_prob):
                csvwriter.writerow([str(x) for x in row])
    else:
        print("Model results already exist for this model configuration.")

def generate_models(clf_library):
    """
    This function returns a list of classifiers with all combinations of
    hyperparameters specified in the dictionary of hyperparameter lists.
    usage example:
        lr_dict = {
            'clf': LogisticRegression, 
            'param_dict': {
                'C': [0.001, 0.1, 1, 10], 
                'penalty': ['l1', 'l2']
                }
            }
        sgd_dict = {
            'clf': SGDClassifier, 
            'param_dict': {
                'alpha': [0.0001, 0.001, 0.01, 0.1], 
                'penalty': ['l1', 'l2']
                }
            }
        clf_library = [lr_dict, sgd_dict]
        generate_models(clf_library)
    """
    clf_list = []
    for i in clf_library:
        param_dict = i['param_dict']
        dict_list = [dict(itertools.izip_longest(param_dict, v)) for v in itertools.product(*param_dict.values())]
        clf_list = clf_list+[i['clf'](**param_set) for param_set in dict_list]
    return clf_list

def run_models(data, unit_col, time_col, cohort_col, X_cols, y_col, knowledge_date=True, X_categories=None, output_dir=''):
    dummy_dict = {
        'clf': DummyClassifier,
        'param_dict': {
            'strategy': ['stratified', 'uniform'],
            'random_state': [0],
            }
        }
    ab_dict = {
        'clf': AdaBoostClassifier,
        'param_dict': {
            'base_estimator': ['DecisionTreeClassifier'],
            'n_estimators': [5, 10, 25, 50],
            'learning_rate': [0.01, 0.1, 0.5, 1],
            'algorithm': ['SAMME', 'SAMME.R'],
            'random_state': [0],
            }
        }
    dt_dict = {
        'clf': DecisionTreeClassifier,
        'param_dict': {
            'criterion': ['entropy', 'gini'],
            'splitter': ['best', 'random'],
            'max_features': ['sqrt', 'log2', None],
            'max_depth': [3, 5, 10, 25, None],
            'random_state': [0],
            }
        }
    et_dict = {
        'clf': ExtraTreesClassifier,
        'param_dict': {
            'n_estimators': [5, 10, 25, 50, 100], 
            'criterion': ['entropy', 'gini'],
            'max_features': ['sqrt', 'log2', None],
            'max_depth': [3, 5, 10, 25, None],
            'bootstrap': [True, False],
            'random_state': [0],
            'n_jobs': [-1],
            }
        }
    gb_dict = {
        'clf': GradientBoostingClassifier,
        'param_dict': {
            'loss': ['deviance', 'exponential'],
            'learning_rate': [0.01, 0.1, 0.5, 1],
            'n_estimators': [5, 10, 25, 100],
            'max_depth': [3, 5, 10, 25, None],
            'subsample': [0.01, 0.1, 0.5, 1],
            'max_features': ['sqrt', 'log2', None],
            'random_state': [0],
            }
        }
    lr_dict = {
        'clf': LogisticRegression,
        'param_dict': {
            'penalty': ['l1', 'l2'],
            'C': [0.001, 0.01, 1, 10],
            'random_state': [0],
            }
        }
    mnb_dict = {
        'clf': MultinomialNB,
        'param_dict': {
            'alpha': [0.0001, 0.001, 0.01, 0.1], 
            'C': [0.001, 0.01, 1, 10],
            }
        }
    rf_dict = {
        'clf': RandomForestClassifier, 
        'param_dict': {
            'n_estimators': [5, 10, 25, 50, 100], 
            'criterion': ['entropy', 'gini'],
            'max_features': ['sqrt', 'log2', None],
            'max_depth': [3, 5, 10, 25, None],
            'bootstrap': [True, False],
            'random_state': [0],
            'n_jobs': [-1],
            }
        }
    sgd_dict = {
        'clf': SGDClassifier, 
        'param_dict': {
            'alpha': [0.0001, 0.001, 0.01, 0.1], 
            'penalty': ['l1', 'l2'],
            'random_state': [0],
            }
        }
    svm_dict = {
        'clf': SVC, 
        'param_dict': {
            'C': [0.001, 0.01, 0.1, 1, 10],
            'kernal': ['poly', 'rbf', 'sigmoid'],
            'probability': [True],
            'random_state': [0],
            }
        }

    rf_best_dict = {
        'clf': RandomForestClassifier, 
        'param_dict': {
            'n_estimators': [5, 50], 
            'criterion': ['entropy'],
            'max_features': [None, 'log2'],
            'max_depth': [3, 10],
            'bootstrap': [True],
            'random_state': [0],
            'n_jobs': [-1],
            }
        }

    rf_very_best_dict = {
        'clf': RandomForestClassifier, 
        'param_dict': {
            'n_estimators': [50], 
            'criterion': ['entropy'],
            'max_features': [None],
            'max_depth': [3],
            'bootstrap': [True],
            'random_state': [0],
            'n_jobs': [-1],
            }
        }

    clf_library = [
                   dummy_dict,
                   #ab_dict, 
                   #dt_dict, 
                   #et_dict, 
                   #gb_dict, 
                   #lr_dict, 
                   #mnb_dict, 
                   #rf_dict, 
                   rf_best_dict, 
                   #rf_very_best_dict, 
                   #sgd_dict, 
                   #svm_dict, 
                   ]

    # Make sure clf_library is iterable (a list).
    if type(clf_library) is not list:
        clf_library = [clf_library]
    # Generate list of instantiated objects from list of dictionaries.
    clf_library = generate_models(clf_library)

    # Feature category sets to use for modeling.
    feat_sets = [['all']]
    if X_categories is not None:
        print X_categories.head()
        # Determine the unique feature categories.
        unique_categories = X_categories['feature_category_primary'].unique()
        # Drop featue categories that should not be used for modeling.
        categories_to_drop = np.array(['id', 'attendance', 'coursework', 'demographic', 'school'])
        unique_categories = np.array(list(set(x for x in unique_categories.tolist()).difference(set(x for x in categories_to_drop.tolist()))))
        # Add single feature categories to the feature sets.
        feat_sets.extend([[x] for x in unique_categories])
        # Add all but single feature categories to the feature sets.
        feat_sets.extend(list(itertools.combinations(unique_categories, len(unique_categories)-1)))
        # Add all categories to the feature sets.
        feat_sets.extend(list(itertools.combinations(unique_categories, len(unique_categories))))

    # Dataset modifiers to use prior to modeling (all combinations)
    mod_dict = {
        'subsample_rate':        [None],
        'oversample_rate_SMOTE': [None],
        #'subsample_rate':        [None, 1.0, 2.5, 5.0],
        #'oversample_rate_SMOTE': [None, 100, 200, 500],
        'imputation':            ['mean'],
        }
    mod_names = sorted(mod_dict)
    mod_sets = [dict(zip(mod_names, product)) for product in itertools.product(*(mod_dict[mod_names] for mod_names in mod_names))]

    top_k = [.001, .002, .005, .01, .02, .05, .1, .5, 1]

    results = []

    train_only_most_recent = True
    train_cohort_years = None
    test_only_most_recent = False
    #test_cohort_years = range(2011, 2016)
    test_cohort_years = [2014]
    grades = range(6, 12)
    evaluations = ['accuracy', 'brier', 'f1', 'roc', 'prc', 'precision', 'recall']

    cohorts = sorted(data[cohort_col].unique())
    cohorts_train = cohorts[:-1]
    cohorts_test = cohorts[1:]
    if train_cohort_years is not None:
        cohorts_train = train_cohort_years
    if test_cohort_years is not None:
        cohorts_test = test_cohort_years

    print("Grades %s" % grades)
    print("Cohorts %s" % cohorts)

    for cohort in cohorts:
        print("Cohort %s with shape %s" % (cohort, data[data['cohort'] == cohort].shape))

    # Iterate over grade levels.
    for grade in grades:
        print("==========\nGrade %s\n==========" % grade)

        X_cols_filtered = X_cols

        # Filter features from higher grade levels.
        X_cols_filtered_by_grade = X_cols_filtered
        highest_grade = 12
        higher_grade_regex = '^(?!' # negation
        if grade < highest_grade:
            for higher_grade in range(grade+1, highest_grade+1):
                higher_grade_regex += r"{time_col}_{grade_level}|".format(time_col=str(time_col), 
                                                                          grade_level=str(higher_grade)
                                                                          )
            higher_grade_regex = higher_grade_regex[:-1] # remove last '|'
            higher_grade_regex = higher_grade_regex + ').*'
            #data = data.filter(regex=higher_grade_regex)
            regex = re.compile(higher_grade_regex)
            # The regex should select all columns except those prefixed by a higher grade level.
            X_cols_filtered_by_grade = filter(lambda i: regex.search(i), X_cols_filtered_by_grade)


        # Iterate over feature sets.
        for features in feat_sets:
            print("  Features: %s" % ', '.join(features))

            if X_categories is not None:
                # Filter to only columns/features to be used for modeling.
                filtered_feats = X_categories.loc[X_categories['exclude_when_modeling'] == 0]
                # Filter to only columns/features in the selected feature categories.
                filtered_feats = filtered_feats['feature_name'].loc[filtered_feats['feature_category_primary'].isin(features)]
                category_regex = '('
                for feat in filtered_feats:
                    category_regex += r"{feat}|".format(feat=str(feat))
                category_regex = category_regex[:-1] # remove last '|'
                category_regex = category_regex + ')'
                regex = re.compile(category_regex)
                # The regex should select all columns that are a member of each selected feature category.
                X_cols_filtered_by_grade_and_category = filter(lambda i: regex.search(i), X_cols_filtered_by_grade)

                print("  %i features." % (len(X_cols_filtered_by_grade_and_category)))
                if len(X_cols_filtered_by_grade_and_category) == 0:
                    continue
            else:
                X_cols_filtered_by_grade_and_category = X_cols_filtered_by_grade

            # Iterate over cohort train/test pairs.
            for train_year in cohorts_train:
                for test_year in cohorts_test:
                    # Train cohort must be prior to test cohort.
                    if train_year >= test_year:
                        continue
                    if knowledge_date:
                        # Train and test cohorts must be separated according to grade level.
                        if train_year > test_year - (12 - grade):
                            continue
                    # Train only on the latest possible cohort, given the test cohort.
                    #if (train_only_most_recent == True) and (train_year != test_year - (12 - grade)):
                    #    continue
                    # Test only on the most recently available cohort.
                    if (test_only_most_recent == True) and (test_year != cohorts[-1]):
                        continue
                    print("  %s %s" % (train_year, test_year))

                    train_and_test = data[(data['cohort'] <= train_year) | (data['cohort'] >= test_year)]

                    # Set training/testing labels (train = 0, test = 1).
                    kf_labels = np.where((train_and_test['cohort'] >= test_year), 1, 0)

                    if len(kf_labels[kf_labels == 0]) == 0:
                        print("No training data.")
                    if len(kf_labels[kf_labels == 1]) == 0:
                        print("No testing data.")
                    if len(kf_labels[kf_labels == 0]) == 0 or len(kf_labels[kf_labels == 1]) == 0:
                        continue

                    if kf_labels is not None:
                        # The cross-validation labels are our train/test cohorts.
                        kf = [(np.where(kf_labels == 0)[0], np.where(kf_labels == 1)[0])]
                    else:
                        kf = cross_validation.StratifiedKFold(train_and_test[y_col], n_folds=n_folds, shuffle=True)

                    X = train_and_test[X_cols_filtered_by_grade_and_category].as_matrix()
                    y = train_and_test[y_col].as_matrix()
                    sid = train_and_test[unit_col].as_matrix() # student IDs

                    # Iterate over train/test sets (only one iteration if on entire cohorts).
                    for train, test in kf:
                        X_train, X_test, y_train, y_test = X[train], X[test], y[train], y[test]
                        sid_train, sid_test = sid[train], sid[test]

                        print("  %i training instances and %i testing instances." % (len(X_train), len(X_test)))
                        print("  %i class 0 instances in the training data." % len(y_train[y_train == 0]))
                        print("  %i class 1 instances in the training data." % len(y_train[y_train == 1]))
                        print("  %i class 0 instances in the testing data." % len(y_test[y_test == 0]))
                        print("  %i class 1 instances in the testing data." % len(y_test[y_test == 1]))
                        
                        # Iterate over dataset modifiers (imputation, sampling, etc.).
                        for mods in mod_sets:
                            imputation_method = mods['imputation']
                            oversample_rate_SMOTE = mods['oversample_rate_SMOTE']
                            subsample_rate = mods['subsample_rate']

                            # Copy the training data and testing feature data before modifications.
                            X_train_t = np.copy(X_train)
                            y_train_t = np.copy(y_train)
                            X_test_t = np.copy(X_test)

                            # Imputation methods.
                            print "  Performing %s-based imputation" % str(imputation_method)
                            if imputation_method == 'mean':
                                #imp = Imputer(missing_values=np.nan, strategy='mean', axis=0)
                                #X_train_t = imp.fit_transform(X_train_t)
                                #X_train_t = DataFrameImputer().fit_transform(X_train_t)
                                X_train_t = pd.DataFrame(X_train_t).fillna(pd.DataFrame(X_train_t).mean().fillna(0)).as_matrix()
                                X_test_t = pd.DataFrame(X_test_t).fillna(pd.DataFrame(X_test_t).mean().fillna(0)).as_matrix()
                            elif imputation_method == 'regression':
                                pass

                            # Assert that there are no missing or infinite training values.
                            #assert not np.any(np.isnan(X_train_t) | np.isinf(X_train_t))
                            #assert not np.any(np.isnan(y_train_t) | np.isinf(y_train_t))

                            # Ensure the training data has at least two class labels.
                            if len(np.unique(y_train_t)) < 2:
                                print("Warning: The data contains only one class: %s" % (str(np.unique(y_train_t))))

                            # Sampling methods.
                            sampled = False
                            print "  Oversampling with SMOTE rate is %s" % str(oversample_rate_SMOTE)
                            print "  Subsample rate is %s" % str(subsample_rate)

                            if oversample_rate_SMOTE is not None:
                                print "  SMOTEing data..."
                                minority = X_train_t[np.where(y_train_t == 1)]
                                smoted = SMOTE(minority, oversample_rate_SMOTE, 5)
                                X_train_t = np.vstack((X_train_t, smoted))
                                y_train_t = np.append(y_train_t, np.ones(len(smoted), dtype=np.int32))
                                sampled = True
                            if subsample_rate is not None:
                                print "  Subsampling data..."
                                sampled = subsample(X_train_t, y_train_t, subsample_rate)
                                X_train_t = X_train_t[sampled]
                                y_train_t = y_train_t[sampled]
                                sampled = True

                            if sampled:
                                print("  Data sampled. There are now:")
                                print("  %i training instances and %i testing instances." % (len(X_train_t), len(X_test_t)))
                                print("  %i class 0 instances in the training data." % len(y_train_t[y_train_t == 0]))
                                print("  %i class 1 instances in the training data." % len(y_train_t[y_train_t == 1]))

                            # Iterate over classification models.
                            for i, clf in enumerate(clf_library):
                                clf_name = str(clf)[:str(clf).index('(')]
                                print("  Model: %s" % clf_name)
                                print("  Parameters: %s" % clf.get_params())

                                summary = {}
                                summary_headers = [
                                    'grade',
                                    'test',
                                    'train',
                                    'model',
                                    'params',
                                    'features',
                                    'subsampled',
                                    'smoted',
                                    'summary_hash',
                                    'acc',
                                    'brier',
                                    'f1',
                                    'roc_auc',
                                    'prc_auc',
                                    'recall',
                                    'pre',
                                    ]
                                for k in top_k:
                                    summary_headers.extend(['pre@' + str(k*100) + '%'])
                                for k in top_k:
                                    summary_headers.extend(['ap@' + str(k*100) + '%'])
                                for header in summary_headers:
                                    summary[header] = ''
                                summary['grade'] = grade
                                summary['model'] = clf_name
                                summary['params'] = clf.get_params()
                                summary['features'] = ', '.join(features)
                                summary['test'] = test_year
                                summary['train'] = train_year
                                summary['subsampled'] = ''
                                summary['smoted'] = ''
                                summary['summary_hash'] = ''
                                if oversample_rate_SMOTE is not None:
                                    summary['smoted'] = oversample_rate_SMOTE
                                if subsample_rate is not None:
                                    summary['subsampled'] = subsample_rate

                                y_pred = y_prob = y_true = [];
                                test_indexes = []

                                # Generate "probabilities" for the current hold-out sample being predicted.
                                fitted_clf = clf.fit(X_train_t, y_train_t)
                                #feature_importances = getattr(fitted_clf, 'feature_importances_', None)

                                # Generate predicted labels and label probabilities.
                                preds_ = fitted_clf.predict(X_test_t)
                                probas_ = fitted_clf.predict_proba(X_test_t)

                                # Define the actual test indexes and labels.
                                test_indexes = np.concatenate((test_indexes, test), axis=0)
                                y_true = np.concatenate((y_true, y_test), axis=0)

                                # Aggregated (if applicable) model predictions of labels and label probabilities.
                                y_pred = np.concatenate((y_pred, preds_), axis=0)
                                y_prob = np.concatenate((y_prob, probas_[:, 1]), axis=0)

                                if clf_name == 'RandomForestClassifier':
                                    features_list = train_and_test[X_cols_filtered_by_grade_and_category].columns.values

                                    # Fit a random forest with (mostly) default parameters to determine feature importance
                                    feature_importance = fitted_clf.feature_importances_

                                    # make importances relative to max importance
                                    feature_importance = 100.0 * (feature_importance / feature_importance.max())

                                    # A threshold below which to drop features from the final data set. Specifically, this number represents
                                    # the percentage of the most important feature's importance value
                                    fi_threshold = 1

                                    # Get the indexes of all features over the importance threshold
                                    important_idx = np.where(feature_importance > fi_threshold)[0]

                                    # Create a list of all the feature names above the importance threshold
                                    important_features = features_list[important_idx]
                                    print "\n", important_features.shape[0], "Important features(>", fi_threshold, "% of max importance):\n", \
                                            important_features

                                    # Get the sorted indexes of important features
                                    sorted_idx = np.argsort(feature_importance[important_idx])[::-1]
                                    print "\nFeatures sorted by importance (DESC):\n", important_features[sorted_idx]

                                    # Adapted from http://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_regression.html
                                    pos = np.arange(sorted_idx.shape[0]) + .5

                                    #importances_df = pd.DataFrame({'pos': pos.tolist(), 'feature_importance': feature_importance[important_idx][sorted_idx[::-1]]})
                                    #sns.barplot('pos', 'feature_importance', importances_df)

                                    f, ax = plt.subplots(figsize=(50, 15))

                                    plt.barh(pos, feature_importance[important_idx][sorted_idx[::-1]], align='center', color='#7777FF')
                                    plt.yticks(pos, important_features[sorted_idx[::-1]])
                                    plt.xlabel('Relative Importance', fontsize=35)
                                    plt.ylabel('Feature', fontsize=35)
                                    plt.title('Variable Importance')
                                    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                                        label.set_fontsize(20) # Size here overrides font_prop
                                    ax.legend(title="")

                                    #plt.draw()
                                    #plt.show()
                                    figure_dir = os.path.join(output_dir, 'figures')
                                    if not os.path.exists(figure_dir):
                                        os.makedirs(figure_dir) 
                                    plt.savefig(os.path.join(figure_dir, 'feature_importance_rf_' + str(grade) + '.pdf'), dpi=100, transparent=True)


                                # Iterate over evaluation metrics.
                                for evaluation in evaluations:
                                    metric_score = None

                                    if evaluation == 'accuracy':
                                        # Compute the accuracy.
                                        accuracy = metrics.accuracy_score(y_true, y_pred)
                                        if accuracy is not None:
                                            summary['acc'] = accuracy

                                    if evaluation == 'brier':
                                        # Compute the brier score.
                                        brier_score = metrics.brier_score_loss(y_true, y_prob)
                                        if brier_score is not None:
                                            summary['brier'] = brier_score

                                    if evaluation == 'f1':
                                        # Compute the F1 score.
                                        f1_score = metrics.f1_score(y_true, y_pred)
                                        if f1_score is not None:
                                            summary['f1'] = f1_score

                                    if evaluation == 'roc':
                                        # Compute the ROC curve and the area under the curve.
                                        mean_tpr = 0.0
                                        mean_fpr = np.linspace(0, 1, 100)

                                        fpr, tpr, thresholds = metrics.roc_curve(y_true, y_prob)
                                        mean_tpr += np.interp(mean_fpr, fpr, tpr)

                                        # Plot the ROC baseline.
                                        #pl.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Baseline')

                                        # Compute true positive rates.
                                        mean_tpr /= len(kf)
                                        mean_tpr[-1] = 1.0
                                        mean_auc = metrics.auc(mean_fpr, mean_tpr)

                                        # Plot the ROC curve.
                                        #pl.plot(mean_fpr, mean_tpr, 'k-',
                                        #        label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)

                                        #pl.xlim([-0.05, 1.05])
                                        #pl.ylim([-0.05, 1.05])
                                        #pl.xlabel('False Positive Rate')
                                        #pl.ylabel('True Positive Rate')
                                        #pl.title(models[ix] + ' ROC')
                                        #pl.legend(loc="lower right")
                                        #pl.show()

                                        if mean_auc is not None:
                                            summary[evaluation + '_auc'] = mean_auc

                                    elif evaluation == 'prc':
                                        # Compute overall precision, recall, and area under PR-curve.
                                        precision, recall, thresholds = metrics.precision_recall_curve(y_true, y_prob)
                                        pr_auc = metrics.auc(recall, precision)

                                        # Plot the precision-recall curve.
                                        #pl.plot(recall, precision, color='b', label='Precision-Recall curve (area = %0.2f)' % pr_auc)
                                        #pl.xlim([-0.05, 1.05])
                                        #pl.ylim([-0.05, 1.05])
                                        #pl.xlabel('Recall')
                                        #pl.ylabel('Precision')
                                        #pl.title(models[ix] + ' Precision-Recall')
                                        #pl.legend(loc="lower right")
                                        #pl.show()

                                        if pr_auc is not None:
                                            summary[evaluation + '_auc'] = pr_auc

                                    elif evaluation == 'recall':
                                        # Compute the recall.
                                        recall_score = metrics.recall_score(y_true, y_pred, average='binary')

                                        if recall_score is not None:
                                            summary[evaluation] = recall_score

                                    elif evaluation == 'precision':
                                        for k in top_k:
                                            # Compute the precision.
                                            precision = metrics.precision_score(y_true, y_pred)
                                            summary['pre'] = precision

                                            # Compute the precision on the top k%.
                                            ord_prob = np.argsort(y_prob,)[::-1] 
                                            r = int(k * len(y_true))

                                            if r == 0:
                                                pre_score_k = 0.0
                                            else:
                                                pre_score_k = np.sum(y_true[ord_prob][:r]) / r

                                            if pre_score_k is not None:
                                                summary['pre@' + str(k * 100) + '%'] = pre_score_k

                                            # Compute the average precision on the top k%.
                                            ap_score_k = 0.0
                                            num_hits = 0.0

                                            for i, p in enumerate(y_pred[:r]):
                                                if p in y_true and p not in y_pred[:i]:
                                                    num_hits += 1.0
                                                    ap_score_k += num_hits / (i + 1.0)

                                            if min(len(y_true), r) == 0:
                                                ap_score_k = 0.0
                                            else:
                                                ap_score_k = ap_score_k / min(len(y_true), r)

                                            if ap_score_k is not None:
                                                summary['ap@' + str(k * 100) + '%'] = ap_score_k

                                    elif evaluation == 'risk':
                                        # Output a list of the topK% students at highest risk along with their risk scores.
                                        #test_indexes = test_indexes.astype(int)
                                        #sort_ix = np.argsort(test_indexes)
                                        #students_by_risk = X.index[test_indexes]
                                        #y_prob = ((y_prob[sort_ix]) * 100).astype(int)
                                        #probas = np.column_stack((students_by_risk, y_prob))
                                        #r = int(top_k * len(y_original_values))
                                        #logging.info(models[ix] + ' top ' + str(100 * top_k) + '%' + ' highest risk')
                                        #logging.info('--------------------------')
                                        #logging.info('%-15s %-10s' % ('Student', 'Risk Score'))
                                        #logging.info('%-15s %-10s' % ('-------', '----------'))
                                        #probas = probas[np.argsort(probas[:, 1])[::-1]]
                                        #for i in range(r):
                                        #    output += '%-15s %-10d' % (probas[i][0], probas[i][1])
                                        #logging.info('\n')
                                        pass

                                summary_hash = str(hashlib.sha1(json.dumps((str(summary['grade']), 
                                                                           str(summary['test']), 
                                                                           str(summary['train']), 
                                                                           str(summary['model']), 
                                                                           str(summary['params']), 
                                                                           str(summary['features']), 
                                                                           str(summary['subsampled']), 
                                                                           str(summary['smoted'])), 
                                                                           sort_keys=True)).hexdigest())
                                summary['summary_hash'] = summary_hash
                                summary_output = []

                                if clf_name == 'DummyClassifier':
                                    summary_file = os.path.join(output_dir, 'summary_dummy.csv')
                                else:
                                    summary_file = os.path.join(output_dir, 'summary.csv')

                                for key in summary_headers:
                                    if key in summary:
                                        summary_output = [[summary[key] for key in summary_headers if key in summary]]
                                write_summary_results(summary_file, summary_output, summary_headers)

                                model_file = os.path.join(output_dir, 'predictions',
                                                          'grade', str(summary['grade']), 
                                                          'test', str(summary['test']), 
                                                          'train', str(summary['train']),
                                                          'model', str(summary['model']), 
                                                          str(summary['summary_hash']) + '.csv')
                                write_model_results(model_file, y_true, y_pred, y_prob, sid_test)

def fetch_data(district=None, from_pickle=False, pickle_filename=None, unit_col='student_id', time_col='grade_level'):
    if from_pickle == True and pickle_filename is not None:
        print("Reading pickle file.")
        data = pd.read_pickle(pickle_filename + '.pkl')
        if os.path.isfile(pickle_filename + '_cats' + '.pkl'):
            feature_categories = pd.read_pickle(pickle_filename + '_cats' + '.pkl')
        feature_categories = None
    else:
        # Retrieve time-invariant features, time-variant features, and outcome labels.
        cohorts, features_constant, features_by_time, feature_categories, labels = extract_data(district)
        features_by_time = features_by_time.drop(['cohort', 'academic_year'], 1)

        # Extract features.
        features = extract_features(features_constant, # time-invariant features
                                    features_by_time, # time-variant features
                                    unit_col=unit_col, # instance identifier column
                                    time_col=time_col, # time unit column
                                    )

        # Extract outcome labels.
        labels = labels[['student_id', 'outcome_label']]
        labels = labels.dropna()

        # Extract instance-level data. Each instance has an identifier, one or more features, and a label.
        data = extract_instances(features, labels, unit_col='student_id')

        if pickle_filename is not None:
            data.to_pickle(pickle_filename + '.pkl')
            if feature_categories is not None:
                feature_categories.to_pickle(pickle_filename + '_cats.pkl')

    return data, feature_categories

def do_model(input_dir, output_dir, district, unit_col, time_col, cohort_col, label_col, from_pickle=False, pickle_filename=None):
    print input_dir
    data, X_categories = fetch_data(district=district, 
                                    from_pickle=from_pickle, 
                                    pickle_filename=os.path.join(input_dir, pickle_filename), 
                                    unit_col=unit_col, 
                                    time_col=time_col
                                    )

    data = data.drop(['date_of_birth'], 1)

    if district == 'wcpss':
        data = data.drop(['age_first_entered_wcpss'], 1)
        data = data.drop(['age_entered_into_us'], 1)

    X_cols = data.columns[(data.columns != label_col) & (data.columns != unit_col) & (data.columns != time_col)]
    y_col = label_col
    run_models(data, unit_col, time_col, cohort_col, X_cols, y_col, 
               X_categories=X_categories, output_dir=output_dir)