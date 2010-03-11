#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

Use with svn hook arguments: svnhook.py REPOSITORY REV
Or for more flexibility, use named options as specified below.
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
import traceback
from optparse import OptionParser
from subprocess import Popen
from subprocess import PIPE
from subprocess import check_call
import re
from tempfile import mkstemp
from urllib import urlencode
import xml.dom.minidom
import httplib
from urlparse import urlparse
from xml.sax.saxutils import escape

""" hook options """
parser = OptionParser()
parser.add_option("-o", "--operation", dest="operation", default="index",
  help="Type of operation: 'index', 'batch', 'drop', 'commit', 'optimize'. Default: %default")
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
  help="The loglevel (standard Log4J levels, lowercase). Defaults to 'svnlook' in PATH.")
parser.add_option("", "--svnlook", dest="svnlook", default="svnlook",
  help="The svnlook command, defaults to 'svnlook' in PATH.")
parser.add_option("", "--curl", dest="curl", default="curl",
  help="The curl command, defaults to 'curl' in PATH.")
parser.add_option("", "--solr", dest="solr", default="http://localhost:8080/solr/",
  help="Solr host, port and root path. With trailing slash. Default: %default")
parser.add_option("", "--schemahead", dest="schemahead", default="svnhead",
  help="The fulltext schema name in solr root or multicore root. Default: %default")

def getOptions():
  """ Created the option parser according to spec above.
    Also allows standard svn hook arguments """
  optargs = sys.argv[1:]
  if len(optargs) == 2 and re.search(r'^\d+$', optargs[1]):
    optargs = ['-p', optargs[0], '-r', optargs[1]]
  
  # options as global variables
  (options, args) = parser.parse_args(optargs)
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
  options.logger.info("Reading %s rev %d" % (options.base, options.rev))
  changedp = Popen([options.svnlook, "changed", "-r %d" % options.rev, options.repo], stdout=PIPE)
  changed = changedp.communicate()[0]
  # assuming utf8 system locale
  changed = changed.decode('utf8')
  # event, revprop support not implemented
  revisionHandler(options, options.rev, dict())
  # parse change list into path events
  changematch = re.compile(r"^([ADU_])([U\s])\s{2}(.+)$")
  errors = 0
  for change in changed.splitlines():
    m = changematch.match(change);
    p = "/" + m.group(3)
    try:
      pathEntryHandler(options, options.rev, p, m.group(1), m.group(2), not p.endswith('/'))
    except NameError, e:
      ''' Catch known indexing errors, log and continue with next path entry '''
      # for name errors it would probably be sufficient to write the error message, traceback is for development 
      options.logger.error("Failed to index %s. %s" % (p, traceback.format_exc())) 
      errors = errors + 1
  return errors

def repositoryDiff(options, revision, path):
  '''
  Returns diff for revision-1:revision as plaintext for the given path
  '''
  pass

def repositoryGetFile(options, revision, path):
  '''
  Returns temporary file with contents. Should be deleted after use.
  '''
  (f, fpath) = mkstemp()
  options.logger.debug("Writing %s to temp %s" % (path, fpath))    
  catp = Popen([options.svnlook, "cat", "-r %d" % options.rev, options.repo, path], stdout=f)
  catp.communicate()
  if not catp.returncode is 0:
    options.logger.debug("Cat failed for %s. It must be a folder." % (path))
    return
  os.close(f)
  return fpath

def repositoryGetProplist(options, revision, path):
  '''
  Returns proplist as dictionary with propname:value pairs
  '''
  p = Popen([options.svnlook, "proplist", "-v", "--xml", "-r %d" % revision, options.repo, path], stdout=PIPE, stderr=PIPE)
  (propxml, error) = p.communicate()
  if p.returncode:
    raise NameError('Proplist failed. %s' % error) # for example if svn version is <1.6
  try:
    return proplistToDict(propxml)
  except xml.parsers.expat.ExpatError, e:
    raise NameError('Failed to parse svnlook proplist xml, line %d offset %d in: %s' % (e.lineno, e.offset, propxml))

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
  #assert isinstance(path, unicode)
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
  schema = options.schemahead
  schemaUrl = options.solr + schema + '/'
  id = indexGetId(options, revision, path)
  doc = '<?xml version="1.0" encoding="UTF-8"?><delete><id>%s</id></delete>' % escape(id.encode('utf8'))
  options.logger.debug(doc)
  u = urlparse(schemaUrl)
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
    options.logger.info("%s deleted %s" % (schema, id))
  else:
    options.logger.error("Error dropping %s: %d %s" % (schema, response.status, responseBody))

def indexSubmitFile_curl(optons, revision, path):
  ''' Python's httplib is not capable of POSTing files
  (multipart upload) so we use command line curl instead '''
  schema = options.schemahead
  schemaUrl = options.solr + schema + '/'
  id = indexGetId(options, revision, path)
  params = {"literal.id": id.encode('utf8'), 
            "literal.svnrevision": revision,
            "commit": "false"}

  props = repositoryGetProplist(options, revision, path)
  for p in props.keys():
    params['literal.svnprop_' + indexEscapePropname(p)] = props[p].encode('utf8')

  name = indexGetName(path)
  params['literal.name'] = name.encode('utf8')

  tempfile = repositoryGetFile(options, revision, path)
  (status, body) = runCurl(getCurlCommand(options) + [
         '%supdate/extract?%s' % (schemaUrl, urlencode(params)),
         '-F', 'myfile=@%s' % tempfile])
  os.unlink(tempfile)
  if status == 200:
    options.logger.info("%s added %s" % (schema, id))
  else:
    ''' Assuming contents are unparseable. Fallback to get the error and the properties indexed '''
    options.logger.debug("Got status %d when indexing %s. Retrying with empty document." % (status, id))
    params['literal.text_error'] = body
    # of course empty file is not valid for all file types, but I guess tika does not use extension to detect type
    f = open(tempfile, 'w')
    f.write('\n')
    f.close()
    url = '%supdate/extract?%s' % (schemaUrl, urlencode(params))
    (status2, body2) = runCurl(getCurlCommand(options) + [url,
           '-F', 'myfile=@%s' % tempfile])
    options.logger.debug("Solr URL is %d bytes", len(url))
    os.unlink(tempfile)
    if status2 == 200:
      options.logger.warn("Content parse error for %s; added to %s as empty" % (id, schema))
    else:
      options.logger.error("Failed to index %s in %s; fallback failed with status %d" % (id, schema, status2))

def getCurlCommand(options):
  curl = [options.curl, '-s', '-S']
  # ignore output of response xml (we could also capture it using Popen to get QTime)
  #curl = curl + ['-o', '/dev/null']
  # fail if status is not 200
  #curl = curl + ['-f']
  # in debug log level let curl print request response headers to stderr
  if options.logger.getEffectiveLevel() is logging.DEBUG:
    curl = curl + ['-v']
  return curl

def runCurl(command):
  ''' executes curl with the arguments from getCurlCommand and returns the status code.
  It would be nice to have the response body on errors but curl -f does not work that way.
  '''
  p = Popen(command, stdout=PIPE, stderr=PIPE)
  (output, error) = p.communicate()
  # with curl -v we get this for every request, but there is no trace level
  if options.operation != 'batch':
    if error:
      options.logger.debug(error)
    if output:
      options.logger.debug(output)
  if p.returncode:
    return (0, output + error)
  return parseSolrExtractionResponse(output)

def parseSolrExtractionResponse(output):
  '''
  Read the response body of an add request and return a tuple with (status, error message).
  If status is 200 error message can be expected to be empty.
  Status 0 is for no response or very weird response.
  '''
  # TODO we need to handle for example "< HTTP/1.1 413 FULL head" (from curl -v)
  if output[0:5] == '<?xml':
    return (200, '')
  m = re.search(r'(\d+)<\/h2>.*<pre>(.*)<\/pre>', output, re.DOTALL)
  if not m:
    return (0, 'Indexing response could not be parsed:\n' + output)
  return (int(m.groups()[0]), m.groups()[1].strip())

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
  schema = options.schemahead
  schemaUrl = options.solr + schema + '/'
  url = urlparse(schemaUrl)
  r = indexPost(url, '<commit/>')
  if r.status is 200:
    options.logger.info("%s committed" % schema)
  else:
    options.logger.error("Commit to %s failed with status %d" % (schema, r.status))

def indexOptimize(options):
  '''
  Issues optimize command to Solr. May take serveral minutes.
  '''
  schema = options.schemahead
  schemaUrl = options.solr + schema + '/'
  url = urlparse(schemaUrl)
  r = indexPost(url, '<optimize/>')
  if r.status is 200:
    options.logger.info("%s optimized" % schema)
  else:
    options.logger.error("Optimize status %d" % r.status)  
  
def indexDrop(options):
  schema = options.schemahead
  url = urlparse(options.solr + schema + '/')
  prefix = indexGetId(options, None, '')
  query = 'id:%s' % prefix.replace(':', '\\:').replace('^', '\\^') + '*'
  deleteDoc = '<?xml version="1.0" encoding="UTF-8"?><delete><query>%s</query></delete>' % query
  r = indexPost(url, deleteDoc)
  if r.status is 200:
    options.logger.info("%s deleted %s" % (schema, query))
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
  e = 0 # count errors, TODO add for each operation?
  if options.operation == 'index' or options.operation == 'batch':
    e = repositoryHistoryReader(options, handleRevision, handlePathEntry)
  if options.operation == 'drop':
    indexDrop(options)    
  if options.operation == 'index' or options.operation == 'drop' or options.operation == 'commit':
    indexCommit(options)
  if options.operation == 'optimize':
    indexOptimize(options)
  if e > 0:
    options.logger.error('%d svnhead indexing operations failed' % e)
    sys.exit(1)
