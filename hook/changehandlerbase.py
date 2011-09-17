#!/usr/bin/env python
# -*- coding: utf-8 -*-

from changehandler import ReposSearchChangeHandler
from repossolr import ReposSolr

class ReposSearchChangeHandlerBase(ReposSearchChangeHandler):
  '''
  Base class to handle svnlook changed "events".
  Provides some useful fields.
  Implements methods with reasonable chance of commonality.
  See ReposSearchChangeHandler for method documentation.
  '''

  def addCustomArguments(self, optionsParser):
    pass

  def configure(self, options):
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
    if hasattr(self, 'coreName'):
      self.reposSolr.commit(self.coreName)

  def onStartOver(self):
    if hasattr(self, 'coreName'):
      self.reposSolr.deleteByQuery(self.coreName, 'id:' + 
            self.reposSolr.value(self.reposSolr.getDocId('/', None)) + '*')

  def onOptimize(self):
    if hasattr(self, 'coreName'):
      self.reposSolr.optimize(self.coreName)
  
  def onFolderCopyBegin(self, copyFromPath, path):
    return True
  
  def onFolderCopyComplete(self, copyFromPath, path):
    pass

  def onFolderDeleteBegin(self, path):
    return False

  def onFolderDeleteComplete(self, path):
    pass

  # --- below are the actual item change events

  def onAdd(self, path, copyFromPath):
    pass
  
  def onChange(self, path, hasPropChanges):
    pass

  def onChangeProps(self, path):
    pass
 
  def onDelete(self, path):
    pass

