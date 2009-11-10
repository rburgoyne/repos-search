"""Search proxy

   Copyright 2009 Staffan Olsson repossearch.com

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

This is a service for mod_python.publisher service that proxies searches to Solr
$LastChangedRevision$
"""

import sys
import os
from mod_python import apache
import httplib
import urllib

def index(req, q=None, target=None, rev=None, base=None):
    
    if not q:
        return "Query ('repossearch' parameter) is required"
    # target and rev is currently not used but repos gui is encouraged to send it 

    settings = getSettings()
    
    # http.client in python 3.x
    url = settings["solrapp"] + settings["schema"] + "select/"
    params = {"version": "2.2", "wt":"json", "q": q, "start": 0, "rows": 10, "indent": "on"}
    # filter on repository for SVNParentPath setups
    if base:
        params["fq"] = "id:%s/*" % base
    headers = {"Accept": "text/plain"}
    c = httplib.HTTPConnection(settings["solrhost"], settings["solrport"])
    try:
        c.request('GET', url + "?" + urllib.urlencode(params), headers=headers)
    except:
        raise apache.SERVER_RETURN, apache.HTTP_SERVICE_UNAVAILABLE
    r1 = c.getresponse()
    data = r1.read()
    c.close()
    if r1.status is not 200:
        raise NameError("Query failed with status %d and response %s" % (r1.status, data))
    
    return data

def getSettings():
    
    return {"solrhost": "localhost",
            # servlet container port
            "solrport": 8080,
            # solr webapp + core path
            "solrapp": "/solr/",
            "schema": "svnhead/"}

