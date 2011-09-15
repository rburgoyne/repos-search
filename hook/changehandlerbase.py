#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO move to an indexing helper module
import httplib

# TODO move to an indexing helper module
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
  if revision:
    id = id + '@%d' % revision
  return id

# TODO move to an indexing helper module
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
  body = r.read()
  h.close()
  return (r.status, body)

class SvnChangeHandler(object):
  '''Base class to handle svnlook changed "events".
  
  Just the parsing of svnlook changed, not the contents.
  rev, path, pathCopyFrom = None)
  These handlers must be overridden to do something.'''

  def addCustomArguments(self, optionsParser):
    '''Allows handlers to add custom command line optnons to the OptionParser
    (see optparse module). Please prefix your options with handler name.'''
    pass

  def configure(self, options):
    '''Called after hook has been initialized with command line options'''
    self.options = options
    self.logger = self.options.logger
  
  def isHandleFolderCopyAsRecursiveAdd(self, path, copyFromPath):
    '''Return true if folders added with copy-from should be handled as
    invocation of onAdd for all sub-items and the folder.
    Note: may not be called if option foldercopy is 'nobranch' or 'no'.
    Paths start with slash.'''
    return True
  
  def onRevisionBegin(self, rev, revprops):
    pass
  
  def onRevisionComplete(self, rev):
    pass
  
  def onAdd(self, rev, path, pathCopyFrom = None):  
    '''
    Repo is the local absolute path to repository, no protocol.
    
    Rev is the inspected revision.
    
    Path is the path from repository root, starting with slash,
    ending with slash for folders but not for files.
    
    PathCopyFrom might be given if isHandleFolderCopyAsRecursiveAdd is False
    '''
    pass
  
  def onChange(self, rev, path):
    '''
    Currently invoked for 'A', 'U' and 'UU' but this might change in the future
    '''
    pass
  
  def onDelete(self, rev, path):   
    pass


