# [DSSG 2015: High School Graduation](http://dssg.github.io/education-highschool)

This is a 2015 [Data Science for Social Good](http://www.dssg.io) project focused on using data science methods to help several partner public school districts improve their respective high school graduation rates and outcomes.


## Directories
+ [`/experiments`](experiments):  Experimental results generated via our data science pipeline.
+ [`/hspipeline`](hspipeline):  Data science pipeline that generates predictive model output from raw data input.
+ [`/presentations`](presentations):  Presentation material for deep dives, meetups, partner updates, etc.
+ [`/resources`](resources):  Literature and material related to partner districts and project topic.


## Team Members
+ Kerstin Frailey
+ Robin Gong
+ Siobhan Greatorex-Voith
+ Reid Johnson


## Quickstart

Starting from a standard AWS install (Ubuntu):

1. Install the [Anaconda Scientific Python Distribution](http://continuum.io/downloads). We did most of our analyses using [Python](https://www.python.org/) using Anaconda, a free enterprise-ready Python distribution for large-scale data processing, predictive analytics, and scientific computing.
2. Clone this  repository using Git. [Git](http://git-scm.com/) is used version control system we used to orginize our code. We hosted the code on [Github](http://github.com/). You can download Git [here](http://git-scm.com/downloads). Information on getting started with Git is [here](http://git-scm.com/book/en/Getting-Started-Git-Basics). Additionally, you will need to create a Github account. Once you have installed Git, you will need to navigate in command line to the folder in which you want to download the code. Then you will need to clone the respository.
3. Create a file ```config.yaml``` in the [`/experiments`](experiments) directory that conforms to the provided ```config.yaml.example``` file.
4. Follow the ```Example.ipynb``` IPython Notebook in the [`/experiments`](experiments) directory.


## Copyright and License

Code is copyright 2015 Data Science for Social Good Summer Fellowship and released under [the MIT license](LICENSE).
