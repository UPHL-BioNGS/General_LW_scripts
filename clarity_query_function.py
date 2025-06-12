# Requiried Libraries for Function
import requests
from requests.auth import HTTPBasicAuth
import re

# Function assumes the list_of_samples is using Clarity Submitted Sample names. This will match the Sample_ID column in most samplesheets created by Clarity.
# Another assumption is list_of_ids are UDFs that are defined in Clarity. 
# The username and password should use the Clarity User "queryuser" and its associated password or you can use your own username and password
# Function will return a dictionary where each element in the list_of_samples is a key. And the vaule for the key is another dictionay where the keys are from
# list_of_ids. If the sample can't be found in clarity the sample will have no values in the dictionary. If there are duplicate sample with differet IDs both will
# be returned. If the sample's associated UDF is empty the vaule for that dictionary key will be empty.

def query_clarity_for_ids(list_of_samples, list_of_ids, q_user, q_password):
    list_of_sample_dictionaries = []
    for sample in list_of_samples:
        xml=(requests.get("https://uphl-ngs.claritylims.com/api/v2/samples?name=%s" % sample, auth=HTTPBasicAuth(q_user, q_password)).content).decode("utf-8")
        if re.findall(r'limsid="([^"]+)"', xml):
            combine_xml = ""
            for duplicate in re.findall(r'limsid="([^"]+)"', xml):
                combine_xml = combine_xml + (requests.get("https://uphl-ngs.claritylims.com/api/v2/samples/%s" % re.findall(r'limsid="([^"]+)"', xml)[0], auth=HTTPBasicAuth(q_user, q_password)).content).decode("utf-8")
            sample_dict = {}
            for id_ in list_of_ids:
                if re.findall(r'<udf:field name="%s" type="String">(.*?)</udf:field>' % id_ , combine_xml):
                    sample_dict[id_] = set(re.findall(r'<udf:field name="%s" type="String">(.*?)</udf:field>' % id_ , combine_xml))
            list_of_sample_dictionaries.append(sample_dict)
        else:
            list_of_sample_dictionaries.append([])
    return dict(zip(list_of_samples, list_of_sample_dictionaries))
