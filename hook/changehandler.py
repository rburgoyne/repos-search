#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ReposSearchChangeHandler(object):
  '''
  Interface for indexing handlers, based on "svnlook changed" change log.
  '''

  def onRevisionBegin(self, rev):
    pass
  
  def onRevisionComplete(self, rev):
    pass

  def onBatchComplete(self):
    '''
    Called when the current indexing batch operation has completed.
    Can be after a single revision or a range. Useful for commit/optimize etc.
    Handlers may also use the revision counter to detect need for commit.
    
    Commit, drop and optimize can be implemented independently or using ReposSolr.
    '''
    pass

  def onStartOver(self):
    '''
    Called to order drop all indexed documents for the current repo.
    Make sure it is only the current repo.
    Dropping of an entire core's data is a manual admin operation.
    '''
    pass

  def onOptimize(self):
    '''
    Called to recommend optimize on a core.
    '''
    pass
  
  def onFolderCopyBegin(self, copyFromPath, path):
    '''
    Return False to skip handling folder added with copy-from info
    as invocation of onAdd for all sub-items and the folder.
    Note: may not be called if option foldercopy is 'nobranch' or 'no'.
    Paths start with slash.
    '''
    pass
  
  def onFolderCopyComplete(self, copyFromPath, path):
    pass

  def onFolderDeleteBegin(self, path):
    '''
    Called after the onDelete for the actual folder that svn operated on.
    Return True to receive separate onDelete for every item in folder.
    Return False to get only onDelete for the actual folder. I most schemas
    recursive delete can be accomplished using a wildcard query when path.isFolder().
    '''
    pass

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
  
  def onChange(self, path, hasPropChanges):
    '''
    Invoked for 'U'. If hasPropChanges is True this call will be
    followed by onChangeProps for the same item.
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


