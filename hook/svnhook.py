#!/usr/bin/env python
"""Fulltext indexing of committed files.
   
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
   
Requires Solr 1.4-dev example set up as described in:
http://wiki.apache.org/solr/ExtractingRequestHandler
$LastChangedRevision$
"""

'''
The hook is designed to index anything from the repository
history that might be relevant to search for.

Indexing performance is assumed to be of minor importance.
Index size can be reduced by modifying the hook logic, but a
better options is to customize the schema for example by
settings fields to type "ignore".

Comments about the "svnrev" schema are design notes, but
indexing of revision properties and diff is not implemented yet.

The hook consists of three components, kept together in a
single script for ease of inclusion from post-commit hook:
* Repository access
* Handlers for changes
* Solr communication
* Startup from command line

Use rebuild_index.py to reindex a repository from revision 0 to HEAD.
'''

import sys
import logging
import logging.handlers
import os
from optparse import OptionParser
from subprocess import Popen
from subprocess import PIPE
from subprocess import check_call
import re
from tempfile import NamedTemporaryFile
from urllib import urlencode
import xml.dom.minidom
import httplib
from urlparse import urlparse
from xml.sax.saxutils import escape

""" hook options """
parser = OptionParser()
parser.add_option("-o", "--operation", dest="operation", default="index",
  help="Type of operation: 'index', 'batch', 'drop', 'commit'. Default: %default")
parser.add_option("-p", "--repository", dest="repo",
  help="A local repository path")
parser.add_option("-r", "--revision", dest="rev",
  help="Committed revision")
parser.add_option("", "--nobase", dest="nobase", action='store_true', default=False,
  help="Disable prefixed with repo name (i.e. @base) when indexing. Defaults to %default")
parser.add_option("", "--prefix", dest="prefix", default="",
  help="Prefix in index, for example parent path or url. Will be prepended to base. Empty by default." +
    " It is recommended to end the prefix with a slash so it can be separated from base in UI")

parser.add_option("", "--loglevel", dest="loglevel", default="info",
  help="The loglevel (standard Log4J levels, lowercase). Defaults to %default.")
parser.add_option("", "--svnlook", dest="svnlook", default="/usr/bin/svnlook",
  help="The svnlook command, default: %default")
parser.add_option("", "--curl", dest="curl", default="/usr/bin/curl",
  help="The curl command, default: %default")
parser.add_option("", "--solr", dest="solr", default="http://localhost:8080/solr/",
  help="Solr host, port and root path. With trailing slash. Default: %default")
parser.add_option("", "--schemahead", dest="schemahead", default="svnhead",
  help="The fulltext schema name in solr root or multicore root. Default: %default")

def getOptions():
  (options, args) = parser.parse_args()
  if options.repo is None:
    print(__doc__)
    parser.print_help()
    sys.exit(2)
  return options

def optionsPreprocess(options):
  '''
  Derives additional options needed in functions below.
  Raises exception on invalid or missing options.
  '''
  # normalize repository path
  options.repo = options.repo.rstrip("/")
  # derive base from repo path
  if options.nobase:
    options.base = ''
  else:
    options.base = os.path.basename(options.repo)
  # only numeric revisions supported
  if options.rev:
    options.rev = long(options.rev)

### ----- hook backend to read from repository ----- ###


def repositoryHistoryReader(options, revisionHandler, pathEntryHandler):
  '''
  Iterates through repository revision and calls the given handlers
  for parse events: new revision and changed path in revision.
  
  This script is called for a single revision so there will only be one
  call to revisionHandler.
  '''
  options.logger.info("Repository '%s' base '%s' rev %d" % (options.repo, options.base, options.rev))
  changedp = Popen([options.svnlook, "changed", "-r %d" % options.rev, options.repo], stdout=PIPE)
  changed = changedp.communicate()[0]
  # assuming utf8 system locale
  changed = changed.decode('utf8')
  # event, revprop support not implemented
  revisionHandler(options, options.rev, dict())
  # parse change list into path events
  changematch = re.compile(r"^([ADU_])([U\s])\s+(.+)$")
  for change in changed.splitlines():
    m = changematch.match(change);
    p = "/" + m.group(3)
    pathEntryHandler(options, options.rev, p, m.group(1), m.group(2), not p.endswith('/'))

def repositoryDiff(options, revision, path):
  '''
  Returns diff for revision-1:revision as plaintext for the given path
  '''
  pass

def repositoryGetFile(options, revision, path):
  '''
  Returns contents as NamedTemporaryFile that will be deleted on close()
  '''
  cat = NamedTemporaryFile('wb')
  options.logger.debug("Writing %s to temp %s" % (path, cat.name))    
  catp = Popen([options.svnlook, "cat", "-r %d" % options.rev, options.repo, path], stdout=cat)
  catp.communicate()
  if not catp.returncode is 0:
    options.logger.debug("Cat failed for %s. It must be a folder." % (path))
    return
  cat.flush()
  return cat

def repositoryGetProplist(options, revision, path):
  '''
  Returns proplist as dictionary with propname:value pairs
  '''
  xml = Popen([options.svnlook, "proplist", "-v", "--xml", "-r %d" % revision, options.repo, path], stdout=PIPE).communicate()[0]
  return proplistToDict(xml)

def proplistToDict(xmlsource):
  dom = xml.dom.minidom.parseString(xmlsource)
  p = dict()
  for n in dom.getElementsByTagName('property'):
    p[n.getAttribute('name')] = n.firstChild and n.firstChild.nodeValue or ''
  return p

### ----- event handlers for results from backend ----- ###

def handleRevision(options, revision, revprops):
  '''
  Event handler for new historical revision in repository,
  called in ascending revision number order.
  
  Revision properties should be indexed in svnrev schema at id
  [prefix][base]/[revision number]
  '''
  pass

def handlePathEntry(options, revision, path, action, propaction, isfile):
  '''
  Event handler for changed path in revision.
  Path is unicode with leading slash, trailing slash for folders.
  Action is one of the subversion characters [ADU] or whitespace.
  
  Contents and current property values should be indexed in svnhead
  schema at [prefix][base][path]
  
  Diff for the path at this revision should be indexed in svnrev
  '''
  if not isfile:
    options.logger.debug('Ignoring folder %s' % path)
    return
  options.logger.debug("%s%s  %s" % (action, propaction, path))
  if action == 'D':
    handleFileDelete(options, options.rev, path)
  elif action == 'A':
    handleFileAdd(options, options.rev, path)
  elif action == 'U':
    handleFileChange(options, options.rev, path)
  elif propaction == 'U':
    handleFileChange(options, options.rev, path)
    
def handleFileDelete(options, revision, path):
  '''
  Handles indexing of file deletion.
  '''
  indexDelete_httpclient(options, revision, path)

def handleFileAdd(options, revision, path):
  indexSubmitFile_curl(options, revision, path)

def handleFileChange(optins, revision, path):
  indexSubmitFile_curl(options, revision, path)

### ----- cummunication with indexing server ----- ###

def indexGetId(options, revision, path):
  '''
  Builds the string used as id in index.
  Concatenates prefix, base, root marker and path.
  '''
  id = '^' + path
  if options.base:
    id = options.base + id
  if options.prefix:
    id = options.prefix + id  
    
  return id

def indexGetName(path):
  '''
  Gets the file or folder name of an entry
  
  >>> indexGetName('/my/sample file.txt')
  'sample file.txt'
  '''
  return path.rpartition('/')[2]

def indexEscapePropname(svnProperty):
  '''
  Escapes subversion property name to valid solr field name
  
  Colon is replaced with underscore.
  Dash is also replaced with underscore because Solr does
  the same implicitly when creating dynamic field.
  
  >>> indexEscapePropname('svn:mime-type')
  'svn_mime_type'
  
  This results in a slight risk of conflict, for example if
  properties wouls be svn:mime-type and svn_mime:type.
  '''
  return re.sub(r'[.:-]', '_', svnProperty)

def indexDelete_httpclient(options, revision, path):
  schema = options.solr + options.schemahead + '/'
  id = indexGetId(options, revision, path)
  doc = '<?xml version="1.0" encoding="UTF-8"?><delete><id>%s</id></delete>' % escape(id.encode('utf8'))
  options.logger.debug(doc)
  u = urlparse(schema)
  h = httplib.HTTPConnection(u.netloc)
  h.putrequest('POST', u.path + 'update')
  h.putheader('content-type', 'text/xml; charset=UTF-8')
  h.putheader('content-length', str(len(doc)))
  h.endheaders()
  h.send(doc)
  response = h.getresponse()
  responseBody = response.read()
  h.close()
  if response.status == 200:
    options.logger.info("Deleted from index %s" % id)
  else:
    options.logger.error("%d %s" % (response.status, responseBody))

def indexSubmitFile_curl(optons, revision, path):
  ''' Python's httplib is not capable of POSTing files
  (multipart upload) so we use command line curl instead '''
  schema = options.solr + options.schemahead + '/'
  id = indexGetId(options, revision, path)
  params = {"literal.id": id.encode('utf8'), 
            "literal.svnrevision": revision,
            "commit": "false"}

  props = repositoryGetProplist(options, revision, path)
  for p in props.keys():
    params['literal.svnprop_' + indexEscapePropname(p)] = props[p].encode('utf8')

  name = indexGetName(path)
  params['literal.name'] = name.encode('utf8')

  contents = repositoryGetFile(options, revision, path)
  curlp = check_call(getCurlCommand(options) + [
         '%supdate/extract?%s' % (schema, urlencode(params)),
         '-F', 'myfile=@%s' % contents.name])
  contents.close()
  options.logger.info("Successfully indexed id: %s" % params["literal.id"]);
  
def getCurlCommand(options):
  curl = [options.curl, '-s', '-S']
  # ignore output of response xml (we could also capture it using Popen to get QTime)
  curl = curl + ['-o', '/dev/null']
  # fail if status is not 200
  curl = curl + ['-f']
  if options.logger.getEffectiveLevel() is logging.DEBUG:
    curl = curl + ['-v']
  return curl

def indexPost(url, doc):
  '''
  http client implementation of post to index
  '''
  h = httplib.HTTPConnection(url.netloc)
  h.putrequest('POST', url.path +'update')
  h.putheader('content-type', 'text/xml; charset=UTF-8')
  h.putheader('content-length', len(doc))
  h.endheaders()
  h.send(doc)
  r = h.getresponse()
  r.read()
  h.close()
  return r

def indexCommit(options):
  '''
  Issues commit command to Solr to make recent indexing searchable.
  '''
  schema = options.solr + options.schemahead + '/'
  url = urlparse(schema)
  r = indexPost(url, '<commit/>')
  options.logger.info("Commited with status %d" % r.status)
  
def indexDrop(options):
  url = urlparse(options.solr + options.schemahead + '/')
  prefix = indexGetId(options, None, '')
  query = 'id:%s' % prefix.replace(':', '\\:').replace('^', '\\^') + '*'
  deleteDoc = '<?xml version="1.0" encoding="UTF-8"?><delete><query>%s</query></delete>' % query
  r = indexPost(url, deleteDoc)
  if r.status is 200:
    options.logger.info("Deleted all %s" % query)
  else:
    options.logger.error("Delete status %d for query %s" % (r.status, query))

### ----- hook start from post-commit arguments ----- ###

def getLogger(options):    
  """ 
  Set up logger based on options 
  and store the instance in options.logger
  """
  LEVELS = {'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL}
  level = LEVELS.get(options.loglevel)
  if not level:
      raise NameError("Invalid log level %s" % options.loglevel)
  logger = logging.getLogger("Repos Search hook")
  logger.setLevel(level)
  # console
  ch = logging.StreamHandler()
  ch.setLevel(level)
  ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
  logger.addHandler(ch)
  options.logger = logger
    
if __name__ == '__main__':
  options = getOptions()
  getLogger(options)
  optionsPreprocess(options)
  if options.operation == 'index' or options.operation == 'batch':
    repositoryHistoryReader(options, handleRevision, handlePathEntry)
  if options.operation == 'drop':
    indexDrop(options)    
  if options.operation == 'index' or options.operation == 'drop' or options.operation == 'commit':
    indexCommit(options)
