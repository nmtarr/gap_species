
# coding: utf-8

# In[9]:

import pysb,time
from IPython.display import display


# In[3]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# In[10]:

habitatMapCollectionID = "527d0a83e4b0850ea0518326"

collectionIDs = sb.get_child_ids(habitatMapCollectionID)

for item in collectionIDs:
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



