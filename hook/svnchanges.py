#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
An idea of how to abstract out the change log reading.
It might however be better to abstract the individual item changes,
such as item added, updated, deleted, properties updated...
In combination with methods to read content and metadata
this would allow indexing of arbitrary backends using the same
handlers, for example indexing webdav contents in an svnhead type of schema.

...

Models the changeset of an svn revision.
The backend may use "svnlook changed" or "svn log", or an API.
There are additional methods that require folder actions to be interpreted
into actions an all the items in the tree below.

TODO implement. Should replace the code around handlePathEntry in svnhook. 
'''

# http://subversion.apache.org/docs/api/1.6/structsvn__log__changed__path2__t.html
class SvnLogChangedPath(object):
  pass

# http://subversion.apache.org/docs/api/1.6/structsvn__log__entry__t.html
class SvnLogEntry(object):
  
  def getChangedPaths(self):
    pass
  
class SvnLogEntryExtended(SvnLogEntry):
  
  def getAddedOrChangedFiles(self):
    '''
    Returns path entries that are files with action 'A', 'M' or 'R'.
    '''
    pass
    
  def getAddedOrChangedFilesNotCopies(self):
    '''
    
    '''
  
  def getNewOrChangedFiles(self):
    '''
    Returns all new or changed files, including copies.
    Use case: index all file checksums in repository.
    '''
    pass
    
class IndexConfig(self):
  
  def getValue(self, name, path):
    '''
    Returns the config for field name at the given path.
    
    >>> getConfig('mode', '/folder/file.txt')
    # Gets the svn property index:mode från 1) file.txt, 2) /folder, 3) repo root
    '''
    pass
  
  def isIndexFull(self, path):
    '''
    Returns True if all indexing should be enabled for the path, including fulltext
    '''
    pass
  
  def isIndexProps(self, path):
    '''
    Returns True if metadata indexing should be enabled for the path
    '''
    pass
  
