from setuptools import find_packages
from setuptools import setup

setup(
    name = 'hspipeline',
    version = '0.1',
    packages = find_packages(exclude=['*.etl', '*.etl.*', 'etl.*', 'etl']),

    # Project requirements.
    install_requires = ('matplotlib',
                        'numpy',
                        'pandas',
                        'pyyaml',
                        'scikit-learn',
                        'SQLAlchemy',
                        ),

    package_data = {
        # Include *.yaml.
        '': ['*.yaml'],
    },

    # Metadata.
    author = 'Team High School Graduation',
    description = ('A data science pipeline to predict whether students will '
                     'graduate from high school on time.'),
    license = 'MIT',
    url = 'https://github.com/dssg/education-highschool',
    )
