#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.dom.minidom import Document
from urlparse import urlparse

from subprocess import Popen
from subprocess import PIPE

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
    p1 = Popen([options.svnlook, "cat", "-r %d" % options.rev, options.repo, path], stdout=PIPE)
    p = Popen([options.md5], stdin=p1.stdout, stdout=PIPE)
    (md5out, error) = p.communicate()
    md5 = md5out.split()[0]
    if p.returncode:
      raise NameError('md5 command failed. %s' % error.decode('utf8'))
    return md5.decode('utf8').strip()
  
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
    md5 = self.getMd5(options, rev, path)
    d = self.doc.createElement('doc')
    d.appendChild(self.solrField(self.doc, 'id', id))
    d.appendChild(self.solrField(self.doc, 'rev', "%s" % rev))
    d.appendChild(self.solrField(self.doc, 'md5', md5))
    self.docs.appendChild(d)
    self.count = self.count + 1
    options.logger.debug('svnrev md5 %s for %s' % (md5, id))
    
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
  