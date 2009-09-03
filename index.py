""" mod_python.publisher service that proxies searches 
(c) Staffan Olsson repossearch.com
$LastChangedRevision$
"""

import sys
import os
from mod_python import apache
import httplib
import urllib

def index(req, repossearch=None, target=None, rev=None, base=None):
    
    if not repossearch:
        return "Query ('repossearch' parameter) is required"
    # target and rev is currently not used but repos gui is encouraged to send it 

    settings = getSettings()
    
    # http.client in python 3.x
    url = settings["solrapp"] + settings["schema"] + "select/"
    params = {"version": "2.2", "wt":"json", "q": repossearch, "start": 0, "rows": 10, "indent": "on"}
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
            "solrport": 8983,
            "solrapp": "/solr/",
            "schema": ""}

