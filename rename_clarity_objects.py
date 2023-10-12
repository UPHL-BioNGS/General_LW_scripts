#!/usr/bin/env python3

"""
Author: John Arnn
Release Date: 10/12/2023

Usage:
This script is to be used to rename artifacts and containers in Clarity. You need to provide your Clarity 
username and password, the lims id of the sample you want to change, weather its a artifact or container,
and the new_name.
"""


import argparse
import xml.etree.ElementTree as ET
from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
import re


parser = argparse.ArgumentParser(description="A script that updates Clarity Derived Samples and Container names")
    
# Required arguments
parser.add_argument("--user", help="User name")
parser.add_argument("--password", help="User's password")
parser.add_argument("--new_name", help="What you want to rename the sample too")

# Either list or file must be provided
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--artifact", help="limsid of derived sample or artifact")
group.add_argument("--container", help="limsid of container")

args = parser.parse_args()

headers = {'Content-Type': 'application/xml'}

if args.container:
    info=requests.get(
      "https://uphl-ngs.claritylims.com/api/v2/containers/%s" % args.container,
      auth=HTTPBasicAuth(args.user, args.password)
    ).content

    doc = etree.fromstring(info)
    for e in doc.iterfind("name"):
        e.text = args.new_name
    xml=etree.tostring(doc).decode("utf-8")
    print("Verify that one of the names is the intended name of the plate you want to change:")
    print(set(info.decode("utf-8").split()).symmetric_difference(set(xml.split()))-{'<?xml', 'version="1.0"', 'standalone="yes"?>', 'encoding="UTF-8"'})

    proceed = input("Continue: y/n? ")

    if proceed == 'y':
        requests.put(
        "https://uphl-ngs.claritylims.com/api/v2/containers/%s" % args.container, data=xml, headers=headers,
        auth=HTTPBasicAuth(args.user, args.password)
        ).content

if args.artifact:
    info=requests.get(
      "https://uphl-ngs.claritylims.com/api/v2/artifacts/%s" % args.artifact,
      auth=HTTPBasicAuth(args.user, args.password)
    ).content

    doc = etree.fromstring(info)
    for e in doc.iterfind("name"):
        e.text = args.new_name
    xml=etree.tostring(doc).decode("utf-8")
    print("Verify that one of the names is the intended name of the plate you want to change:")
    print(set(info.decode("utf-8").split()).symmetric_difference(set(xml.split()))-{'<?xml', 'version="1.0"', 'standalone="yes"?>', 'encoding="UTF-8"'})

    proceed = input("Continue: y/n? ")

    if proceed == 'y':
        requests.put(
        "https://uphl-ngs.claritylims.com/api/v2/artifacts/%s" % args.artifact, data=xml, headers=headers,
        auth=HTTPBasicAuth(args.user, args.password)
        ).content

