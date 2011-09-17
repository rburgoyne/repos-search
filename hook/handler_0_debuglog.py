#!/usr/bin/env python
# -*- coding: utf-8 -*-

from changehandlerbase import ReposSearchChangeHandlerBase

class ReposSearchDebugLogHandler(ReposSearchChangeHandlerBase):

  def __init__(self):
    self.flagArgs = False

  def log(self, message):
    self.logger.debug("Event: %s" % message)

  def warn(self, message):
    self.logger.debug("Event logger warning: %s" %message)

  def addCustomArguments(self, optionsParser):
    self.flagArgs = True

  def configure(self, options):
    ReposSearchChangeHandlerBase.configure(self, options)
    if not self.flagArgs:
      self.warn("addCustomArguments was never called")
    self.logger.debug("Event logger activated")
    if not self.options:
      self.warn("no options passed to configure")

  def onRevisionBegin(self, rev):
    ReposSearchChangeHandlerBase.onRevisionBegin(self, rev)
    self.log("onRevisionBegin %s %d" % (self.options.base, self.rev))
  
  def onRevisionComplete(self, rev):
    ReposSearchChangeHandlerBase.onRevisionComplete(self, rev)
    self.log("onRevisionComplete")
    if self.rev:
      self.warn("rev was not cleared")
  
  def onBatchComplete(self):
    self.log("batch complete after %d revisions" % self.revCount)

  def onStartOver(self):
    self.log("onStartOver")

  def onOptimize(self):
    self.log("onOptimize")

  def onFolderCopyBegin(self, copyFromPath, path):
    self.log("onFolderCopyBegin %s->%s" % (copyFromPath, path))
    return True
  
  def onFolderCopyComplete(self, copyFromPath, path):
    self.log("onFolderCopyComplete %s->%s" % (copyFromPath, path))

  def onFolderDeleteBegin(self, path):
    self.log("onFolderDeleteBegin %s" % path)

  def onFolderDeleteComplete(self, path):
    self.log("onFolderDeleteComplete %s" % path)

  def onAdd(self, path, copyFromPath):
    self.log("onAdd %s" % path)
    if copyFromPath:
     self.log("      copied from %s" % copyFromPath)
  
  def onChange(self, path, hasPropChanges):
    self.log("onChange %s" % path)

  def onChangeProps(self, path):
    self.log("onChangeProps %s" % path)
 
  def onDelete(self, path):
    self.log("onDelete %s" % path)

