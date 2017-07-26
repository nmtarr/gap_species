
# coding: utf-8

# In[4]:

import requests
import pysb
import json
from IPython.display import display
from bis2 import gc2
from bis import tir
from bis import gap


# In[ ]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# In[3]:

# Set up the actions/targets for this particular instance
thisRun = {}
thisRun["instance"] = "DataDistillery"
thisRun["db"] = "BCB"
thisRun["baseURL"] = gc2.sqlAPI(thisRun["instance"],thisRun["db"])

_habitatMapCollectionID = "527d0a83e4b0850ea0518326"
_gapSpecies = sb.get_child_ids(_habitatMapCollectionID)

for item in _gapSpecies:
    print (item)
    checkTIR = requests.get(thisRun["baseURL"]+"&q=SELECT id FROM tir.tir WHERE registration->>'id' = '"+item+"'").json()
    if len(checkTIR["features"]) == 0:
        gapSpecies = gap.gapToTIR(sb.get_item(item, {'fields':'identifiers,tags'}))
        display (gapSpecies)
        print (tir.tirRegistration(gc2.sqlAPI("DataDistillery","BCB"),json.dumps(gapSpecies)))


# In[ ]:



