#!/usr/bin/python

"""
Get a search query from the user and pass it through to Solr. Then filter
results from Solr through Subversion's path-based authorization file and pass
the results back out to the search interface.
"""

import cgi
import cgitb;cgitb.enable()
from urllib import urlencode
from urllib2 import urlopen
import sys
import json
import authz_parser
import re
import os

# Set the path to `authz`
AUTHZ_FILE = '/srv/svn/authz'

def authorized(doc_id):
    """
    Pass the user, repo, and path to the authorize function of the authz_parser
    module and return the result.
    """
    user = os.environ['REMOTE_USER']
    matched = re.match("^(.*)\^(.*)$", doc_id)
    repo = matched.group(1)
    path = matched.group(2)
    return authz_parser.authorize(user, repo, path)

def filter(response):
    """
    Takes the JSON response from Solr and filters it to remove unauthorized
    results. Then returns the filtered JSON data.
    """
    response_dict = json.loads(response)
    docs = response_dict['response']['docs']
    filtered_docs = [doc for doc in docs if authorized(doc['id'])]
    response_dict['response']['docs'] = filtered_docs  
    return json.dumps(response_dict)

authz_parser.read(AUTHZ_FILE)
form = cgi.FieldStorage()
# settings for accessing solr
solrhost = 'localhost'
solrport = '8080'
solrapp = '/solr/'
schema = 'svnhead/'
# parameters for solr search
params = {}
params['wt'] = 'json'
params['start'] = form.getfirst('start', '0')
params['rows'] = form.getfirst('rows', '10')
params['indent'] = 'on'
params['qt'] = form.getfirst('qt', 'standard')
params['q'] = form.getfirst('q')

# forward to search page if there is no query
if (not params['q']): 
    print "Content-type: text/html"
    print
    print """
<html>
<head>
<title>Repos Search proxy: no query yet</title>
<meta http-equiv="refresh" content="1;url=search.html" />
</head>
<body>
<p>Redirecting to <a href="search.html">sample search form</a> becase <code>q</code> is not set.</p>
</body>
</html>
"""
    sys.exit()

# the search
fq = ''
if (form.getfirst('base')):
    params['fq'] = 'id_repo:' + form.getfirst('base')

# search URI
url = "http://" + solrhost + ":" + solrport + solrapp + schema + 'select'
url += '?' + urlencode(params)
try:
    fp = urlopen(url)
    print "Content-type: application/json"
    print
    print filter(fp.read())
    fp.close()
except:
    print 'Status: HTTP/1.1 503 Service Unavailable'
    print 'Content-type: text/plain'
    print
    print "Search engine error. Not available or query is invalid.\n"
