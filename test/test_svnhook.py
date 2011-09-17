#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.append('../hook/')
from svnhook import *
from optparse import OptionParser

class SvnhookTest(unittest.TestCase):
    
  def testGetOptions(self):
    # use the global parser
    (opt, args) = parser.parse_args(['-p', '/svn/r1/'])
    self.assertEquals(opt.repo, '/svn/r1/')
    self.assertEquals(opt.nobase, False, 'default')
  
  def testPreprocessOptions(self):
    opt = OptionParser().parse_args([])[0]
    opt.repo = '/svn/r1/'
    opt.rev = '1234'
    opt.nobase = False
    optionsPreprocess(opt)
    self.assertEqual(opt.repo, '/svn/r1', 'should strip trailing slash from repo')
    self.assertEqual(opt.rev, 1234, 'should make rev numeric')
    self.assertEqual(opt.base, 'r1', 'should get base from last folder name in repo path')
    pass

  def testPreprocessOptionsNobase(self):
    opt = OptionParser().parse_args([])[0]
    opt.repo = '/svn/r1/'
    opt.rev = '1234'
    opt.nobase = True
    optionsPreprocess(opt)
    self.assertEqual(opt.base, '', 'should get base from last folder name in repo path')
    pass
      
  def testSvnlookChangedWithCopyInfo(self):
    svnlook_changed = '''D   test/
A + test2/
    (from test/:r82)'''
    # not tested yet
    pass
  
  def testGetProplist(self):
    pass
    
  def testProplistToDict(self):
    xml = '''<?xml version="1.0"?>
          <properties>
          <target
             path="reb.py">
          <property
             name="svn:executable"></property>
          <property
             name="what:Ever">jell o</property>
          </target>
          </properties>
          '''
    p = proplistToDict(xml)
    self.assertFalse(p['svn:executable'])
    self.assertEqual(p['svn:executable'], '')
    self.assertEqual(p['what:Ever'], 'jell o')
    
  def testParseCurlResponseSuccess(self):
    response = '''<?xml version="1.0" encoding="UTF-8"?>
<response>
<lst name="responseHeader"><int name="status">0</int><int name="QTime">1</int></lst>
</response>
'''
    (s, o) = parseSolrExtractionResponse(response);
    self.assertEqual(s, 200)  
    
  def testParseCurlResponseError(self):
    response = '''<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"/>
<title>Error 500 org.apache.tika.exception.TikaException: TIKA-237: Illegal SAXException from org.apache.tika.parser.xml.DcXMLParser@455b4492

org.apache.solr.common.SolrException: org.apache.tika.exception.TikaException: TIKA-237: Illegal SAXException from org.apache.tika.parser.xml.DcXMLParser@455b4492
  at org.apache.solr.handler.extraction.ExtractingDocumentLoader.load(ExtractingDocumentLoader.java:211)
Caused by: org.xml.sax.SAXParseException: The prefix "punkt" for element "punkt:lista-elem" is not bound.
  at com.sun.org.apache.xerces.internal.util.ErrorHandlerWrapper.createSAXParseException(ErrorHandlerWrapper.java:195)
  ... 26 more
</title>
</head>
<body><h2>HTTP ERROR 500</h2>
<p>Problem accessing /solr/svnhead/update/extract. Reason:
<pre>    org.apache.tika.exception.TikaException: TIKA-237: Illegal SAXException from org.apache.tika.parser.xml.DcXMLParser@455b4492

org.apache.solr.common.SolrException: org.apache.tika.exception.TikaException: TIKA-237: Illegal SAXException from org.apache.tika.parser.xml.DcXMLParser@455b4492
  at org.apache.solr.handler.extraction.ExtractingDocumentLoader.load(ExtractingDocumentLoader.java:211)
Caused by: org.xml.sax.SAXParseException: The prefix "punkt" for element "punkt:lista-elem" is not bound.
  at com.sun.org.apache.xerces.internal.util.ErrorHandlerWrapper.createSAXParseException(ErrorHandlerWrapper.java:195)
  ... 26 more
</pre></p><hr /><i><small>Powered by Jetty://</small></i><br/>                                                                                             
<br/>                                                

</body>
</html>    
    '''
    (s, o) = parseSolrExtractionResponse(response);
    self.assertEqual(s, 500)
    self.assertEqual(o[0:50], 'org.apache.tika.exception.TikaException: TIKA-237:')
 
if __name__ == '__main__':
  unittest.main()
           
