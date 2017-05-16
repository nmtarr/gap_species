
# coding: utf-8

# In[20]:

import requests,configparser,pysb,time,datetime
from IPython.display import display
import pandas as pd


# In[21]:

# Get API keys and any other config details from a file that is external to the code.
config = configparser.RawConfigParser()
config.read_file(open(r'../config/stuff.py'))


# In[22]:

# Build base URL with API key using input from the external config.
def getBaseURL():
    gc2APIKey = config.get('apiKeys','apiKey_GC2_BCB').replace('"','')
    apiBaseURL = "https://gc2.mapcentia.com/api/v1/sql/bcb?key="+gc2APIKey
    return apiBaseURL


# In[26]:

# Basic function to insert registration info pairs into TIR
def registerToTIR(recordInfoPairs):
    # Build query string
    insertSQL = "INSERT INTO tir.tir2 (registration) VALUES ('"+recordInfoPairs+"')"
    # Execute query
    response = requests.get(getBaseURL()+"&q="+insertSQL).json()
    return response


# In[24]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# In[27]:

habitatMapCollectionID = "527d0a83e4b0850ea0518326"

collectionIDs = sb.get_child_ids(habitatMapCollectionID)

for item in collectionIDs:
    thisItem = sb.get_item(item)
    recordInfoPairs = '"registrationDate"=>"'+datetime.datetime.utcnow().isoformat()+'"'
    recordInfoPairs = recordInfoPairs+',"ScienceBaseItemID"=>"'+item+'"'
    for identifier in thisItem["identifiers"]:
        recordInfoPairs = recordInfoPairs+',"'+identifier["type"]+'"=>"'+identifier["key"].strip()+'"'
    for tag in thisItem["tags"]:
        if tag["scheme"] == "https://www.sciencebase.gov/vocab/bis/tir/scientificname":
            recordInfoPairs = recordInfoPairs+',"GAP_ScientificName"=>"'+tag["name"]+'"'
        elif tag["scheme"] == "https://www.sciencebase.gov/vocab/bis/tir/commonname":
            recordInfoPairs = recordInfoPairs+',"GAP_CommonName"=>"'+tag["name"]+'"'
        else:
            pass
    print (registerToTIR(recordInfoPairs))


# In[ ]:



