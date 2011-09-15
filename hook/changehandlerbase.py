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

class ReposSearchChangeHandlerBase(object):
  '''
  Base class to handle svnlook changed "events".
  Subclasses choose their own means of accessing svn and solr,
  global helper functions should be considered deprecated.
  '''

  def addCustomArguments(self, optionsParser):
    '''
    Allows handlers to add custom command line optnons to the OptionParser
    (see optparse module). Please prefix your options with handler name.
    '''
    pass

  def configure(self, options):
    '''
    Called after hook has been initialized with command line options
    '''
    self.options = options
    self.logger = self.options.logger
    self.revCount = 0

  def onRevisionBegin(self, rev):
    self.rev = rev
    self.revCount = self.revCount + 1 
  
  def onRevisionComplete(self, rev):
    self.rev = None

  def onBatchComplete(self):
    '''
    Called when the current indexing batch operation has completed.
    Can be after a single revision or a range. Useful for commit/optimize etc.
    Handlers may also use the revision counter to detect need for commit.
    '''
    pass
  
  def onFolderCopyBegin(self, copyFromPath, path):
    '''
    Return False to skip handling folder added with copy-from info
    as invocation of onAdd for all sub-items and the folder.
    Note: may not be called if option foldercopy is 'nobranch' or 'no'.
    Paths start with slash.'''
    return True
  
  def onFolderCopyComplete(self, copyFromPath, path):
    pass

  def onFolderDeleteBegin(self, path):
    '''Can be used to flag to onDelete that we're emulating item delete based on tree.
    Called after the onDelete for the actual folder that svn operated on.'''
    pass

  def onFolderDeleteComplete(self, path):
    pass

  # --- low level change event, mapping directly to svn status letters

  def onAdd(self, path, copyFromPath):
    '''
    Invoked both for svn status A(dd) and R(eplace),
    because R is not represented in svnlook.
    For R onDelete is invoked followed by onAdd.
    
    Path is the path from repository root, type ChangePath, starting with slash,
    ending with slash for folders but not for files.
    
    CopyFromPath is None unless add is a copy. For contents of folder copy
    it is also None because only the folder entry is a real svn copy.

    Note that files and folders may be adde svn properties,
    but onChangeProps will never be called for Add.
    '''
    pass
  
  def onChange(self, path):
    '''
    Invoked for 'U'.
    '''
    pass

  def onChangeProps(self, path):
    '''
    Invoked for 'UU' and '_U'. For the former it is called after onChange.
    '''
    pass
 
  def onDelete(self, path):
    '''
    Invoked for 'D' and each item in deleted folder. 
    '''   
    pass

