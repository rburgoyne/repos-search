#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from subprocess import check_call
from shutil import rmtree, copyfile
import urllib2
from urllib import quote
import json

# global settings for the test
# currently assumes a manually started server
solr = 'http://localhost:8080/solr/'
repo = tempfile.mkdtemp()
reponame = os.path.basename(repo)
repourl = 'file://' + repo
hook = repo + '/hooks/post-commit'
hooklog = hook + '.log'

def run(cmd):
  #not properly quoted:#print '# ' + ' '.join(cmd)
  return check_call(cmd)

def createRepository():
  ''' create repository with indexing hook enabled '''
  run(['svnadmin', 'create', repo])
  hook = repo + '/hooks/post-commit'
  f = open(hook, 'w')
  f.write('#!/bin/sh\n')
  f.write('export LC_ALL="en_US.UTF-8"\n')
  f.write('%s $1 $2' % os.path.abspath('../hook/svnhook.py'))
  f.write(' >> %s 2>&1\n' % hooklog)
  f.close()
  os.chmod(hook, 0777)

def createInitialStructure():
  '''
    Test data can be added from tests but we do a batch first for faster test execution.
    All tests may use this data.
  '''
  print '# ------- setup start --------'
  run(['svn', 'import', 'docs', repourl + '/docs', '-m', 'Mixed documents'])
  # properties must be added in a working copy, using a small subfolder for performance
  propwc = tempfile.mkdtemp()
  run(['svn', 'co', repourl + '/docs/svnprops/', propwc])
  txt =  propwc + '/textwithsvnprops.txt'
  run(['svn', 'propset', 'svn:keywords', 'Id LastChangedRevision HeadURL', txt])
  # Currently keywords properties are only treated as keywords if their namespace match the schema copyField rule 
  run(['svn', 'propset', 'cms:keywords', 'ReposSearch repossearch keywordfromsvnprop', txt])
  run(['svn', 'propset', 'whatever:tags', 'metadataindexing tagging-in-svnprop', txt])
  run(['svn', 'propset', 'custom:someurl', 'Visit http://repossearch.com/', txt])
  run(['svn', 'propset', 'svn:mime-type', 'application/pdf', propwc + '/shortpdf.pdf'])
  run(['svn', 'propset', 'cms:keywords', 'keywordfromsvnprop', propwc + '/shortpdf.pdf'])
  # creating the invalid xml here so the error is not logged in rev 1 too
  xml = propwc + '/invalid, tag not closed.xml'
  f = open(xml, 'w')
  f.write('<?xml version="1.0"?>\n<document>\n<opentag>\n</document>\n')
  f.close()
  run(['svn', 'add', xml])
  run(['svn', 'propset', 'some:prop', 'OnInvalidXml', xml])
  run(['svn', 'commit', '-m', 'Properties added', propwc])
  print '# ---- common test data ----'
  run(['svnlook', 'tree', repo])
  print '# ------- hook log ---------'
  f = open(hooklog, 'r')
  print f.read()
  f.close()
  print '# ------- setup done --------'
  print ''

def curl(url):
  # transparently restrict hits to this instance
  if url.find('q=') > 0:
    url = url + '&fq=id_repo:' + reponame
  r = urllib2.urlopen(url)
  return r.read()

def search(query, queryType='standard'):
  '''
  queryType: standard/None, meta, content
  query: solr escaped but not urlencoded query
  '''
  # todo encode and stuff
  r = curl(solr + 'svnhead/select?qt=' + queryType + '&q=' + quote(query) + '&wt=json')
  #print '\n' + r 
  return json.loads(r)

def searchMeta(query):
  return search(query, 'meta')

def searchContent(query):
  return search(query, 'content')

def s1(queryType, query):
  ''' search, throw exception if number if hits is not 1, return the document id for the hit '''
  r = search(query, queryType)
  n = r['response']['numFound']
  if n == 0:
    raise NameError('No results for query "%s" type %s' % (query, queryType))
  if n > 1:
    raise NameError('%d results for query "%s" type %s: \n%s' % (n, query, queryType, repr(r)))
  return r['response']['docs'][0]['id'].partition('^')[2]

class ReposSearchTest(unittest.TestCase):
  
  def testServerIsUp(self):
    r = curl(solr + '')
    self.assertTrue(r.find('svnhead') > -1, r)
    
  def testFilename(self):
    self.assertEqual(s1('meta', 'shouldBeUNIQUEfilename'), 
                     '/docs/filenames/shouldBeUniqueFilename.txt')

  def testFilenameWithExtension(self):
    self.assertEqual(s1('meta', 'shouldbeuniquefilename.txt'), 
                     '/docs/filenames/shouldBeUniqueFilename.txt')
    
  def testFilenameTokenizeDash(self):
    self.assertEqual(s1('standard', 'name:(subversion AND related AND document2)'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt',
                     'dash should be searchable as space')
    # How do we handle dashes when the adjacent chars are digits?
    self.assertEqual(s1('meta', 'subversion document 2010'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')    
    self.assertEqual(s1('meta', '2010-02-10'), 
                     '/docs/filenames/Subversion-related Document2, 2010-02-10.txt') 
    # TODO Should dash-separated words be joined? Difference between digits and letters?
    #self.assertEqual(s1('meta', '20100210'), 
    #                 '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')
    #self.assertEqual(s1('meta', 'subversionrelated 2010-02-10'), 
    #                 '/docs/filenames/Subversion-related Document2, 2010-02-10.txt')          
    # TODO Should CamelCase be split into separate words? in that case we should have 2 hits above
    # Even if CamelCase is split it must still match as one word, as below
    self.assertEqual(s1('meta', 'subversionrelated ver'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt')    
  
  def testFilenameTokenizerCodes(self):
    self.assertEqual(s1('meta', '11.2'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt',
                     'string like 11.2 (version number) must be searchable')
    self.assertEqual(s1('meta', 'DNR333'), 
                     '/docs/filenames/SubversionRelated DNR333 ver 11.2.txt',
                     'letters+digits could be a product code and must be searchable')
  
  def testFilenameLatin1Accents(self):
    self.assertEqual(s1('meta', 'aeea'),
                     u'/docs/filenames/Latin1 accents áéèà.txt',
                     'accented chars should be searchable without accent')
  
  def testFilenameTokenizeWhitespaceComma(self):
    self.assertEqual(s1('standard', 'name:(short AND not AND long AND filename AND txt)'),
                     '/docs/filenames/short, not long, filename.txt',
                     'commas should be ignored, common words like "not" should be kept')
    
  def testFilenameUnicode(self):
    self.assertEqual(s1('meta', u'Swedish åäö'.encode('utf-8')),
                     u'/docs/filenames/In Swedish Åäö.txt')

  def testContentXslAndOds(self):
    r = searchContent('"cell B2"')
    self.assertEqual(r['response']['numFound'], 2)
  
  def testContentDocAndOdt(self):
    r = searchContent('"Repos Search is ok"')
    self.assertEqual(r['response']['numFound'], 2)
    
  def testPDFPrintedOnOsX(self):
    self.assertEqual(s1('content', 'veryshortpdfcontents'),
                     '/docs/svnprops/shortpdf.pdf')
  
  def testContentInvalidXml(self):
    r = searchMeta('invalid not closed')
    self.assertEqual(r['response']['numFound'], 1)
    error = r['response']['docs'][0]['text_error']
    self.assertTrue(error.find('xml') >= 0, 'Got: %s' % error)
    self.assertTrue(error.find('opentag') >= 0, 'Should specify the invalid tag. Got: %s' % error)    
    self.assertEqual(r['response']['docs'][0]['svnprop_some_prop'], 'OnInvalidXml',
                     'svn properties should be indexed even if document can not be parsed')
    
  def testSvnPropsTextfile(self):
    r = searchMeta('textwithsvnprops.txt')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['svnrevision'], 2)
    self.assertFalse(r['response']['docs'][0].has_key('svnprop_svn_keywords'),
                     'svn properties should normally not be indexed');
    self.assertEqual(r['response']['docs'][0]['svnprop_custom_someurl'], 'Visit http://repossearch.com/',
                     'by default custom properties should be indexed and stored as plain strings')
    
  def testMetaDontMatchSvnKeywords(self):
    r = searchMeta('LastChangedRevision')
    self.assertEqual(r['response']['numFound'], 0,
                     'svn keywords should not be indexed because they are not keywords')
    
  def testSearchOnCustomKeywords(self):
    r = searchMeta('keywordfromsvnprop')
    docs = r['response']['docs']
    self.assertEqual(len(docs), 2, 'should be two files with this keyword')    
    self.assertEqual(r['response']['docs'][1]['id'], # could probably be index 0, ranking not tested 
                     '%s^/docs/svnprops/textwithsvnprops.txt' % reponame,
                     'meta search should include keywords properties with likely namespaces except svn')

  def testSearchOnCustomTagsField(self):
    self.assertEqual(s1('meta', 'tagging-in-svnprop'),
                     '/docs/svnprops/textwithsvnprops.txt',
                     'meta search should include any *:kewords property value except svn:keywords')
    
  def testKeywordsFromPDFAndSvnProperty(self):
    r = search('allkeywords:(keywordinsaveaspdf AND keywordfromsvnprop)')
    self.assertEqual(r['response']['numFound'], 1, 'should match on both keyword from file and svn')
    doc = r['response']['docs'][0]
    self.assertEqual(doc['id'], '%s^/docs/svnprops/shortpdf.pdf' % reponame)
    self.assertEqual(doc['svnprop_svn_mime_type'], 'application/pdf', 'should index svn:mime-type')
    
  def testSearchEmbeddedPDFTitle(self):
    self.assertEqual(s1('meta', '"PDF Title"'),
                     '/docs/svnprops/shortpdf.pdf',
                     'should match on part of PDF embedded Title')

  def testSearchEmbeddedPDFSubject(self):
    # TODO Should subject be matched in meta query?    
    self.assertEqual(s1('standard', 'subject:"PDF subject"'),
                     '/docs/svnprops/shortpdf.pdf',
                     'should match on part of PDF embedded Subject')
    
  def testContentUTF8Txt(self):
    self.assertEqual(s1('content', u'ÅÄÖåäö'.encode('utf-8')),
                     u'/docs/filenames/In Swedish Åäö.txt')


if __name__ == '__main__':
  createRepository()
  createInitialStructure()
  unittest.main()
  rmtree(repo)