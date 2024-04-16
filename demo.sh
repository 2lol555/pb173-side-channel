#!/bin/bash

# install dependencies

# if packages are managed externally create virtual enviroment
# python3 -m venv env
# source ./env/bin/activate

pip install -r requirements.txt

cd ./peak-alignment/
python3 alignment.py --help
# python3 alignment.py <path-to-trace> -s 14000 -w 4000 -n 1000 

# cd ../
# deactivate
