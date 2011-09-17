#!/usr/bin/env python
# -*- coding: utf-8 -*-

from repossolr import ReposSolr

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
    self.reposSolr = ReposSolr(self.options)
    self.revCount = 0

  def onRevisionBegin(self, rev):
    self.rev = rev
    self.revCount = self.revCount + 1 
  
  def onRevisionComplete(self, rev):
    self.rev = None
    # commit automatically for very big batches
    if hasattr(self, 'coreName') and self.revCount % 1000 == 0:
      self.reposSolr.commit(self.coreName)

  def onBatchComplete(self):
    '''
    Called when the current indexing batch operation has completed.
    Can be after a single revision or a range. Useful for commit/optimize etc.
    Handlers may also use the revision counter to detect need for commit.
    
    Commit, drop and optimize can be implemented independently or using ReposSolr.
    '''
    if hasattr(self, 'coreName'):
      self.reposSolr.commit(self.coreName)

  def onStartOver(self):
    '''
    Called to order drop all indexed documents for the current repo.
    Make sure it is only the current repo.
    Dropping of an entire core's data is a manual admin operation.
    '''
    if hasattr(self, 'coreName'):
      self.reposSolr.deleteByQuery(self.coreName, 'id:' + 
            self.reposSolr.value(self.reposSolr.getDocId('/', None)) + '*')

  def onOptimize(self):
    '''
    Called to recommend optimize on a core.
    '''
    if hasattr(self, 'coreName'):
      self.reposSolr.optimize(self.coreName)
  
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
    '''
    Called after the onDelete for the actual folder that svn operated on.
    Return True to receive separate onDelete for every item in folder.
    Return False to get only onDelete for the actual folder. I most schemas
    recursive delete can be accomplished using a wildcard query when path.isFolder().
    '''
    return False

  def onFolderDeleteComplete(self, path):
    pass

  # --- below are the actual item change events

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


