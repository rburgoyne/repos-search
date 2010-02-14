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


class ReposSearchTest(unittest.TestCase):
  
  def testServerIsUp(self):
    r = curl(solr + '')
    self.assertTrue(r.find('svnhead') > -1, r)
    
  def testFilename(self):
    r = searchMeta('shouldBeUNIQUEfilename')
    self.assertEqual(r['response']['numFound'], 1,
                     'Case should not matter, extension should not be needed')
    self.assertEqual(r['response']['docs'][0]['id'], 
                     u'%s^/docs/filenames/shouldBeUniqueFilename.txt' % reponame)

  def testFilenameWithExtension(self):
    r = searchMeta('shouldbeuniquefilename.txt')
    self.assertEqual(r['response']['numFound'], 1)
    
  def testFilenameStemmingDash(self):
    r = searchMeta('subversion related')
    self.assertEqual(r['response']['numFound'], 1, 'dash should be searchable as space')
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/filenames/Subversion-related Document2, 2010-02-10.txt' % reponame)
    # other stemming results
    self.assertEqual(searchMeta('subversionrelated')['response']['numFound'], 1)
    # these tests throw a KeyError if the search fails but assert that we get the expected hit
    self.assertEqual(searchMeta('subversion document 2010')['response']['docs'][0]['id'], 
                     '%s^/docs/filenames/Subversion-related Document2, 2010-02-10.txt' % reponame)
    self.assertEqual(searchMeta('20100210')['response']['docs'][0]['id'], 
                     '%s^/docs/filenames/Subversion-related Document2, 2010-02-10.txt' % reponame)
  
  def testFilenameStemmingWhitespaceComma(self):
    self.assertEqual(search('name:short not long filename txt')['response']['numFound'], 1,
                     'commas should be ignored, common words like "not" should be kept')
    
  def testFilenameUTF8(self):
    r = searchMeta(u'Swedish åäö'.encode('utf-8'))
    self.assertEqual(r['response']['numFound'], 1, 'unicode filename should not be a problem')
    self.assertEqual(r['response']['docs'][0]['id'], 
                     u'%s^/docs/filenames/In Swedish Åäö.txt' % reponame)  

  def testContentXslAndOds(self):
    r = searchContent('"cell B2"')
    self.assertEqual(r['response']['numFound'], 2)
  
  def testContentDocAndOdt(self):
    r = searchContent('"Repos Search is ok"')
    self.assertEqual(r['response']['numFound'], 2)
    
  def testPDFPrintedOnOsX(self):
    r = searchContent('veryshortpdfcontents')
    self.assertEqual(r['response']['numFound'], 1)
  
  def testContentInvalidXml(self):
    r = searchMeta('invalid not closed')
    self.assertEqual(r['response']['numFound'], 1)
    error = r['response']['docs'][0]['text_error']
    self.assertTrue(error.find('invalid') >= 0)
    self.assertTrue(error.find('xml') >= 0)
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
    r = searchMeta('tagging-in-svnprop')
    self.assertEqual(r['response']['numFound'], 1)
    self.assertEqual(r['response']['docs'][0]['id'], 
                     '%s^/docs/svnprops/textwithsvnprops.txt' % reponame,
                     'meta search should include any *:kewords property value except svn:keywords')
    
  def testKeywordsFromPDFAndSvnProperty(self):
    r = search('allkeywords:(keywordinsaveaspdf AND keywordfromsvnprop)')
    self.assertEqual(r['response']['numFound'], 1, 'should match on both keyword from file and svn')
    doc = r['response']['docs'][0]
    self.assertEqual(doc['id'], '%s^/docs/svnprops/shortpdf.pdf' % reponame)
    self.assertEqual(doc['svnprop_svn_mime_type'], 'application/pdf', 'should index svn:mime-type')
    
  def testSearchEmbeddedPDFTitle(self):
    r = searchMeta('"PDF Title"')
    docs = r['response']['docs']
    self.assertEqual(len(docs), 1, 'should match on part of PDF embedded Title')
    self.assertEqual(docs[0]['id'], '%s^/docs/svnprops/shortpdf.pdf' % reponame)

  def testSearchEmbeddedPDFSubject(self):
    # TODO Should subject be matched in meta query?    
    r = search('subject:"PDF subject"')
    docs = r['response']['docs']
    self.assertEqual(len(docs), 1, 'should match on part of PDF embedded Subject')
    self.assertEqual(docs[0]['id'], '%s^/docs/svnprops/shortpdf.pdf' % reponame)


if __name__ == '__main__':
  createRepository()
  createInitialStructure()
  unittest.main()
  rmtree(repo)