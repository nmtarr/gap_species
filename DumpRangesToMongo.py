
# coding: utf-8

# In[1]:

from pymongo import MongoClient
import pandas as pd
from IPython.display import display


# In[2]:

mdbClient = MongoClient()


# In[3]:

bis = mdbClient["bis"]


# In[4]:

gapRangeDataCache = bis["gapRangeData"]


# In[ ]:

RangeCodesDict = {"Presence": {1: "Known/extant", 2: "Possibly present", 3: "Potential for presence", 
                               4: "Extirpated/historical presence", 
                               5: "Extirpated purposely (applies to introduced species only)",
                                6: "Occurs on indicated island chain", 7: "Unknown",  0: "Unknown"},
                "Origin": {1: "Native", 2: "Introduced", 3: "Either introducted or native", 
                           4: "Reintroduced", 5: "Either introduced or reintroduced",
                           6: "Vagrant", 7: "Unknown",  0: "Unknown"},
                "Reproduction": {1: "Breeding", 2: "Nonbreeding", 
                                 3: "Both breeding and nonbreeding", 4: "Unknown", 7: "Unknown",  0: "Unknown"},
                 "Season": {1: "Year-round", 2: "Migratory", 3: "Winter", 4: "Summer", 
                            5: "Passage migrant or wanderer", 6: "Seasonal permanence uncertain", 
                            7: "Unknown", 8: "Vagrant",  0: "Unknown"}}


# In[ ]:

for fileName in ["National_GAP_Amphibians_Range_Table.txt","National_GAP_Reptiles_Range_Table.txt","National_GAP_Mammals_Range_Table.txt","National_GAP_Birds_Range_Table.txt"]:
    rangeData = pd.read_csv(fileName)
    for index, row in rangeData.iterrows():
        thisRecord = row.to_dict()
        thisRecord["Origin"] = RangeCodesDict["Origin"][thisRecord["intGapOrigin"]]
        thisRecord["Presence"] = RangeCodesDict["Presence"][thisRecord["intGapPres"]]
        thisRecord["Reproduction"] = RangeCodesDict["Reproduction"][thisRecord["intGapRepro"]]
        thisRecord["Season"] = RangeCodesDict["Season"][thisRecord["intGapSeas"]]
        print (gapRangeDataCache.insert_one(thisRecord).inserted_id)


# In[ ]:



