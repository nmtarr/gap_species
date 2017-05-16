
# coding: utf-8

# This notebook updates all of the GAP species habitat map items in ScienceBase to call out, explicitly, the scientific name and common name used by GAP for these items. The problem in the previous code that generated these items was that there was no way in code to determine which name was which. In this process, I eliminated the "United States" place name tag for now. We will be running another process once these items are registered to feed back SGCN states as a specific type of "place" identifier for faceted searching.

# In[49]:

import requests,configparser,pysb,os,time
from IPython.display import display
import pandas as pd


# In[27]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# In[9]:

# Get API keys and any other config details from a file that is external to the code.
config = configparser.RawConfigParser()
config.read_file(open(r'../config/stuff.py'))


# In[10]:

# Build base URL with API key using input from the external config.
def getBaseURL():
    gc2APIKey = config.get('apiKeys','apiKey_GC2_BCB').replace('"','')
    apiBaseURL = "https://gc2.mapcentia.com/api/v1/sql/bcb?key="+gc2APIKey
    return apiBaseURL


# In[45]:

gapInventory = pd.read_table("ScienceBaseCSV_20170417NT.csv", sep=",")


# In[42]:

habitatMapCollectionID = "527d0a83e4b0850ea0518326"

collectionIDs = sb.get_child_ids(habitatMapCollectionID)

for item in collectionIDs:
    thisItem = sb.get_item(item)
    thisItemTags = {}
    thisItemTags["id"] = item
    for identifier in thisItem["identifiers"]:
        if identifier["type"] == "GAP_SpeciesCode":
            gapCode = identifier["key"]
            scientificName = {}
            scientificName["type"] = "Theme"
            scientificName["scheme"] = "https://www.sciencebase.gov/vocab/bis/tir/scientificname"
            scientificName["name"] = gapInventory.loc[gapInventory['GAP_code'] == gapCode, 'scientific_name'].iloc[0]

            commonName = {}
            commonName["type"] = "Theme"
            commonName["scheme"] = "https://www.sciencebase.gov/vocab/bis/tir/commonname"
            commonName["name"] = gapInventory.loc[gapInventory['GAP_code'] == gapCode, 'common_name'].iloc[0]

            thisItemTags["tags"] = [scientificName,commonName]
            
            break
    
    display (sb.update_item(thisItemTags))
    time.sleep(1)


# In[ ]:



