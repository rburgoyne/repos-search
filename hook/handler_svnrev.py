#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import Document
from urlparse import urlparse

from subprocess import Popen
from subprocess import PIPE

import hashlib

from changehandlerbase import ReposSearchChangeHandlerBase

class ReposSearchSvnrevChangeHandler(ReposSearchChangeHandlerBase):
  
  def __init__(self):
    self.coreName = 'svnrev' # activate automatic commit in base class
    self.doc = Document()
    self.docs = self.doc.createElement("add")
    self.doc.appendChild(self.docs)
    self.count = 0

  def onAdd(self, path, copyFromPath):
    if not path.isFolder():
      self.indexFile(path)

  def onChange(self, path, hasPropChanges):
    if not path.isFolder():
      self.indexFile(path)

  def getId(self, path):
    return self.getDocId(path, self.rev)

  def getMd5(self, rev, path):
    return self.getDigest(rev, path, hashlib.md5)

  def getSha1(self, rev, path):
    return self.getDigest(rev, path, hashlib.sha1)
    
  def getDigest(self, rev, path, commandName):
    # Read the content via svnlook cat
    p1 = Popen([self.options.svnlook, "cat", "-r %d" % rev, self.options.repo, path], stdout=PIPE)
    # Create the hash object
    h = commandName()
    # Read the file in 4k blocks
    while True:
      line = p1.stdout.read(4096)
      if line != "":
        h.update(line)
      else:
        break
    # Return the UTF-8 hex digest
    return h.hexdigest().decode('utf8')
  
  def solrField(self, d, name, value):
    f = d.createElement("field")
    f.setAttribute("name", name)
    v = d.createTextNode(value.encode('utf8'))
    f.appendChild(v)
    return f

  def indexFile(self, path):
    '''
    Creating xml directly, this design does not support properties 
    '''
    if path.endswith('/'):
      return
    id = self.getId(path)
    d = self.doc.createElement('doc')
    d.appendChild(self.solrField(self.doc, 'id', id))
    d.appendChild(self.solrField(self.doc, 'rev', "%s" % self.rev))
    md5 = self.getMd5(self.rev, path)
    d.appendChild(self.solrField(self.doc, 'md5', md5))
    sha1 = self.getSha1(self.rev, path)
    d.appendChild(self.solrField(self.doc, 'sha1', sha1))
    self.docs.appendChild(d)
    self.count = self.count + 1
    self.logger.debug('svnrev SHA-1 is %s for %s' % (sha1, id))
    
  def getSolrXml(self):
    return self.doc.toxml()
  
  def onRevisionComplete(self, rev):
    if self.count is 0:
      return
    schema = 'svnrev'
    (status, body) = self.reposSolr.submit(schema, self.getSolrXml())
    if status is 200:
      self.logger.info("%s indexed %d files in rev %d" % (schema, self.count, rev))
    else:
      self.logger.error("%s add failed: %d %s" % (schema, status, body))
    self.count = 0

  
