
# coding: utf-8

# This is one-time code that fixes an issue in the DOIs that were minted and recorded in the GAP species model items in ScienceBase. These are the foundational metadata containers that provide information about the GAP models and their access points. The original script that generated the items from a spreadsheet inventory used a method that posted the information to a web app to mint the DOI. That app returned some whitespace characters trailing the DOI that got inserted into ScienceBase. This code strips the newline and whitespace to clean up the string and puts the identifiers list back to the ScienceBase items.

# In[1]:

import pysb,time
from IPython.display import display


# In[2]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# In[30]:

#habitatMapCollectionID = "527d0a83e4b0850ea0518326"
#collectionIDs = sb.get_child_ids(habitatMapCollectionID)

items = sb.find_items('filter=dateRange!%3D%7B"choice"%3A"day"%7D&parentId=527d0a83e4b0850ea0518326&max=100')

#for item in collectionIDs:
for item in items["items"]:
    item = item["id"]

    thisItem = sb.get_item(item)
    thisItemUpdate = {}
    thisItemUpdate["id"] = item

    thisItemNewIdentifiers = []
    for identifier in thisItem["identifiers"]:
        if identifier["type"] == "DOI":
            thisID = {}
            thisID["type"] = identifier["type"]
            thisID["scheme"] = identifier["scheme"]
            thisID["key"] = identifier["key"].strip()
        else:
            thisID = identifier
        thisItemNewIdentifiers.append(thisID.copy())
        thisItemUpdate["identifiers"] = thisItemNewIdentifiers

    sb.update_item(thisItemUpdate)
    display (thisItemUpdate)
    time.sleep(0.5)


# In[ ]:



