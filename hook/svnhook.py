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
from subprocess import CalledProcessError
import re
from tempfile import mkstemp
from urllib import urlencode
import xml.dom.minidom
import httplib

# We should maybe make a real python module, but for now we have a bunch of source files
mainscript = __file__
if not mainscript:
  mainscript = sys.argv[0]
scriptdir = os.path.dirname(mainscript)
if not scriptdir:
  scriptdir = '.'

sys.path.append(scriptdir)

from repossolr import ReposSolr

# Plugin system like http://stackoverflow.com/questions/3048337/python-subclasses-not-listing-subclasses
# Load all SvnChangeHandler subclasses in python files named handler_*
handlerspattern = r"^handler_.*\.py$"
handlerfiles = sorted([h for h in os.listdir(scriptdir) if re.match(handlerspattern, h)])
from changehandlerbase import ReposSearchChangeHandlerBase
for handlerfile in handlerfiles:
  __import__(re.sub(r".py$", r"", handlerfile))
changehandlerclasses = ReposSearchChangeHandlerBase.__subclasses__()
changeHandlers = [c() for c in changehandlerclasses]

""" hook options """
parser = OptionParser()
parser.add_option("-o", "--operation", dest="operation", default="index",
  help="Special operations: 'batch' to index but not commit, 'drop' to empty cores" +
    ", 'commit' to commit only, 'optimize' to optimize (not done after indexing)" +
    ". This option is deprecated in favor the revision option supporting range syntax.")
parser.add_option("-p", "--repository", dest="repo",
  help="A local repository path")
parser.add_option("-r", "--revision", dest="rev",
  help="Revision to index. May be a single integer " +
    ", a range N:M when N is integer and M integer or HEAD (both ends inclusive)" +
    ", or \"*\" to drop and reindex 0:HEAD. Ranges to HEAD will cause optimize after revisions.")
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

# Options that affect one or more handlers' behavior
parser.add_option("", "--foldercopy", dest="foldercopy", default="nobranch",
  help="Enable indexing of all files in folder copies. 'yes', 'no' or 'nobranch'. Default: %default." +
    " With 'no' files will only be indexed if changed. With 'nobranch' this behavior applies only to" +
    " copies of a 'trunk' or 'branches/*' folder." +
    " With 'yes' behavior is customisable per path in change handlers' onFolderCopyBegin.")

# Custom handler options
for h in changeHandlers:
  h.addCustomArguments(parser)

class ChangePath(unicode):
  '''Wrapper class for changelist path, can still be used as string.'''

  def getPath(self):
    return "%s" % self

  def getName(self):
    return self.rpartition('/')[2]

  def isFolder(self):
    return self.endswith('/')

# startup helper
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

def isBranch(path, copyFromPath):
  ''' Used to skip folder copy for foldercopy==nobranch option.
  Simple detection checking only the source name for trunk or branch.
  '''
  istrunk = re.match(r".*/trunk/$", copyFromPath) != None
  return istrunk or re.match(r".*/branches/[^/]+/$", copyFromPath) != None

### ----- hook backend to read from repository ----- ###

def svnrun(command):
  ''' runs subversion command, handles error, returns decoded output '''
  p = Popen(command, stdout=PIPE, stderr=PIPE)
  output, error = p.communicate()
  if p.returncode:
    raise CalledProcessError(p.returncode, command)#, output=error)
  # assuming utf8 system locale
  return output.decode('utf8')

def repositoryHistoryReader(options, revision, changeHandlers):
  '''
  Iterates through repository revision and calls the given handlers
  for parse events: new revision and changed path in revision.
  
  This script is called for a single revision so there will only be one
  call to revisionHandler.
  '''
  options.logger.info("Reading %s rev %d" % (options.base, revision))
  # get change list including copy-from info
  changed = svnrun([options.svnlook, "changed", "--copy-info", "-r %d" % revision, options.repo])
  for handler in changeHandlers:
    handler.onRevisionBegin(revision)
  errors = repositoryChangelistHandler(options, revision, changeHandlers, changed.splitlines())
  for handler in changeHandlers:
    handler.onRevisionComplete(revision)
  return errors

def repositoryChangelistHandler(options, revision, changeHandlers, changeList):
  '''parse change list into path events'''
  changematch = re.compile(r"^([ADU_])([U\s])([\+\s])\s{1}(.+)$")
  copyfrommatch = re.compile(r"^\s+\(from (.*):r(\d+)\)$")  
  errors = 0
  iscopy = False # flag that next line has copy-from info
  for change in changeList:
    try:
      if iscopy:
        cfm = copyfrommatch.match(change)
        if not cfm:
          raise NameError("Expected copy-from info but got: %s" % change)
        pfrom = ChangePath('/' + cfm.group(1)) # no leading slash in copy-from
        handlePathEntry(options, revision, changeHandlers, p, m.group(1), m.group(2), pfrom)
        if p.isFolder():
          errors = errors + repositoryChangelistHandlerFolderCopy(options, revision, changeHandlers, changeList, p, pfrom)
        iscopy = False
        continue
      m = changematch.match(change)
      p = ChangePath("/" + m.group(4))
      iscopy = m.group(3) == '+'
      if not iscopy:
        handlePathEntry(options, revision, changeHandlers, p, m.group(1), m.group(2))
    except NameError, e:
      ''' Catch known indexing errors, log and continue with next path entry '''
      # for name errors it would probably be sufficient to write the error message, traceback is for development 
      options.logger.error("Failed to index %s. %s" % (p, traceback.format_exc())) 
      errors = errors + 1
  return errors

def repositoryChangelistHandlerFolderCopy(options, revision, changeHandlers, changeList, p, pfrom):
  if options.foldercopy == 'no':
    return 0
  elif options.foldercopy == 'nobranch':
    if isBranch(p, pfrom):
      options.logger.info("Skipping contents of branch %s->%s" % (pfrom, p)) 
      return 0
  elif options.foldercopy != 'yes':
    raise NameError("Unexpected foldercopy option value: %s" % options.foldercopy)
  # use folder tree as change list
  tree = svnrun([options.svnlook, "tree", "--full-paths", "-r %d" % revision, options.repo, p])
  copypaths = ['A   ' + p[1:] + t[len(p):] for t in tree.splitlines()[1:]]
  options.logger.debug('Folder copy for %s handled as:\n%s' % (p, '\n'.join(copypaths)));
  # call only the change handlers that wish to treat this as add
  changeHandlersForCopy = [h for h in changeHandlers if h.onFolderCopyBegin(p, pfrom) is not False]
  # recursion
  errors = repositoryChangelistHandler(options, changeHandlersForCopy, copypaths)
  [h for h in changeHandlers if h.onFolderCopyComplete(p, pfrom)]
  return errors
  # Note that this may mean that files edited inside a copy in the same commit are indexed twice

def repositoryGetFile(options, revision, path):
  '''
  Returns temporary file with contents. Should be deleted after use.
  '''
  (f, fpath) = mkstemp()
  options.logger.debug("Writing %s to temp %s" % (path, fpath))    
  catp = Popen([options.svnlook, "cat", "-r %d" % revision, options.repo, path], stdout=f)
  catp.communicate()
  if not catp.returncode is 0:
    options.logger.debug("Cat failed for %s. It might be a folder." % (path))
    return
  os.close(f)
  if not os.path.exists(fpath):
    raise NameError("Svn cat to temp file failed for %s@%s" % (path, str(revision)))
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

def handlePathEntry(options, revision, handlers, path, action, propaction, copyFrom = None):
  '''
  Event handler for changed path in revision.
  Path is unicode with leading slash, trailing slash for folders.
  Action is one of the subversion characters [ADU] or whitespace.
  
  Handlers is a new concept for pluggable change handlers.
  Global methods named handle* is the deprecated concept.
  '''
  options.logger.debug("%s%s  %s" % (action, propaction, path))
  propchanges = propaction == 'U'
  if action == 'D':
    [h.onDelete(path) for h in handlers]
    if path.isFolder():
      handleFolderDelete(options, revision, path) # TODO convert svnhead to changehandler
      [h.onFolderDeleteBegin(path) for h in handlers]
      # TODO recursive delete
      [h.onFolderDeleteComplete(path) for h in handlers]
    else:
      handleFileDelete(options, revision, path) # TODO convert svnhead to changehandler
  elif action == 'A':
    if not path.isFolder():
      handleFileAdd(options, revision, path) # TODO convert svnhead to changehandler
    [h.onAdd(path, copyFrom) for h in handlers]
  elif action == 'U':
    if not path.isFolder():
      handleFileChange(options, revision, path) # TODO convert svnhead to changehandler
    [h.onChange(path, propchanges) for h in handlers]
  elif action != '_':
    options.logger.warn("Unrecognized action %s" % action) 
  if propchanges:
    if not path.isFolder():
      handleFileChange(options, revision, path) # TODO convert svnhead to changehandler
    [h.onChangeProps(path) for h in handlers]

### ----- svnhead ----

reposSolr = None # initialized in __main__, TODO convert svnhead to changehandler

def handleFileDelete(options, revision, path):
  '''
  Handles indexing of file deletion.
  '''
  id = reposSolr.getDocId(path, None)
  reposSolr.delete('svnhead', id)

def handleFolderDelete(options, revision, path):
  '''
  Deletes folder and all sub-items in svnhead, recursive delete operations are not needed.
  '''
  folderId = reposSolr.getDocId(path, None)
  query = 'id:%s' % reposSolr.value(folderId) + '*'
  options.logger.debug("%s folder delete %s" % ('svnhead', query))
  reposSolr.deleteByQuery('svnhead', query)

def handleFileAdd(options, revision, path):
  '''Contents and current property values should be indexed in svnhead
  schema at [prefix][base][path]'''
  indexSubmitFile_curl(options, revision, path)

def handleFileChange(optins, revision, path):
  indexSubmitFile_curl(options, revision, path)
  
def indexSubmitFile_curl(optons, revision, path):
  ''' Python's httplib is not capable of POSTing files
  (multipart upload) so we use command line curl instead '''
  schema = options.schemahead
  schemaUrl = options.solr + schema + '/'
  id = reposSolr.getDocId(path, None)
  params = {"literal.id": id.encode('utf8'), 
            "literal.svnrevision": revision,
            "commit": "false"}

  props = repositoryGetProplist(options, revision, path)
  for p in props.keys():
    params['literal.svnprop_' + reposSolr.escapePropname(p)] = props[p].encode('utf8')

  name = path.getName()
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

def getCurrentHead(options):
  look = svnrun([options.svnlook, 'youngest', options.repo])
  youngest = int(look)
  if not youngest:
    raise NameError('invalid repository %s, svnlook youngest retunred %d' % (options.repo, youngest))
  return youngest

def getRevisionsToIndex(options, rangeValue):
  if rangeValue == '*':
    head = getCurrentHead(options)
    return range(1, head + 1)
  (fr, sep, to) = rangeValue.partition(':')
  if fr and sep and to:
    if fr == '*':
      fr = 1
    if to == 'HEAD':
      to = getCurrentHead(options)
    return range(int(fr), int(to) + 1)
  elif fr:
    return [int(fr)]
  else:
    raise NameError("Invalid revision range %s" % rangeValue)

def runRevision(options, changeHandlers, revision):
  '''
  Index a single revision.
  Throws exception if indexing fails.
  '''


if __name__ == '__main__':
  options = getOptions()
  getLogger(options)
  optionsPreprocess(options)
  reposSolr = ReposSolr(options) # for svnhead functions
  for h in changeHandlers:
    h.configure(options)
  if len(changeHandlers) < 1:
    options.logger.warn('No change handlers registered')
  options.logger.debug('Change handlers: ' + repr(changeHandlers))
  revs = getRevisionsToIndex(options, options.rev)
  if options.operation == 'drop' or options.rev.startswith('*'):
    handleFolderDelete(options, 0, '/')
    [h.onStartOver() for h in changeHandlers]
  if options.operation != 'drop' and options.operation != 'commit' and options.operation != 'optimize':
    if len(revs) > 1:
      options.logger.info('Indexing revisions %d..%d' % (revs[0], revs[len(revs) - 1]))
    for r in revs:
      try:
        e = repositoryHistoryReader(options, r, changeHandlers)
      except Exception, e:
        print "Aborting indexing at revision %d due to error"
        print traceback.format_exc()
        sys.exit(1)
      if e > 0:
        options.logger.error('%d svnhead indexing operations failed' % e)
        raise NameError("%d indexing errors for revision %d" % (e, revision))    
  if options.operation != 'batch':
    reposSolr.commit('svnhead')
    [h.onBatchComplete() for h in changeHandlers]
  if options.operation == 'optimize' or options.rev.endswith('HEAD') and options.operation != 'batch':
    reposSolr.optimize('svnhead')
    [h.onOptimize() for h in changeHandlers]

