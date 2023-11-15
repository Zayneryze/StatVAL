# TODO
# flask
# data analysis:
#   death location / kill locations
#   util location
#   spike plant locations
#   comp analysis
#   weapons
#   economy
#   sort by map

# use pandas df to store info
# c

import json
import requests
from os import listdir

DIR = "matches"

match_file_names = listdir(DIR)

for match_file_name in match_file_names:
    with open match_file_name as match_json:
        match =json.loads(match_json)
