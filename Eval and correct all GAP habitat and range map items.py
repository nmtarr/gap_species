
# coding: utf-8

# This notebook rebuilds all GAP Habitat Map and Range Map items in their respective ScienceBase collections from source material contained in files attached to both items, retaining only the DOI assignment from the original items. It can be used to make adjustments to the item metadata, which is considered the master online source within the Biogeographic Information System for the GAP species records. From this point, the informaiton is pulled out via the ScienceBase API and cached in other data stores for use.

# In[ ]:

import requests
import pysb
import time
from IPython.display import display
import pandas as pd
import ast
import json
import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO


# In[ ]:

rootItems = {}
rootItems["Habitat Maps"] = "527d0a83e4b0850ea0518326"
rootItems["Range Maps"] = "5951527de4b062508e3b1e79"


# This code block retrieves two sets of vocabularies from the ScienceBase Vocab and builds them into a simple dictionary data structure for use. This is used to key off of identifier types and the code lists that indicate how ITIS and NatureServe identifiers relate to GAP species codes so that the final identifiers in the ScienceBase Items all point explicitly to a definition of the relationship via their scheme attribute.

# In[ ]:

sbItemIdentifiers = requests.get("https://www.sciencebase.gov/vocab/identifier/terms?nodeType=term&parentId=528e99f7e4b05d51c7038afd&max=100&format=json").json()
bisIdentifiers = requests.get("https://www.sciencebase.gov/vocab/categories?parentId=59e62074e4b0adbd11e26b12&max=100&format=json").json()

identifiers = {}
identifiers["ITIS"] = {}
identifiers["NatureServe"] = {}
for i in sbItemIdentifiers["list"]:
    identifiers[i["name"]] = i["scheme"]+"/"+i["name"]
for i in bisIdentifiers["list"]:
    identifiers[i["name"]] = i["scheme"]+"/"+i["name"]
    if i["name"].find("itis_tsn_") == 0:
        identifiers["ITIS"][i["label"]] = {"scheme":i["scheme"]+"/"+i["name"],"name":i["name"]}
    elif i["name"].find("nsid_") == 0:
        identifiers["NatureServe"][i["label"]] = {"scheme":i["scheme"]+"/"+i["name"],"name":i["name"]}


# In[ ]:

sb = pysb.SbSession()
username = input("Username: ")
sb.loginc(str(username))


# The root collection items (see above) both have source files attached to them identified by specific titles indicating their purpose. These came from a couple of backend databases and spreadsheets used by the GAP team in managing species information and connecting it to other data for use. These files are essentially the "online debut" of the information and a point of reference from which we build out the species items with code. The attributes we use from these sources are built into a local data structure for each species called "speciesRecord" that is then used to build out each species item. Some of the information is common between Habitat Maps and Range Maps while other attributes are specific to one or the other. If we ever need to change information for these records, we can either rerun this code with fresh files or edit the information directly on the ScienceBase Items through some other means and then refresh backend systems from there.
# 
# The following code block reads the data from the attached CSVs into Pandas dataframes for processing. The files are called into those dataframes based on their very explicit titles from the collection item attachments.

# In[ ]:

habitatMapRootItem = sb.get_item(rootItems["Habitat Maps"])
rangeMapRootItem = sb.get_item(rootItems["Range Maps"])

habitatMapSourceMetadata = pd.read_csv(StringIO(sb.get([f for f in habitatMapRootItem["files"] if f["title"] == "Metadata Source: Habitat Maps"][0]["url"])))
rangeMapSourceMetadata = pd.read_csv(StringIO(sb.get([f for f in rangeMapRootItem["files"] if f["title"] == "Metadata Source: Range Maps"][0]["url"])))
itis_ns_codes = pd.read_csv(StringIO(sb.get([f for f in habitatMapRootItem["files"] if f["title"] == "Code Mapping: ITIS and NatureServe"][0]["url"])))
iucn_codes = pd.read_csv(StringIO(sb.get([f for f in habitatMapRootItem["files"] if f["title"] == "Code Mapping: IUCN"][0]["url"])))


# These are a couple of specific functions that made sense to pull out here. I don't know if they would be useful in other circumstances. If so, we can pull them out into the bis package.

# In[ ]:

def getScienceBaseItem(whichRoot,GAP_SpeciesCode):
    searchResults = sb.find_items("parentId="+rootItems[whichRoot]+"&fields=identifiers&q="+GAP_SpeciesCode)
    if len(searchResults["items"]) > 1:
        return None
    else:
        return searchResults["items"][0]

def doiIdentifier(doiString):
    identifier = {"type":"doi","scheme":"https://www.sciencebase.gov/vocab/identifier/term/doi"}

    if doiString.find("://") > 0:
        doiString = "doi:"+doiString.split("/")[-2]+"/"+doiString.split("/")[-1]

    identifier["key"] = doiString
    return identifier


# This is the main information processing section of the script. It uses the primary file of base species metadata from the Habitat Map collection item as the driving loop, iterating over each row to build the speciesRecord dictionary from attributes in that file and the other reference files and then make choices about how to build out the Habitat Map and Range Map items. It then updates those items via the ScienceBase API, essentially replacing all the major core attributes on those items with freshened information. This could be made more elegant by doing date comparisons between source files and items to determine what exactly needed to be updated, but it is a small enough number of items that it shouldn't realy matter.
# 
# Note that other code will be running eventually to put new attributes on the ScienceBase Items from the Taxa Information Registry (e.g., ITIS taxonomy, IUCN threats, FWS listing status, etc.). These "value-added" facets on the items will help drive search and analysis processes and will be driven partly by how this base information is put onto the items (e.g., specific link types for ITIS identifiers determines what information we pull back from that system and how we deal with it).

# In[ ]:

