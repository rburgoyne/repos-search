#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib

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

class SvnChangeHandler(object):
  '''Base class to handle svnlook changed "events".
  
  Just the parsing of svnlook changed, not the contents.
  
  These handlers must be overridden to do something.'''
  def onAdd(self, options, rev, path):
    '''
    Repo is the local absolute path to repository, no protocol.
    
    Rev is the inspected revision.
    
    Path is the path from repository root, starting with slash,
    ending with slash for folders but not for files.
    '''
    pass
  def onChange(self, options, rev, path):
    '''
    Currently invoked for 'A', 'U' and 'UU' but this might change in the future
    '''
    pass
  def onDelete(self, options, rev, path):
    pass
