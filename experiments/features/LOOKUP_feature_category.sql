/* schema creation for feature lookup table _feature_category.csv */
CREATE TABLE wake._feature_category (
	feature_name VARCHAR(255) NOT NULL, 
	table_name VARCHAR(255) NOT NULL, 
	feature_category_primary VARCHAR(255) NOT NULL, 
	exclude_when_modeling INTEGER NOT NULL
);