count = 0
for index, habitatMapMetadata in habitatMapSourceMetadata.iterrows():
    try:
        # Set up a local species record structure containing common attributes; instantiate as available
        speciesRecord = {}
        speciesRecord["GAP_SpeciesCode"] = habitatMapMetadata["GAP_code"]
        speciesRecord["CommonName"] = habitatMapMetadata["common_name"]
        speciesRecord["ScientificName"] = habitatMapMetadata["scientific_name"]
        speciesRecord["startDate"] = int(habitatMapMetadata["start_date"])
        speciesRecord["endDate"] = int(habitatMapMetadata["end_date"])
        speciesRecord["publicationDate"] = int(habitatMapMetadata["publication_date"])
        speciesRecord["habitatMapEditor"] = habitatMapMetadata["editor"]
        speciesRecord["habitatMapReviewer"] = habitatMapMetadata["reviewer"]

        # Get the Range Map metadata for this species code from the source file attached to the range map collection
        rangeMapMetadata = rangeMapSourceMetadata.loc[rangeMapSourceMetadata["GAP_code"] == speciesRecord["GAP_SpeciesCode"]]

        speciesRecord["rangeMapReviewer"] = rangeMapMetadata["reviewer"].to_string(index=False)
        speciesRecord["rangeMapEditor"] = ast.literal_eval(rangeMapMetadata["editors"].to_string(index=False))

        # Get the identifiers associated with species
        itis_ns_code = itis_ns_codes.loc[itis_ns_codes["strUC"] == speciesRecord["GAP_SpeciesCode"]]
        iucn_code = iucn_codes.loc[iucn_codes["GapSpCode"] == speciesRecord["GAP_SpeciesCode"]]

        speciesRecord["itisID"] = int(itis_ns_code["intITIScode"].to_string(index=False))
        speciesRecord["itisTypeCode"] = int(itis_ns_code["intGapITISmatch"].to_string(index=False))
        speciesRecord["natureServeID"] = int(itis_ns_code["intNSglobal"].to_string(index=False))
        speciesRecord["natureServeTypeCode"] = int(itis_ns_code["intGapNSmatch"].to_string(index=False))
        if iucn_code.empty:
            speciesRecord["iucnID"] = None
        else:
            speciesRecord["iucnID"] = int(iucn_code["IUCN Spp Number"].to_string(index=False))

        # Get the current ScienceBase record for both the Habitat Map and the Range Map
        habitatMapItem_old = getScienceBaseItem("Habitat Maps",speciesRecord["GAP_SpeciesCode"])
        rangeMapItem_old = getScienceBaseItem("Range Maps",speciesRecord["GAP_SpeciesCode"])

        # Fail this record and continue if either of the current ScienceBase records can't be found - something went wrong
        if habitatMapItem_old is None or rangeMapItem_old is None:
            display (speciesRecord)
            continue
        else:
            speciesRecord["habitatMapID"] = habitatMapItem_old["id"]
            speciesRecord["rangeMapID"] = rangeMapItem_old["id"]
            speciesRecord["d_habitatMapDOI"] = doiIdentifier(habitatMapItem_old["identifiers"][[i for i,_ in enumerate(habitatMapItem_old["identifiers"]) if _["type"] == "doi"][0]]["key"])
            speciesRecord["d_rangeMapDOI"] = doiIdentifier(rangeMapItem_old["identifiers"][[i for i,_ in enumerate(rangeMapItem_old["identifiers"]) if _["type"] == "doi"][0]]["key"])
            speciesRecord["habitatMapDOI"] = speciesRecord["d_habitatMapDOI"]["key"]
            speciesRecord["rangeMapDOI"] = speciesRecord["d_rangeMapDOI"]["key"]

        # Set up new documents for the two items; these will be used to update the ScienceBase record with assured information
        habitatMapItem_new = {"id":speciesRecord["habitatMapID"],"identifiers":[],"contacts":[],"webLinks":[],"dates":[]}
        rangeMapItem_new = {"id":speciesRecord["rangeMapID"],"identifiers":[],"contacts":[],"webLinks":[],"dates":[]}

        # Add GAP Species Code identifier
        habitatMapItem_new["identifiers"].append({"type":"GAP_SpeciesCode","key":speciesRecord["GAP_SpeciesCode"],"scheme":identifiers["GAP_SpeciesCode"]})
        rangeMapItem_new["identifiers"].append({"type":"GAP_SpeciesCode","key":speciesRecord["GAP_SpeciesCode"],"scheme":identifiers["GAP_SpeciesCode"]})

        # Add in name identifiers
        habitatMapItem_new["identifiers"].append({"type":"CommonName","key":speciesRecord["CommonName"],"scheme":identifiers["CommonName"]})
        rangeMapItem_new["identifiers"].append({"type":"CommonName","key":speciesRecord["CommonName"],"scheme":identifiers["CommonName"]})
        habitatMapItem_new["identifiers"].append({"type":"ScientificName","key":speciesRecord["ScientificName"],"scheme":identifiers["ScientificName"]})
        rangeMapItem_new["identifiers"].append({"type":"ScientificName","key":speciesRecord["ScientificName"],"scheme":identifiers["ScientificName"]})

        # Add in DOIs
        habitatMapItem_new["identifiers"].append(speciesRecord["d_habitatMapDOI"])
        rangeMapItem_new["identifiers"].append(speciesRecord["d_rangeMapDOI"])

        # Add in ITIS identifiers
        habitatMapItem_new["identifiers"].append({"key":speciesRecord["itisID"],"type":identifiers["ITIS"][str(speciesRecord["itisTypeCode"])]["name"],"scheme":identifiers["ITIS"][str(speciesRecord["itisTypeCode"])]["scheme"]})
        rangeMapItem_new["identifiers"].append({"key":speciesRecord["itisID"],"type":identifiers["ITIS"][str(speciesRecord["itisTypeCode"])]["name"],"scheme":identifiers["ITIS"][str(speciesRecord["itisTypeCode"])]["scheme"]})

        # Add in NatureServe identifiers
        habitatMapItem_new["identifiers"].append({"key":speciesRecord["natureServeID"],"type":identifiers["NatureServe"][str(speciesRecord["natureServeTypeCode"])]["name"],"scheme":identifiers["NatureServe"][str(speciesRecord["natureServeTypeCode"])]["scheme"]})
        rangeMapItem_new["identifiers"].append({"key":speciesRecord["natureServeID"],"type":identifiers["NatureServe"][str(speciesRecord["natureServeTypeCode"])]["name"],"scheme":identifiers["NatureServe"][str(speciesRecord["natureServeTypeCode"])]["scheme"]})

        # Add in IUCN identifier when it is available
        if speciesRecord["iucnID"] is not None:
            habitatMapItem_new["identifiers"].append({"key":speciesRecord["iucnID"],"type":"iucn_id_verified","scheme":identifiers["iucn_id_verified"]})
            rangeMapItem_new["identifiers"].append({"key":speciesRecord["iucnID"],"type":"iucn_id_verified","scheme":identifiers["iucn_id_verified"]})

        # Set title for both items
        _titlePrefix = speciesRecord["CommonName"]+" ("+speciesRecord["ScientificName"]+") "
        habitatMapItem_new["title"] = _titlePrefix+"Habitat Map"
        rangeMapItem_new["title"] = _titlePrefix+"Range Map"

        # Set citation string for both items
        _citationPrefix = "U.S. Geological Survey - Gap Analysis Project, 2017, "
        habitatMapItem_new["citation"] = _citationPrefix+habitatMapItem_new["title"]+", "+speciesRecord["habitatMapDOI"].replace("doi:","http://doi.org/")+"."
        rangeMapItem_new["citation"] = _citationPrefix+rangeMapItem_new["title"]+", "+speciesRecord["rangeMapDOI"].replace("doi:","http://doi.org/")+"."

        # Set Habitat Map editor and reviewer
        habitatMapItem_new["contacts"].append({"contactType":"person","type":"editor","name":speciesRecord["habitatMapEditor"]})
        habitatMapItem_new["contacts"].append({"contactType":"person","type":"reviewer","name":speciesRecord["habitatMapReviewer"]})

        # Set Range Map editors and reviewer
        rangeMapItem_new["contacts"].append({"contactType":"person","type":"reviewer","name":speciesRecord["rangeMapReviewer"]})
        for editorName in speciesRecord["rangeMapEditor"]:
            rangeMapItem_new["contacts"].append({"contactType":"person","type":"editor","name":editorName})

        # Set dates on items
        habitatMapItem_new["dates"].append({"type":"Publication","label":"Publication Date","dateString":speciesRecord["publicationDate"]})
        habitatMapItem_new["dates"].append({"type":"Start","label":"Start Date","dateString":speciesRecord["startDate"]})
        habitatMapItem_new["dates"].append({"type":"End","label":"End Date","dateString":speciesRecord["endDate"]})
        rangeMapItem_new["dates"].append({"type":"Publication","label":"Publication Date","dateString":speciesRecord["publicationDate"]})
        rangeMapItem_new["dates"].append({"type":"Start","label":"Start Date","dateString":speciesRecord["startDate"]})
        rangeMapItem_new["dates"].append({"type":"End","label":"End Date","dateString":speciesRecord["endDate"]})

        # Set up crosslinks between items
        habitatMapItem_new["webLinks"].append({"type":"webLink","typeLabel":"Web Link","uri":"https://www.sciencebase.gov/catalog/item/"+speciesRecord["rangeMapID"],"title":rangeMapItem_new["title"]})
        rangeMapItem_new["webLinks"].append({"type":"webLink","typeLabel":"Web Link","uri":"https://www.sciencebase.gov/catalog/item/"+speciesRecord["habitatMapID"],"title":habitatMapItem_new["title"]})

        # Add additional link to range map items for SHUCs DOI
        rangeMapItem_new["webLinks"].append({"type":"webLink","typeLabel":"Web Link","uri":"https://doi.org/10.5066/F7DZ0754","title":"Source data for strHUC12RNG in species range"})

        # Add in purpose statements
        habitatMapItem_new["purpose"] = "GAP distribution models represent the areas where species are predicted to occur based on habitat associations. The distribution models represent the spatial arrangement of environments suitable for occupation by a species. In other words, a species distribution is created using a deductive model to predict areas suitable for occupation within a species range. To represent these suitable environments for this species' habitat distribution model, we used the land cover and other ancillary datasets listed here in this metadata. Details on the habitat affinities and the parameters used to model are provided in the species report in the attached files section of this record.These models can be used to assess the habitat availability across the range of the species and in combination with other data to assess the conservation status or threats to the habitat for the species."
        rangeMapItem_new["purpose"] = "GAP range maps represent a coarse representation of the total areal extent of a species or the geographic limits within which a species can be found. The known range for a species can be used to constrain the boundaries of the species distribution model and in assessments of the conservation status and/or threats within the range of a species."

        # Send updates to both items
        sb.update_item(habitatMapItem_new)
        sb.update_item(rangeMapItem_new)

        # Print a count of the items processed for status checking
        count = count + 1
        print (count)
        # Display the speciesRecord data structure for inline processing reference; 
        display (speciesRecord)
        # Put in a short delay to keep ScienceBase from booting us out
        time.sleep(1)
    except Exception as e:
        print (e)
        display (habitatMapMetadata)
        display (speciesRecord)


# In[ ]:



