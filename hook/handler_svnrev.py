#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import Document
from urlparse import urlparse

from subprocess import Popen
from subprocess import PIPE

import hashlib

from changehandlerbase import SvnChangeHandler, indexGetId, indexPost

class ReposSearchSvnrevChangeHandler(SvnChangeHandler):
  
  def __init__(self):
    self.doc = Document()
    self.docs = self.doc.createElement("add")
    self.doc.appendChild(self.docs)
    self.count = 0
  
  def getId(self, options, rev, path):
    return indexGetId(options, rev, path)
  
  def getMd5(self, options, rev, path):
    return self.getDigest(options, rev, path, hashlib.md5)

  def getSha1(self, options, rev, path):
    return self.getDigest(options, rev, path, hashlib.sha1)
    
  def getDigest(self, options, rev, path, commandName):
    # Read the content via svnlook cat
    p1 = Popen([options.svnlook, "cat", "-r %d" % options.rev, options.repo, path], stdout=PIPE)
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
  
  def onChange(self, options, rev, path):
    '''
    Creating xml directly, this design does not support properties 
    '''
    if path.endswith('/'):
      return
    id = self.getId(options, rev, path)
    d = self.doc.createElement('doc')
    d.appendChild(self.solrField(self.doc, 'id', id))
    d.appendChild(self.solrField(self.doc, 'rev', "%s" % rev))
    md5 = self.getMd5(options, rev, path)
    d.appendChild(self.solrField(self.doc, 'md5', md5))
    sha1 = self.getSha1(options, rev, path)
    d.appendChild(self.solrField(self.doc, 'sha1', sha1))
    self.docs.appendChild(d)
    self.count = self.count + 1
    options.logger.debug('svnrev SHA-1 is %s for %s' % (sha1, id))
    
  def getSolrXml(self):
    return self.doc.toxml()
  
  def onRevisionComplete(self, options, rev):
    if self.count is 0:
      return
    schema = 'svnrev'
    url = urlparse(options.solr + schema + '/')
    (status, body) = indexPost(url, self.getSolrXml())
    if status is 200:
      options.logger.info("%s indexed %d files in rev %d" % (schema, self.count, rev))
    else:
      options.logger.error("%s add failed: %d %s" % (schema, status, body))
  