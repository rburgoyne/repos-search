#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urlparse import urlparse
from xml.sax.saxutils import escape
import httplib

class ReposSolr(object):
  '''
  Utility methods for common solr core operations in Repos Search handlers.
  '''
  
  def __init__(self, svnhookOptions):
    self.options = svnhookOptions

  def value(self, fieldValue):
    '''
    Escapes field value for use in solr query. Note that entire queries
    cannot be escaped with this because : will be \:
    '''
    return fieldValue.replace(':', '\\:').replace('^', '\\^').replace('/', '\\/')

  def escapePropname(self, svnProperty):
    '''
    Escapes subversion property name to valid solr field name
    
    Colon is replaced with underscore.
    Dash is also replaced with underscore because Solr does
    the same implicitly when creating dynamic field.
    
    >>> ReposSorl().escapePropname('svn:mime-type')
    'svn_mime_type'
    
    This results in a slight risk of conflict, for example if
    properties wouls be svn:mime-type and svn_mime:type.
    '''
    return re.sub(r'[.:-]', '_', svnProperty)

  def getDocId(self, path, revision = None):
    '''
    Builds standard string used as id in index.
    Concatenates prefix, base, root marker and path.
    Other id's are allowed too, this is just a helper.
    TODO move this to ChangeHandlerBase after svnhead has been converted.
    Make sure dropCurrentRepo supports custom IDs.
    Reconsider use of root marker. It is good for drop etc,
    but it makes it impossible to make ids that are valid URLs.
    On the other hand valid URLs would require encoding.
    '''
    id = '^' + path
    if self.options.base:
      id = self.options.base + id
    if self.options.prefix:
      id = self.options.prefix + id
    if revision:
      id = id + '@%d' % revision
    return id

  def submit(self, coreName, doc):
    '''
    Sends documment (add, delete etc.) to Solr.
    Returns httpstatus, response body.
    '''
    url = urlparse(self.options.solr + coreName + '/')
    return self.indexPost(url, doc)

  def delete(self, coreName, id):
    id = id.encode('utf8')
    return self.deleteRaw(coreName, '<id>%s</id>' % escape(id))

  def deleteByQuery(self, coreName, query):
    query = query.encode('utf8')
    return self.deleteRaw(coreName, '<query>%s</query>' % escape(query))

  def deleteRaw(self, coreName, deleteNodeContent):
    ''' deletes using xml encoded solr delete node content, see http://wiki.apache.org/solr/UpdateXmlMessages '''
    doc = '<?xml version="1.0" encoding="UTF-8"?><delete>%s</delete>' % deleteNodeContent
    (status, body) = self.submit(coreName, doc)
    if status is 200:
      self.options.logger.info("%s deleted %s" % (coreName, deleteNodeContent))
    else:
      self.options.logger.error("%s delete failed for %s: %d %s" % (coreName, deleteNodeContent, status, body))
    return (status, body)

  def commit(self, coreName):
    self.indexCommitSchema(coreName)

  def optimize(self, coreName):
    self.indexOptimizeSchema(coreName)

  def dropCurrentRepo(self, coreName):
    '''
    Drops all documents for a repository,
    assuming standard ids (see getDocId).
    '''
    self.indexDropSchema(self, coreName)

  # --- implementation, not part of public API ---

  def indexPost(self, url, doc):
    '''
    Post solr document to index. Python httplib implementation.
    Returns httpstatus, response body.
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
   
  def indexCommitSchema(self, schema):
    (status, body) = self.submit(schema, '<commit/>')
    if status is 200:
      self.options.logger.info("%s committed" % schema)
    else:
      self.options.logger.error("Commit %s failed: %d %s" % (schema, status, body))
    
  def indexOptimizeSchema(self, schema):  
    '''
    Issues optimize command to Solr. May take serveral minutes.
    '''
    (status, body) = self.submit(schema, '<optimize/>')
    if status is 200:
      self.options.logger.info("%s optimized" % schema)
    else:
      self.options.logger.error("Optimize %s failed: %d %s" % (schema, status, body))  
    
  def indexDropSchema(self, schema):
    prefix = self.getDocId(self.options, None, '')
    query = 'id:%s' % prefix.replace(':', '\\:').replace('^', '\\^') + '*'
    deleteDoc = '<?xml version="1.0" encoding="UTF-8"?><delete><query>%s</query></delete>' % query
    (status, body) = self.submit(schema, deleteDoc)
    if status is 200:
      self.options.logger.info("%s dropped %s" % (schema, query))
    else:
      self.options.logger.error("Drop %s failed: %d %s" % (schema, status, body))

